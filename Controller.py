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
    def __init__(self, broker, zones, loop_delay):
        self.broker = broker
        broker_to_controller_callbacks = {'start_stop': self.start_stop_firing, 'auto_manual': self.auto_manual,
            'set_heat_for_zone': self.set_heat_for_zone, 'get_profile_message': self.get_profile_message,
            'set_profile_by_name': self.set_profile_by_name}
        self.broker.set_controller_functions(broker_to_controller_callbacks)

        self.profile = Profile.Profile()
        self.profile_names = self.get_profile_names()
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

        self.controller_state = ControllerState()


    def start_stop_firing(self):
        if self.controller_state.get_state()['firing']:
            self.controller_state.firing_off()
            log.debug('Stop firing.')
        else:
            self.set_profile_by_name('fast.json')  # TODO NO
            if self.controller_state.get_state()['profile_chosen']:
                self.controller_state.firing_on()
                self.start_time_ms = time.time() * 1000  # Start or restart

                self.send_profile(self.profile.name, self.profile.data, self.start_time_ms)
                log.debug('Start firing.')
                self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)
        self.slope.restart()

    def send_profile(self, name: str, data: list, start_ms: float):
        self.broker.new_profile_all(Profile.convert_old_profile_ms(name, data, start_ms))

    def send_updated_profile(self, name: str, data: list, start_ms: float):
        self.broker.update_profile_all(Profile.convert_old_profile_ms(name, data, start_ms))


    def auto_manual(self):
        if not self.controller_state.get_state()['manual']:
            self.controller_state.manual_on()
        else:
            self.controller_state.manual_off()

    def get_profile_names(self) -> list:
        return self.profile.get_profiles_names()

    def get_profile_message(self) -> list | None:
        names = None
        if not self.controller_state.get_state()['firing']:
            names = self.profile_names
        return names

    def set_profile_by_name(self, name: str):
        self.profile.load_profile_by_name(name)
        if not self.controller_state.choosing_profile():
            log.error('Could not set the profile')
        if self.start_time_ms is None:
            self.start_time_ms = time.time() * 1000
        self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)

    def control_loop(self):
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
        target = 'OFF'

        if self.profile.name is not None:
            min_temp = 2000
            time_since_start = 0
            for index, zone in enumerate(zones_status):
                if zone['temperature'] < min_temp:
                    min_temp = zone['temperature']
                    time_since_start = (zones_status[index]['time_ms'] - self.start_time_ms) / 1000
            target, update, segment_change = self.profile.update_profile(time_since_start, min_temp,
                                                                         12)  # TODO loop_delay + 2, doesn't work woth sim speedup
            if segment_change: self.slope.restart()
            if type(target) is str:
                self.controller_state.firing_off()
            elif update: # The profile has shifted, show the shift in the UI
                self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)

        if self.controller_state.get_state()['firing']:
            heats = []
            for index, zone in enumerate(tthz):
                zones_status[index]["target"] = target  # This can be None if profile is None FIRING - not allowed
                zones_status[index]["target_slope"] = self.profile.get_target_slope(
                    (zones_status[index]['time_ms'] - self.start_time_ms) / 1000)

                delta_t = (zones_status[index]['time_ms'] - self.last_times[index]) / 1000
                self.last_times[index] = zones_status[index]['time_ms']

                heat = self.__update_heat(target, zones_status[index]['temperature'], delta_t)
                heats.append(heat)

            if not self.controller_state.get_state()['manual']:
                self.kiln_zones.set_heat_for_zones(heats)
        else:
            self.kiln_zones.all_heat_off()
            for index, zone in enumerate(zones_status):
                zones_status[index]["target"] = 'Off'
                zones_status[index]["target_slope"] = 0
                self.last_times[index] = zones_status[index]['time_ms']

        if self.controller_state.get_state()['manual']: display = 'MANUAL'
        elif self.controller_state.get_state()['firing']: display = 'FIRING'
        else: display = 'IDLE'
        self.broker.update_status(display, self.controller_state.get_state()['manual'], zones_status)

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

                zones_status.append(
                    {'time_ms': best_time, 'temperature': best_temp, 'heat_factor': t_t_h_z[index][0]['heat_factor'],
                     'slope': slope, 'pstdev': pstdev})

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

    def set_heat_for_zone(self, heat, zone):
        if self.controller_state.get_state()['manual']:
            self.kiln_zones.zones[zone - 1].set_heat(heat / 100)


# This clall limits the possible states to the ones we want. For example, don't start the firing without
# furst choosing a profile.
class ControllerState:
    def __init__(self):
        self.__controller_state = {
            'firing': False,
            'profile_chosen': False,
            'manual': False
        }

    def get_state(self):
        return self.__controller_state

    def firing_on(self) -> bool:
        worked = False
        if self.__controller_state['profile_chosen']:
            self.__controller_state['firing'] = True
            worked = True
        return worked

    def firing_off(self) -> bool:
        self.__controller_state['firing'] = False
        return True

    def choosing_profile(self) -> bool:
        worked = False
        if not self.__controller_state['firing']:
            self.__controller_state['profile_chosen'] = True
            worked = True
        return worked

    def manual_on(self) -> bool:
        worked = False
        if self.__controller_state['firing']:
            self.__controller_state['manual'] = True
            worked = True
        return worked

    def manual_off(self) -> bool:
        self.__controller_state['manual'] = False
        return True
