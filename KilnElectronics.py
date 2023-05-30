import random
import threading
import time
from abc import ABC, abstractmethod
import logging
from typing import Tuple

import adafruit_max31855
import adafruit_max31856
import adafruit_bitbangio as bitbangio
import board
import busio
import digitalio

from KilnSimulator import KilnSimulator

log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger(__name__)

# Each zone needs it's own KilElectronics for thermocouples and switching. Diffferent zones can
# have different hardware if needed. Power and any ohter sensors should also go here.

class KilnElectronics(ABC):
    @abstractmethod
    def set_heat(self, heat_factor: float):
        # This needs to set the switches timing to achieve the heat_factor.
        # E.g. on one second, off on second for a heat_factor of  0.5.
        pass

    def get_heat_factor(self) -> float:
        pass

    @abstractmethod
    def get_temperature(self) -> tuple:
        pass

class Sim(KilnElectronics):
    class FakeHeater:
        def __init__(self):
            self.value = None

    def __init__(self, name: str):
        self.heat_factor = 0
        self.kiln_sim = KilnSimulator()
        self.sim_speedup = self.kiln_sim.sim_speedup
        self.start = time.time()  # This is needed for thr simulator speedup
        self.latest_temp = 0
        heater = self.FakeHeater()
        self.switches = SSR(heater, "SSR " + name)

    def set_heat(self, heat_factor: float):
        self.switches.set_heat(heat_factor)
        self.heat_factor = self.switches.get_heat_factor()

    def get_heat_factor(self) -> float:
        return self.switches.get_heat_factor()

    def get_temperature(self) -> tuple: # From the thermocouple board
        self.kiln_sim.update_sim(self.heat_factor)
        error = 0
        temperature = self.kiln_sim.get_latest_temperature()
        temperature += random.gauss(mu=0, sigma=0.65)

        # Record the error and use the latest good temperature
        if random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 1:
            error = 1
            temperature = self.latest_temp

        self.latest_temp = temperature
        time_sim = (time.time() - self.start) * self.sim_speedup + self.start
        time_ms = round(time_sim * 1000)  # Thingsboard and SQLite require timestamps in milliseconds

        time.sleep(0.7 / self.sim_speedup)  # Real sensors take time to read
        return time_ms, temperature, error


class Max31856(KilnElectronics):
    def __init__(self, switches):
        log.info( "56 Running on board: " + board.board_id)
        self.switches = switches
        # SCK D11, MOSI D10, MISO D9
        self.spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)  # MOSI to SDI, Miso to SDO
        self.cs1 = digitalio.DigitalInOut(board.D7)

        self.sensor = adafruit_max31856.MAX31856(self.spi, self.cs1)
        self.sensor.averaging = 16
        self.sensor.noise_rejection = 60

        self.heat_factor = 0


    def set_heat(self, heat_factor: float):
        self.switches.set_heat(heat_factor)
        self.heat_factor = heat_factor

    def get_heat_factor(self) -> float:
        return self.switches.get_heat_factor()

    def get_temperature(self) -> tuple:
        error = False
        temp = self.sensor.temperature
        # log.debug("56 temperature: " + str(temp))

        for k, v in self.sensor.fault.items():
            if v:
                log.error('Temp1 31856 fault: ' + str(k))
                error = True

        time_ms = round(time.time() * 1000)
        return time_ms, temp, error

class Max31855(KilnElectronics):
    def __init__(self, switches):
        log.info( "55 running on board: " + board.board_id)
        self.switches = switches
        self.spi = busio.SPI(board.D21, MOSI=board.D20, MISO=board.D19)
        # self.spi = bitbangio.SPI(board.D22, MOSI=board.D17, MISO=board.D27)
        self.cs1 = digitalio.DigitalInOut(board.D16)

        self.sensor = adafruit_max31855.MAX31855(self.spi, self.cs1)

        self.last_temp = 0
        self.heat_factor = 0


    def set_heat(self, heat_factor: float):
        self.switches.set_heat(heat_factor)
        self.heat_factor = heat_factor

    def get_heat_factor(self) -> float:
        return self.switches.get_heat_factor()

    def get_temperature(self) -> tuple:
        error = False
        try:
            temp = self.sensor.temperature_NIST
            self.last_temp = temp
        except RuntimeError as ex:
            log.error('31855 read temperature crash: ' + str(ex))
            temp = self.last_temp
            error = True

        self.last_temp = temp

        time.sleep(1)

        time_ms = round(time.time() * 1000)
        return time_ms, temp, error

