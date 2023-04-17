import time
import logging
from logging import Logger

from Profile import Profile
from KilnZones import KilnZones
import DataFilter

log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'

log: Logger = logging.getLogger(__name__)


class Controller:
    def __init__(self, file: str, broker, zones, loop_delay):
        self.broker = broker
        self.broker.set_controller_functions(self.start_firing, self.stop_firing)
        self.profile = Profile(file)
        self.loop_delay = loop_delay

        self.zones = zones
        self.data_filter = DataFilter
        self.start_time_ms = None

        self.kiln_zones = KilnZones(zones, broker)

        self.long_t_t_h_z = []
        for index, zone in enumerate(zones):
            self.long_t_t_h_z.append([])

        log.info('Controller initialized.')

        self.state = "IDLE"  # IDLE or FIRING for now

    def start_firing(self):
        self.state = 'FIRING'
        log.debug('Start firing.')

    def stop_firing(self):
        self.state = 'IDLE'
        log.debug('Stop firing.')

    def control_loop(self):
        self.start_time_ms = time.time() * 1000
        self.__zero_heat_zones()
        # time.sleep(10)  # Let thermocouple loops  start up
        while True:
            self.loop_calls()
            time.sleep(self.loop_delay)

    def loop_calls(self):
        # [[{'time_ms': 1681699151525, 'temperature': 26.61509180150021, 'heat_factor': 0, 'error': 0},
        # {'time_ms': 1681699153531, 'temperature': 26.61509180150021, 'heat_factor': 0, 'error': 1},
        # {'time_ms': 1681699155537, 'temperature': 26.61509180150021, 'heat_factor': 0, 'error': 1}]]
        tthz = self.kiln_zones.get_times_temps_heating_for_zones()
        # [{'time_ms': 1681699155538, 'temperature': 26.61509180150021, 'heat_factor': 0, 'slope': -38.53027597928395, 'pstdev': 0.11994385358365571},
        # {'time_ms': 1681699156539, 'temperature': 26.35214565357634, 'heat_factor': 0, 'slope': 32.486937287637026, 'pstdev': 0.703745679973122}]
        zones_status = self.smooth_temperatures(tthz)

        if self.state == 'FIRING':
            heats = []
            for index, zone in enumerate(tthz):
                target = self.profile.get_target_temperature((zones_status[index]['time_ms'] - self.start_time_ms) / 1000)
                temp_error = zones_status[index]['temperature'] - target
                zones_status[index]["target"] = target
                zones_status[index]["target_slope"] = \
                    self.profile.get_target_slope((zones_status[index]['time_ms'] - self.start_time_ms) / 1000)

                heat = self.__update_heat(zones_status[index]['heat_factor'], temp_error)
                heats.append(heat)
            self.kiln_zones.set_heat_for_zones(heats)
        else:
            self.kiln_zones.all_heat_off()
            for index, zone in enumerate(zones_status):
                zones_status[index]["target"] = 0
                zones_status[index]["target_slope"] = 0

        self.broker.update_status(self.state, zones_status)

    def smooth_temperatures(self, t_t_h_z: list) -> list:
        filter_result = []
        zones_status = []
        for index, t_t_h in enumerate(t_t_h_z):
            if len(t_t_h) > 0:  # No data happens on startup
                self.long_t_t_h_z[index].append(t_t_h[0])
                if len(self.long_t_t_h_z[index]) > 10:
                    self.long_t_t_h_z[index].pop(0)
                log.debug('Long_data: ' + str(len(self.long_t_t_h_z[index])))
                filter_result.append(self.data_filter.linear(self.long_t_t_h_z[index]))
                log.debug(filter_result[index])
                if filter_result[index] is not None:
                    slope = filter_result[index]['slope'] * 3.6e6
                    log.info(str(slope) + ' Degrees per hour.')
                else:
                    slope = 0

                median_result = self.data_filter.median(t_t_h_z[index])
                if median_result is not None:
                    best_temp = median_result['median']
                    pstdev = median_result['p_stand_dev']
                else:
                    log.warning('median_result: ' + str(median_result) + ' ' + str(t_t_h_z[index]))
                    best_temp = t_t_h_z[-1]['temperature']
                    pstdev = 0
                best_time = round((t_t_h_z[index][0]['time_ms'] + t_t_h_z[index][-1]['time_ms']) / 2)
                zones_status.append({'time_ms': best_time,
                                     'temperature': best_temp,
                                     'heat_factor': t_t_h_z[index][0]['heat_factor'],
                                     'slope': slope,
                                     'pstdev': pstdev})

        return zones_status

    def __zero_heat_zones(self):
        heats = []
        for i in range(len(self.zones)):
            heats.append(0)
        self.kiln_zones.set_heat_for_zones(heats)

    def __update_heat(self, last_heat: float, temp_error: float) -> float:

        if temp_error > 0:
            heat = 0
        else:
            heat = - temp_error * 0.5
        if heat > 1:
            heat = 1

        return heat


class notifier:
    def update(self, message):
        log.info(message)


#  This is for testing
if __name__ == '__main__':
    controller = Controller("test-fast.json", notifier())
    controller.control_loop()
