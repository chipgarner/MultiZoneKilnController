import time
import logging
from logging import Logger

from Profile import Profile
from KilnZones import KilnZones, SimZone
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

        self.kiln_zones = KilnZones(zones)

        self.long_t_t_h_z = {}
        for zone in zones:
            self.long_t_t_h_z.update({zone.name: []})

        log.info('Controller initialized.')

        self.state = "IDLE" #  IDLE or FIRING for now

    def start_firing(self):
        self.state = 'FIRING'
        log.debug('Start firing.')
    def stop_firing(self):
        self.state = 'IDLE'
        log.debug('Stop firing.')

    def control_loop(self):
        self.start_time_ms = time.time() * 1000
        self.__zero_heat_zones()
        time.sleep(2) # Let thermocouple loops  start up
        while True:
            self.loop_calls()
            time.sleep(self.loop_delay)

    def loop_calls(self):
        # This has all the time temperature data
        t_t_h_z = self.kiln_zones.get_times_temps_heat_for_zones()
        # {'Zone 1': {'time_ms': time_ms, 'temperature': temp, 'heat_factor': self.heat_factor}}
        zones_status = self.smooth_temperatures(t_t_h_z)

        targets = {}
        if self.state == 'FIRING':
            heats = []
            for zone in t_t_h_z:
                target = self.profile.get_target_temperature((zones_status[zone]['time_ms'] - self.start_time_ms) / 1000)
                temp_error = zones_status[zone]['temperature'] - target
                targets.update({zone: target})

                heat = self.__update_heat(zones_status[zone]['heat_factor'], temp_error)
                heats.append(heat)
            self.kiln_zones.set_heat_for_zones(heats)
        else:
            self.kiln_zones.all_heat_off()

        self.broker.update(self.state, zones_status, t_t_h_z, targets)

    def smooth_temperatures(self, t_t_h_z):
        filter_result = {}
        zones_status = {}
        for zone in t_t_h_z:
            self.long_t_t_h_z[zone] = self.long_t_t_h_z[zone] + t_t_h_z[zone]
            if len(self.long_t_t_h_z[zone]) > 100:
                self.long_t_t_h_z[zone].pop(0)
            log.debug('Long_data: ' + str(len(self.long_t_t_h_z[zone])))
            filter_result[zone] = self.data_filter.linear(self.long_t_t_h_z[zone])
            log.debug(filter_result[zone])
            if filter_result[zone] is not None:
                slope = filter_result[zone]['slope'] * 3.6e6
                log.info(str(slope) + ' Degrees per hour.')
            else: slope = 0

            median_result = self.data_filter.median(t_t_h_z[zone])
            if median_result is not None:
                best_temp = median_result['median']
                pstdev = median_result['p_stand_dev']
            else:
                log.warning('median_result: ' + str(median_result) + ' ' + str(t_t_h_z[zone]))
                best_temp = t_t_h_z[zone][-1]['temperature']
                pstdev = 0
            best_time = round((t_t_h_z[zone][0]['time_ms'] + t_t_h_z[zone][-1]['time_ms']) / 2)
            zones_status[zone] = {'time_ms': best_time,
                                         'temperature': best_temp,
                                         'heat_factor': t_t_h_z[zone][0]['heat_factor'],
                                         'slope': slope,
                                         'pstdev': pstdev}

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
