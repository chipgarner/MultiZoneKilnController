import time
import logging
from logging import Logger

import Profile
from KilnZones import KilnZones
import DataFilter
import pid
import Slope


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
log: Logger = logging.getLogger(__name__)


class Controller:
    def __init__(self, file: str, broker, zones, loop_delay):
        self.broker = broker
        self.broker.set_controller_functions(self.start_stop_firing)
        self.profile = Profile.Profile(file)
        # self.pid = Pid.PID()
        self.pid = pid.PID(10, 0.01, 2, setpoint=27, sample_time=None, output_limits=(0, 100))

        self.loop_delay = loop_delay

        self.zones = zones
        self.data_filter = DataFilter
        self.start_time_ms = None

        self.kiln_zones = KilnZones(zones, broker)
        self.slope = Slope.Slope(len(zones))

        self.last_times = []
        for _ in zones:
            self.last_times.append(0)

        log.info('Controller initialized.')

        self.state = "IDLE"  # IDLE or FIRING for now

    def start_stop_firing(self):
        if self.state == 'FIRING':
            self.state = 'IDLE'
            log.debug('Stop firing.')
        else:
            self.state = 'FIRING'
            log.debug('Start firing.')
        self.slope.restart()

    def control_loop(self):
        self.start_time_ms = time.time() * 1000
        self.__zero_heat_zones()
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

        min_temp = 2000
        time_since_start = 0
        for index, zone in enumerate(zones_status):
            if zone['temperature'] < min_temp:
                min_temp = zone['temperature']
                time_since_start = (zones_status[index]['time_ms'] - self.start_time_ms) / 1000
        status = self.profile.update_profile(time_since_start, min_temp, 12)
        if status is not None:
            if status == "IDLE":
                self.state = "IDLE"
            if status == "update":
                self.broker.update_profile_all(Profile.convert_old_profile_ms(self.profile.name, self.profile.data, self.start_time_ms))

        if self.state == 'FIRING':
            heats = []
            for index, zone in enumerate(tthz):
                target = self.profile.get_target_temperature((zones_status[index]['time_ms'] - self.start_time_ms) / 1000)
                zones_status[index]["target"] = target
                zones_status[index]["target_slope"] = \
                    self.profile.get_target_slope((zones_status[index]['time_ms'] - self.start_time_ms) / 1000)

                delta_t = (zones_status[index]['time_ms'] - self.last_times[index]) / 1000
                self.last_times[index] = zones_status[index]['time_ms']

                # This can happen if shutoff time is reached between update_profile and get_target_temperature
                if type(target) is str:
                    self.state = "IDLE"
                    heat = 0
                else:
                    heat = self.__update_heat(target, zones_status[index]['temperature'], delta_t)

                heats.append(heat)
            self.kiln_zones.set_heat_for_zones(heats)
        else:
            self.kiln_zones.all_heat_off()
            for index, zone in enumerate(zones_status):
                zones_status[index]["target"] = 'Off'
                zones_status[index]["target_slope"] = 0
                self.last_times[index] = zones_status[index]['time_ms']

        self.broker.update_status(self.state, zones_status)

    def smooth_temperatures(self, t_t_h_z: list) -> list:
        zones_status = []
        for index, t_t_h in enumerate(t_t_h_z):
            if len(t_t_h) > 0:  # No data happens on startup
                median_result = self.data_filter.median(t_t_h_z[index])
                if median_result is not None:
                    best_temp = median_result['median']
                    pstdev = median_result['p_stand_dev']
                else:
                    log.warning('median_result: ' + str(median_result) + ' ' + str(t_t_h_z[index]))
                    best_temp = t_t_h_z[-1]['temperature']
                    pstdev = 0
                best_time = round((t_t_h_z[index][0]['time_ms'] + t_t_h_z[index][-1]['time_ms']) / 2)

                slope = self.slope.slope(index, best_time, best_temp, t_t_h_z[index][0]['heat_factor'])

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

    def __update_heat(self, target: float, temp: float, delta_tm: float) -> float:

        self.pid.setpoint = target
        heat = self.pid(temp, dt=delta_tm)

        return heat / 100.0


class notifier:
    def update(self, message):
        print(message)

    def set_controller_functions(self, start, stop):
        print('Set_controller_fucntions called')

    def update_status(self, status, tc_data ):
        print("Update status called")

    def update_tc_data(self, tc_data):
        print("Update tc_data called")


#  This is for testing
if __name__ == '__main__':
    # zones = [zone1, zone2, zone3, zone4]
    controller = Controller("test-fast.json", notifier(), [], 10)
    controller.control_loop()