class SSR:
    # heater = digitalio.DigitalInOut(config.gpio_heat)
    # heater.direction = digitalio.Direction.OUTPUT
    def __init__(self, heater, pin_name: str): # Heater has the CircuitPython GPIO: heater = digitalio.DigitalInOut(GPIO)
        self.heat_factor = 0
        self.resolution = 20
        self.on_off = []
        self.set_heat_off()

        self.heater = heater
        thread_name = 'SSR pin ' + pin_name
        thread = threading.Thread(target=self.__heater_loop, name=thread_name, daemon=True)

        self.running = True
        thread.start()

    def set_heat_off(self):
        onoff = []
        for i in range(self.resolution):
            onoff.append(False)

        self.on_off = onoff.copy()

    def get_heat_factor(self) -> float:
        return self.heat_factor

    def __heater_loop(self):
        cycle_time = 0.1 # Depends on the SSR, many will work at 10 Hertz
        while self.running:
            log.debug('Thread: ' + threading.current_thread().name)
            onoff = self.on_off.copy()
            for on in onoff:
                self.heater.value = on
                time.sleep(cycle_time)

    def cycles_on_off(self, heat_factor: float) -> Tuple[int, int]:
        # 20 cycles keeps the round off errors small
        cycles_on = round(heat_factor * self.resolution)
        cycles_off = self.resolution - cycles_on

        return cycles_on, cycles_off

    def set_cycles_list(self, heat_factor: float) -> list:
        #TODO there must be a simpler way to do this. It spreads out the on off cycles nicely over 20 steps
        # It seems way to complicated, and code is repeated as it is symetric around 50%
        onoff = []
        cycles_on, cycles_off = self.cycles_on_off(heat_factor)
        for i in range(self.resolution):
            onoff.append(False)
        if cycles_on == 0: return onoff
        if cycles_off == 0:
            for i in range(self.resolution):
                onoff[i] = True
            return onoff

        onoff = []
        if cycles_on > cycles_off:
            if cycles_off > 0:
                skips, mod = divmod(cycles_on, cycles_off)
                if mod > 0:  # Need to skip some number (n1) of skips and some number (n2) of skips + 1
                    # n1 + n2 = ons: n1*skips + n2(skips + 1) = offs. Solve for n1 and n2
                    n2 = cycles_on - skips * cycles_off
                    n1 = cycles_off - n2
                else:
                    n1 = cycles_off
                    n2 = 0

                if n2 > 0:
                    ns = n1 / n2
                    num_shorts = round(ns)
                    if ns > 0 and num_shorts < 1:
                        skips += 1
                else:
                    num_shorts = 0

                if num_shorts >= 1:
                    index = 0
                    while index < self.resolution:
                        # Longs
                        onoff.append(False)
                        for i in range(skips + 1):
                            onoff.append(True)
                        # shorts, there may be more of these than longs
                        for _ in range(num_shorts):
                            onoff.append(False)
                            for i in range(skips):
                                onoff.append(True)

                        index = len(onoff) - 1
                else:
                    index = 0
                    while index < self.resolution:
                        onoff.append(False)
                        for i in range(skips):
                            onoff.append(True)

                        index = len(onoff)

                onoff = onoff[:20]
        else:
            if cycles_on > 0:
                skips, mod = divmod(cycles_off, cycles_on)
                if mod > 0:  # Need to skip some number (n1) of skips and some number (n2) of skips + 1
                    # n1 + n2 = ons: n1*skips + n2(skips + 1) = offs. Solve for n1 and n2
                    n2 = cycles_off - skips * cycles_on
                    n1 = cycles_on - n2
                else:
                    n1 = cycles_on
                    n2 = 0

                if n2 > 0:
                    ns = n1 / n2
                    num_shorts = round(ns)
                    if ns > 0 and num_shorts < 1:
                        skips += 1
                else:
                    num_shorts = 0

                if num_shorts >= 1:
                    index = 0
                    while index < self.resolution:
                        # Longs
                        onoff.append(True)
                        for i in range(skips + 1):
                            onoff.append(False)
                        # shorts, there may be more of these than longs
                        for _ in range(num_shorts):
                            onoff.append(True)
                            for i in range(skips):
                                onoff.append(False)

                        index = len(onoff) - 1
                else:
                    index = 0
                    while index < self.resolution:
                        onoff.append(True)
                        for i in range(skips):
                            onoff.append(False)

                        index = len(onoff)

                onoff = onoff[:20]

        return onoff

    def set_heat(self, heat_factor: float):
        onoff = self.set_cycles_list(heat_factor)
        self.on_off = onoff.copy()

        ons = [x for x in onoff if x]
        self.heat_factor = len(ons) / self.resolution



