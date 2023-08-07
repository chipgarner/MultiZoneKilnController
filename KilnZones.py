import threading
import logging

# Supports multiple sensors for multiple zone kilns.
# Sensors are on one thread. You can't call sensors from separate threads if they share the SPI/

log = logging.getLogger(__name__)


class KilnZones:
    def __init__(self, zones: list, broker):
        self.zones = zones
        self.broker = broker
        thread = threading.Thread(target=self.__sensors_loop, name='KilnZones', daemon=True)
        thread.start()
        log.info('KilnZones running using ' + str(len(zones)) + ' zones.')

    # Controller calls this from its loop to get all the data since the last call and uses it for averaging etc.
    def get_times_temps_heating_for_zones(self) -> list:
        tts_for_zones = []
        for zone in self.zones:
            tts_for_zones.append(zone.get_times_temps_heat())
        return tts_for_zones

    def all_heat_off(self):
        for zone in self.zones:
            zone.set_heat(0)

    def set_heat_for_zones(self, heat_for_zones: list):
        for i, zone in enumerate(self.zones):
            zone.set_heat(heat_for_zones[i])

    def __sensors_loop(self):
        while True:
            thermocouple_data = []
            for zone in self.zones:
                thermocouple_data.append(zone.update_time_temperature())

            # Data is sent to front end on every update, around once per second.
            self.broker.update_tc_data(thermocouple_data)
            # log.debug('Thread: ' + threading.current_thread().name)

class Zone:
    def __init__(self, kiln):
        self.kiln_elec = kiln
        self.times_temps_heat = []

    def get_times_temps_heat(self) -> list:
        t_t_h = self.times_temps_heat
        self.times_temps_heat = []
        return t_t_h

    def set_heat(self, heat_factor: float):
        if heat_factor > 1.0 or heat_factor < 0:
            log.error('Heat factor must be from zero through one. heat_factor: ' + str(heat_factor))
            raise ValueError
        self.kiln_elec.set_heat(heat_factor)

    def update_time_temperature(self) -> dict:
        time_ms, temp, error = self.kiln_elec.get_temperature()
        thermocouple_data = {'time_ms': time_ms, 'temperature': temp, 'heat_factor': self.kiln_elec.get_heat_factor(), 'error': error}
        self.times_temps_heat.append(thermocouple_data)

        return thermocouple_data
