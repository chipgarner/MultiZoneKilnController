import time
import logging

import Profile
from KilnZones import KilnZones
import DataFilter
import pid
import Slope

log = logging.getLogger(__name__)
log.level = logging.DEBUG


class Controller:
    def __init__(self, broker, zones, loop_delay):
        self.profile = Profile.Profile()
        # self.pid = Pid.PID()
        self.pid = pid.PID(20, 0.01, 200, setpoint=27, sample_time=None, output_limits=(0, 100))

        self.loop_delay = loop_delay

        self.zones = zones
        self.data_filter = DataFilter
        self.start_time_ms = None

        self.kiln_zones = KilnZones(zones, broker)
        self.slope = Slope.Slope(len(zones))

        self.last_times = []
        self.last_heat = []
        for _ in zones:
            self.last_times.append(0)
            self.last_heat.append(0)

        self.broker = broker
        broker_to_controller_callbacks = {'start_stop': self.start_stop_firing,
                                          'auto_manual': self.auto_manual,
                                          'set_heat_for_zone': self.set_heat_for_zone,
                                          'set_profile_by_name': self.set_profile_by_name,
                                          'add_observer': self.add_observer}
        self.broker.set_controller_functions(broker_to_controller_callbacks)

        self.profile_names = self.get_profile_names()
        self.controller_state = ControllerState(self.broker.update_UI_status)

        self.min_temp = 0

        self.skipped = [0, 0, 0, 0]

        log.info('Controller initialized.')

    def add_observer(self):
        self.controller_state.update_ui(self.controller_state.get_UI_status())

    def start_stop_firing(self):
        print('start/stop called')
        if self.controller_state.get_state()['firing']:
            self.controller_state.firing_off()
            log.info('Stop firing.')
        else:
            if self.controller_state.firing_on():
                print('Min temp: ' + str(self.min_temp))
                self.start_time_ms = time.time() * 1000  # Start or restart

                if self.min_temp > 60:  # Hot start
                    self.start_time_ms = self.start_time_ms - \
                                         self.profile.hot_start(self.min_temp) * 1000

                    # TODO config dstuff, this e[ends on the lenght of the sope data + 300 give it a litlle extra time to stabalize the slope - long enough to include the slope data
                    self.profile.set_last_profile_change(time.time() - self.start_time_ms / 1000 + 300)

                self.send_profile(self.profile.name, self.profile.data, self.start_time_ms)
                log.info('Start firing.')
                self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)
        # self.slope.restart()

    def send_profile(self, name: str, data: list, start_ms: float):
        self.broker.new_profile_all(Profile.convert_old_profile_ms(name, data, start_ms))

    def send_updated_profile(self, name: str, data: list, start_ms: float):
        self.broker.update_profile_all(Profile.convert_old_profile_ms(name, data, start_ms))

    def auto_manual(self):
        if not self.controller_state.get_state()['manual']:
            self.controller_state.manual_on()
            log.info('Manual on.')
        else:
            self.controller_state.manual_off()
            log.info('Manual off')

    def get_profile_names(self) -> list:
        return self.profile.get_profiles_names()

    def set_profile_by_name(self, name: str):
        if not self.controller_state.choosing_profile(name):
            log.error('Could not set the profile')
        else:
            self.profile.load_profile_by_name(name + '.json')
            if self.start_time_ms is None:
                self.start_time_ms = time.time() * 1000
            self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)
            log.debug('Name: ' + name + ' Profile: ' + self.profile.name)

    def control_loop(self):
        self.__zero_heat_zones()
        time.sleep(3) # Let other threads start
        while True:
            self.update_loop()
            time.sleep(self.loop_delay)

    def update_loop(self):
        tthz = self.kiln_zones.get_times_temps_heating_for_zones()
        zones_status = self.smooth_temperatures(tthz)

        if self.controller_state.get_state()['firing']:
            target = self.__profile_checks(zones_status)
            heats = []
            for index, zone in enumerate(tthz):
                zones_status[index]["target"] = target
                zones_status[index]["target_slope"] = self.profile.get_target_slope(
                    (zones_status[index]['time_ms'] - self.start_time_ms) / 1000)

                delta_t = (zones_status[index]['time_ms'] - self.last_times[index]) / 1000
                self.last_times[index] = zones_status[index]['time_ms']

                heat = self.__update_heat(target,
                                          zones_status,
                                          index,
                                          delta_t)
                heats.append(heat)

            if not self.controller_state.get_state()['manual']:
                self.kiln_zones.set_heat_for_zones(heats)
        else:
            self.min_temp = tthz[0][0]['temperature']  # Needed for hot start
            self.kiln_zones.all_heat_off()
            for index, zone in enumerate(zones_status):
                zones_status[index]["target"] = 'Off'
                zones_status[index]["target_slope"] = 0
                self.last_times[index] = zones_status[index]['time_ms']

            self.broker.update_names(self.profile_names)

        self.broker.update_zones(zones_status)

    @staticmethod
    def lagging_temp_time_heat(zones_status, start_time_ms):
        min_temp = 3000
        time_since_start = 0
        heat_factor = 0
        zone_index = None
        for index, zone in enumerate(zones_status):
            if zone['temperature'] < min_temp:
                min_temp = zone['temperature']
                time_since_start = (zones_status[index]['time_ms'] - start_time_ms) / 1000
                heat_factor = zone['heat_factor']
                zone_index = index

        return min_temp, time_since_start, heat_factor, zone_index

    def __profile_checks(self, zones_status) -> float or str:
        self.min_temp, time_since_start, heat_factor, zone_index = \
            self.lagging_temp_time_heat(zones_status, self.start_time_ms)
        target = self.profile.get_target_temperature(time_since_start)

        if self.profile.is_segment_cooling():
            error = self.min_temp - target
        else:
            error = target - self.min_temp
        log.info('Target: ' + str(target) + ' Temperature difference: ' + str(error))

        update = False
        firing_finished = False
        if error < 0.5:  # Temperature close enough or high, check segment time
            segment_change, update, firing_finished = self.profile.check_switch_segment(time_since_start)

        if firing_finished:
            if self.controller_state.get_state()['firing']:  # Only finish once.
                self.controller_state.firing_finished()
                target = "Done"
                log.info('Firing finished.')
        else:
            if error > 5:  # Too cold, move segment times so it can catch up
                if heat_factor > 0.99:
                    update = self.profile.check_shift_profile(time_since_start, self.min_temp,
                                                              zones_status, zone_index)

            if update:  # The profile has shifted, show the shift in the UI
                self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)

        return target

    def smooth_temperatures(self, t_t_h_z: list) -> list:
        zones_status = []
        for zone_index, t_t_h in enumerate(t_t_h_z):
            if len(t_t_h) > 0:  # No data happens on startup
                median_result = self.data_filter.median(t_t_h)
                if median_result is not None:
                    best_temp = median_result['median']
                    pstdev = median_result['p_stand_dev']
                else:
                    log.warning('median_result: ' + str(median_result) + ' ' + str(t_t_h))
                    best_temp = t_t_h_z[-1]['temperature']
                    pstdev = 'NA'
                best_time = round((t_t_h[0]['time_ms'] + t_t_h[-1]['time_ms']) / 2)

                slope, curvature, curve_data = self.slope.slope(zone_index, best_time, best_temp,
                                                                t_t_h[0]['heat_factor'])
                # slope, stderror, final_temp = self.slope.linear_r_degrees_per_hour(t_t_h)
                # best_time = t_t_h[-1]['time_ms']
                # if final_temp is not None:
                #     best_temp = final_temp
                if isinstance(pstdev, float): pstdev = "{:.2f}".format(pstdev)
                # if isinstance(stderror, float): stderror = "{:.2f}".format(stderror)

                zones_status.append({'time_ms': best_time,
                                     'temperature': best_temp,
                                     'curve_data': curve_data,
                                     'heat_factor': t_t_h[-1]['heat_factor'],
                                     'slope': slope,
                                     'curvature': curvature,
                                     'stderror': curvature,
                                     'pstdev': curvature})

        return zones_status

    def __zero_heat_zones(self):
        heats = []
        for i in range(len(self.zones)):
            heats.append(0)
        self.kiln_zones.set_heat_for_zones(heats)

    def __update_heat(self, target: float, zones_status: list, index: int, delta_tm: float) -> float:
        heat = zones_status[index]['heat_factor']

        self.skipped[index] += 1
        print(self.skipped[index])
        if self.skipped[index] < 9:
            return heat
        self.skipped[index] = 0

        future = 540  # seconds
        future_temp = self.profile.get_target_temperature(future +
                                                          (zones_status[index]['time_ms'] - self.start_time_ms) / 1000,
                                                          future=True)
        if not isinstance(future_temp, str):
            temp = zones_status[index]['temperature']
            future_temp_error = future_temp - temp
            future_slope = future_temp_error / future  # This is the slope we need to hit the target temperature in future seconds
            slope_error = future_slope - zones_status[index]['slope']

            mcp = self.zones[index].mCp
            hA = self.zones[index].hA
            zone_power = self.zones[index].power
            delta_power = mcp * slope_error + hA * future_temp_error  # In watts
            heat = self.last_heat[index] + delta_power / zone_power
            if heat > 1.0: heat = 1.0
            if heat < 0.0: heat = 0.0

            log.debug('******************************************************************')
            log.debug('temp: ' + str(temp))
            log.debug('Future temp: ' + str(future_temp))
            log.debug('Future temp at this slope: ' + str(zones_status[index]['slope'] * future + temp))
            log.debug('Last Heat: ' + str(self.last_heat[index]))
            log.debug('Updated heat: ' + str(heat))
            log.debug('delta_power: ' + str(delta_power) + ' delta_leakage: ' + str(hA * future_temp_error))

        self.last_heat[index] = heat
        return heat

    def set_heat_for_zone(self, heat, zone):
        if self.controller_state.get_state()['manual']:
            self.kiln_zones.zones[zone - 1].set_heat(heat / 100)


