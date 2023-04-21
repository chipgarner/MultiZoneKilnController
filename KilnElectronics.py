import random
import time
from abc import ABC, abstractmethod
import logging

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
    def __init__(self):
        self.heat_factor = 0
        self.kiln_sim = KilnSimulator()
        self.sim_speedup = self.kiln_sim.sim_speedup
        self.start = time.time()  # This is needed for thr simulator speedup
        self.latest_temp = 0

    def set_heat(self, heat_factor: float):
        self.heat_factor = heat_factor

    def get_heat_factor(self) -> float:
        return self.heat_factor

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

class FakeSwitches:
    def __init__(self):
        self.heat_factor = 0
    def set_heat(self, heat_factor: float):
        self.heat_factor = heat_factor

    def get_heat_factor(self) -> float:
        return self.heat_factor

class Max31856(KilnElectronics):
    def __init__(self, switches):
        log.info( "Running on board: " + board.board_id)
        self.switches = switches
        self.spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        self.cs1 = digitalio.DigitalInOut(board.D5)

        self.sensor = adafruit_max31856.MAX31856(self.spi, self.cs1)
        self.sensor.averaging = 16
        self.sensor.noise_rejection = 60


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
        log.info( "Running on board: " + board.board_id)
        self.switches = switches
        self.spi = bitbangio.SPI(board.D22, MOSI=board.D17, MISO=board.D27)
        print(board.MOSI)
        self.cs1 = digitalio.DigitalInOut(board.D6)

        self.sensor = adafruit_max31855.MAX31855(self.spi, self.cs1)

        self.last_temp = 0


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

