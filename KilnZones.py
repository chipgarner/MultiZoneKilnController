import threading
import time
import logging
from KilnSimulator import KilnSimulator
import random

# Supports multiple sensors for multiple zone kilns.
# Sensors are on one thread. You can't call sensors from separate threads if they share the SPI/


log = logging.getLogger(__name__)


class KilnZones:
    def __init__(self, zones: list):
        self.zones = zones
        thread = threading.Thread(target=self.__sensors_loop, name='KilnZones', daemon=True)
        thread.start()
        log.info('KilnZones running using ' + str(len(zones)) + ' zones.')

    def get_times_temps_heat_for_zones(self) -> list:
        tts_for_zones = []
        for zone in self.zones:
            tts_for_zones.append(zone.get_times_temps_heat())
        return tts_for_zones

    def set_heat_for_zones(self, heat_for_zones: list):
        for i, zone in enumerate(self.zones):
            zone.set_heat(heat_for_zones[i])

    def __sensors_loop(self):
        while True:
            for zone in self.zones:
                zone.update_time_temperature()


class SimZone:
    def __init__(self):
        self.heat_factor = 0
        self.times_temps_heat = []
        self.tth_length = 20 # How many times_temps_heat are saved
        self.kiln_sim = KilnSimulator()
        self.sim_speedup = self.kiln_sim.sim_speedup
        self.start = time.time()

    def get_times_temps_heat(self) -> list:
        t_t_h = self.times_temps_heat
        self.times_temps_heat = []
        return t_t_h

    def set_heat(self, heat_factor: float):
        if heat_factor > 1.0 or heat_factor < 0:
            log.error('Heat factor must be from zero through one. heat_factor: ' + str(heat_factor))
            raise ValueError
        self.heat_factor = heat_factor

    def update_time_temperature(self):
        self.__update_sim()
        temp = self.__get_temperature()
        time_sim = (time.time() - self.start) * self.sim_speedup + self.start
        time_ms = round(time_sim * 1000)  # Thingsboard and SQLite require timestamps in milliseconds
        self.times_temps_heat.append({'time_ms': time_ms, 'temperature': temp, 'heat_factor': self.heat_factor})

        time.sleep(1 / self.sim_speedup) # Real sensors take time to read

    def __update_sim(self):
        self.kiln_sim.update_sim(self.heat_factor)

    def __get_temperature(self) -> float: # From the thermocouple board
        temperature = self.kiln_sim.get_latest_temperature()
        temperature += random.gauss(mu=0, sigma=0.65)
        return temperature
