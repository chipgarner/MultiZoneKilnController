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
        self.profile = Profile.Profile()
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

        self.broker = broker
        broker_to_controller_callbacks = {'start_stop': self.start_stop_firing,
                                          'auto_manual': self.auto_manual,
                                          'set_heat_for_zone': self.set_heat_for_zone,
                                          'get_profile_names': self.get_profile_names,
                                          'set_profile_by_name': self.set_profile_by_name}
        self.broker.set_controller_functions(broker_to_controller_callbacks)

        self.profile_names = self.get_profile_names()
        self.controller_state = ControllerState(self.profile_names)
        self.broker.update_UI_status(self.controller_state.get_UI_status())

        log.info('Controller initialized.')

    def start_stop_firing(self):
        if self.controller_state.get_state()['firing']:
            self.controller_state.firing_off()
            log.debug('Stop firing.')
        else:
            if self.controller_state.firing_on():
                self.start_time_ms = time.time() * 1000  # Start or restart
                self.send_profile(self.profile.name, self.profile.data, self.start_time_ms)
                log.debug('Start firing.')
                self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)
        self.slope.restart()
        self.broker.update_UI_status(self.controller_state.get_UI_status())

    def send_profile(self, name: str, data: list, start_ms: float):
        self.broker.new_profile_all(Profile.convert_old_profile_ms(name, data, start_ms))

    def send_updated_profile(self, name: str, data: list, start_ms: float):
        self.broker.update_profile_all(Profile.convert_old_profile_ms(name, data, start_ms))

    def auto_manual(self):
        if not self.controller_state.get_state()['manual']:
            self.controller_state.manual_on()
        else:
            self.controller_state.manual_off()
        self.broker.update_UI_status(self.controller_state.get_UI_status())

    def get_profile_names(self) -> list:
        return self.profile.get_profiles_names()

    def set_profile_by_name(self, name: str):
        if not self.controller_state.choosing_profile(name):
            log.error('Could not set the profile')
        else:
            self.profile.load_profile_by_name(name)
            if self.start_time_ms is None:
                self.start_time_ms = time.time() * 1000
            self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)

    def control_loop(self):
        self.__zero_heat_zones()
        while True:
            self.loop_calls()
            time.sleep(self.loop_delay)

    def loop_calls(self):
        tthz = self.kiln_zones.get_times_temps_heating_for_zones()
        zones_status = self.smooth_temperatures(tthz)
        target = 'OFF'

        if self.profile.name is not None:
            min_temp, time_since_start = self.lagging_temp_time(zones_status, self.start_time_ms)
            target = self.profile.get_target_temperature(time_since_start)
            if type(target) is str:
                self.controller_state.firing_off()
            else:
                error = target - min_temp

                segment_change = False
                update = False
                if error < 2:  # Temperature close enough or high, check segment time
                    segment_change, update = self.profile.check_switch_segment(time_since_start)
                if segment_change: self.slope.restart()

                if error > 5:  # Too cold, move segment times so it can catch up
                    update = self.profile.check_shift_profile(time_since_start, min_temp)
                if update:  # The profile has shifted, show the shift in the UI
                    log.debug('target: ' + str(target) + ', error: ' + str(error))
                    self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)

        if self.controller_state.get_state()['firing']:
            heats = []
            for index, zone in enumerate(tthz):
                zones_status[index]["target"] = target
                zones_status[index]["target_slope"] = self.profile.get_target_slope(
                    (zones_status[index]['time_ms'] - self.start_time_ms) / 1000)

                delta_t = (zones_status[index]['time_ms'] - self.last_times[index]) / 1000
                self.last_times[index] = zones_status[index]['time_ms']

                heat = self.__update_heat(target, zones_status[index]['temperature'], delta_t)
                heats.append(heat)

                log.debug(str(target - zones_status[index]['temperature']))

            log.debug(heats)

            if not self.controller_state.get_state()['manual']:
                self.kiln_zones.set_heat_for_zones(heats)
        else:
            self.kiln_zones.all_heat_off()
            for index, zone in enumerate(zones_status):
                zones_status[index]["target"] = 'Off'
                zones_status[index]["target_slope"] = 0
                self.last_times[index] = zones_status[index]['time_ms']

        self.broker.update_UI_status(self.controller_state.get_UI_status())
        self.broker.update_zones(zones_status)

    def lagging_temp_time(self, zones_status, start_time_ms):
        min_temp = 2000
        time_since_start = 0
        for index, zone in enumerate(zones_status):
            if zone['temperature'] < min_temp:
                min_temp = zone['temperature']
                time_since_start = (zones_status[index]['time_ms'] - start_time_ms) / 1000

        return min_temp, time_since_start


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

                slope, slope_data_length = self.slope.slope(index, best_time, best_temp, t_t_h_z[index][0]['heat_factor'])

                zones_status.append({'time_ms': best_time,
                                     'temperature': best_temp,
                                     'heat_factor': t_t_h_z[index][0]['heat_factor'],
                                     'slope': slope,
                                     'slope_data_length': slope_data_length,
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

    def set_heat_for_zone(self, heat, zone):
        if self.controller_state.get_state()['manual']:
            self.kiln_zones.zones[zone - 1].set_heat(heat / 100)


# This class limits the possible states to the ones we want. For example, don't start the firing without
# first choosing a profile. All the logic is in one place, instead of repeating logic on the fornt end.
class ControllerState:
    def __init__(self, profile_names):
        self.__controller_state = {'firing': False, 'profile_chosen': False, 'manual': False}

        # This avoids repeating logic on the front end.
        self.__UI_status = {
            'label': 'IDLE',
            'StartStop': 'Start',
            'StartStopDisabled': True,
            'Manual': False,
            'ManualDisabled': True,
            'ProfileName': 'None',
            'ProfileNames': profile_names,
            'ProfileSelectDisabled': False,
        }

    def get_UI_status(self):
        return self.__UI_status

    def get_state(self):
        return self.__controller_state

    def firing_on(self) -> bool:
        worked = False
        if self.__controller_state['profile_chosen']:
            self.__controller_state['firing'] = True

            self.__UI_status['label'] = 'FIRING'
            self.__UI_status['StartStop'] = 'Stop'
            self.__UI_status['StartStopDisabled'] = False
            self.__UI_status['Manual'] = False
            self.__UI_status['ManualDisabled'] = False
            self.__UI_status['ProfileSelectDisabled'] = True

            worked = True
        return worked

    def firing_off(self) -> bool:
        self.__controller_state['firing'] = False

        self.__UI_status['label'] = 'IDLE'
        self.__UI_status['StartStop'] = 'Start'
        self.__UI_status['StartStopDisabled'] = False
        self.__UI_status['Manual'] = False
        self.__UI_status['ManualDisabled'] = True
        self.__UI_status['ProfileSelectDisabled'] = False

        return True

    def choosing_profile(self, name) -> bool:
        worked = False
        if not (self.__controller_state['firing'] or self.__controller_state['manual']):
            self.__controller_state['profile_chosen'] = True
            self.__UI_status['ProfileName'] = name

            self.__UI_status['label'] = 'IDLE'
            self.__UI_status['StartStop'] = 'Start'
            self.__UI_status['StartStopDisabled'] = False
            self.__UI_status['Manual'] = False
            self.__UI_status['ManualDisabled'] = True
            self.__UI_status['ProfileSelectDisabled'] = False

            worked = True
        return worked

    def manual_on(self) -> bool:
        worked = False
        if self.__controller_state['firing']:
            self.__controller_state['manual'] = True

            self.__UI_status['label'] = 'MANUAL'
            self.__UI_status['StartStop'] = 'Stop'
            self.__UI_status['StartStopDisabled'] = False
            self.__UI_status['Manual'] = True
            self.__UI_status['ManualDisabled'] = False
            self.__UI_status['ProfileSelectDisabled'] = True

            worked = True
        return worked

    def manual_off(self) -> bool:
        self.__controller_state['manual'] = False

        self.__UI_status['label'] = 'FIRING'
        self.__UI_status['StartStop'] = 'Stop'
        self.__UI_status['StartStopDisabled'] = False
        self.__UI_status['Manual'] = False
        self.__UI_status['ManualDisabled'] = False
        self.__UI_status['ProfileSelectDisabled'] = True

        return True