# This class limits the possible states to the ones we want. For example, don't start the firing without
# first choosing a profile. All the logic is in one place, instead of repeating logic on the front end.
# Updates the UI on any stat changes
class ControllerState:
    def __init__(self, update_ui):
        self.__controller_state = {'firing': False, 'profile_chosen': False, 'manual': False}
        self.update_ui = update_ui

        # This avoids repeating logic on the front end.
        self.__UI_status = {
            'label': 'IDLE',
            'StartStop': 'Start',
            'StartStopDisabled': True,
            'Manual': False,
            'ManualDisabled': True,
            'ProfileName': 'None',
            'ProfileSelectDisabled': False,
        }

        self.update_ui(self.get_UI_status())

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

            self.update_ui(self.get_UI_status())
        print(worked)
        return worked

    def firing_finished(self):
        self.firing_off()
        self.__UI_status['label'] = 'Done'
        self.__UI_status['StartStopDisabled'] = True
        self.__UI_status['ProfileSelectDisabled'] = True

        self.update_ui(self.get_UI_status())

    def firing_off(self) -> bool:
        self.__controller_state['firing'] = False

        self.__UI_status['label'] = 'IDLE'
        self.__UI_status['StartStop'] = 'Start'
        self.__UI_status['StartStopDisabled'] = False
        self.__UI_status['Manual'] = False
        self.__UI_status['ManualDisabled'] = True
        self.__UI_status['ProfileSelectDisabled'] = False

        self.update_ui(self.get_UI_status())

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

            self.update_ui(self.get_UI_status())
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

            self.update_ui(self.get_UI_status())
        return worked

    def manual_off(self) -> bool:
        self.__controller_state['manual'] = False

        self.__UI_status['label'] = 'FIRING'
        self.__UI_status['StartStop'] = 'Stop'
        self.__UI_status['StartStopDisabled'] = False
        self.__UI_status['Manual'] = False
        self.__UI_status['ManualDisabled'] = False
        self.__UI_status['ProfileSelectDisabled'] = True

        self.update_ui(self.get_UI_status())

        return True
