import threading
import time
import logging
from KilnSimulator import KilnSimulator

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
        self.heat = None
        self.times_temps = []
        self.kiln_sim = KilnSimulator()
        self.sim_speedup = self.kiln_sim.sim_speedup
        self.start = time.time()

    def get_times_temps_heat(self) -> tuple:
        return self.times_temps, self.heat

    def set_heat(self, heat: float):
        self.heat = heat

    def update_time_temperature(self):
        self.__update_sim()
        temp = self.__get_temperature()
        ttime = time.time() - self.start
        self.times_temps.append((ttime, temp))

        time.sleep(1 / self.sim_speedup) # Real sensors take time to read

    def __update_sim(self):
        self.kiln_sim.update_sim(self.heat)

    def __get_temperature(self) -> float:
        return self.kiln_sim.get_latest_temperature()
