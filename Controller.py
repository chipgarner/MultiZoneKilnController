import time
import logging

import Profile
from KilnZones import KilnZones
import DataFilter
import pid
import Slope
import ControllerState
from dataclasses import dataclass, asdict

log = logging.getLogger(__name__)
# log.level = logging.DEBUG


class Controller:
    def __init__(self, broker, zones):
        broker_to_controller_callbacks = {'start_stop': self.start_stop_firing,
                                          'auto_manual': self.auto_manual,
                                          'set_heat_for_zone': self.set_heat_for_zone,
                                          'set_profile_by_name': self.set_profile_by_name,
                                          'add_observer': self.add_observer}
        broker.set_controller_functions(broker_to_controller_callbacks)

        self.controller_state = ControllerState.ControllerState(broker.update_UI_status)
        self.control_loop = ControlLoop(zones, broker, self.controller_state)

        log.info('Controller initialized.')

    def add_observer(self):
        self.control_loop.add_observer()

    def start_stop_firing(self):
        print('start/stop called')
        if self.controller_state.get_state().firing:
            self.controller_state.firing_off()
            log.info('Stop firing.')
        else:
            if self.controller_state.firing_on():
                self.control_loop.start_firing()

    def auto_manual(self):
        if not self.controller_state.get_state().manual:
            self.controller_state.manual_on()
            log.info('Manual on.')
        else:
            self.controller_state.manual_off()
            log.info('Manual off')

    def set_profile_by_name(self, name: str):
        if not self.controller_state.choosing_profile(name):
            log.error('Could not set the profile')
        else:
            self.control_loop.load_profile(name)

    def set_heat_for_zone(self, heat: int, zone_number: int):
        if self.controller_state.get_state().manual:
            self.control_loop.set_heat_for_zone_number(heat, zone_number)


@dataclass
class ZoneStatus:
    time_ms: int
    temperature: float
    curve_data: list
    heat_factor: float = 0
    slope: float = 0
    curvature: float = 0
    stderror: float = 0
    pstdev: float = 0
    target: str = 'Off'
    target_slope: float = 0

class ControlLoop:
    def __init__(self, zones, broker, controller_state):
        self.profile = Profile.Profile()

        self.profile_names = self.get_profile_names()
        self.zones = zones

        self.kiln_zones = KilnZones(zones, broker)
        self.slope = Slope.Slope(len(zones))

        self.controller_state = controller_state
        self.broker = broker

        self.data_filter = DataFilter
        self.start_time_ms = None

        self.last_times = []
        self.last_heat = []
        for _ in zones:
            self.last_times.append(0)
            self.last_heat.append(0)

        self.skipped = [0, 0, 0, 0]

        self.pid = pid.PID(20, 0.01, 200, setpoint=27, sample_time=None, output_limits=(0, 100))

        self.start_time_ms = None
        self.min_temp = 0

    def control_loop(self, loop_delay: int):
        time.sleep(1)  # Let other threads start
        self.__zero_heat_zones()
        while True:
            self.update_loop()
            time.sleep(loop_delay)

    def update_loop(self):
        tthz = self.kiln_zones.get_times_temps_heating_for_zones()
        zones_status = self.smooth_temperatures(tthz)

        if self.controller_state.get_state().firing:
            heats = self.__compute_heats_for_zones(zones_status, tthz)
            if not self.controller_state.get_state().manual:
                self.kiln_zones.set_heat_for_zones(heats)
        else:
            zones_status = self.__status_off(zones_status, tthz)

        zones_dict = []
        for zone in zones_status:
            zones_dict.append(asdict(zone))

        self.broker.update_zones(zones_dict)

    def start_firing(self):
        self.start_time_ms = time.time() * 1000  # Start or restart

        if self.min_temp > 60:  # Hot start
            self.start_time_ms = self.start_time_ms - \
                                 self.profile.hot_start(self.min_temp) * 1000

            # TODO config stuff, this ends on the lengyh of the sope data + 300 give it a litlle extra time
            #  to stabalize the slope - long enough to include the slope data
            self.profile.set_last_profile_change(time.time() - self.start_time_ms / 1000 + 300)

        self.send_profile(self.profile.name, self.profile.data, self.start_time_ms)
        log.info('Start firing.')

    def get_profile_names(self) -> list:
        return self.profile.get_profiles_names()

    def add_observer(self):
        self.broker.update_names(self.profile_names)
        self.controller_state.update_ui(self.controller_state.get_UI_status_dict())

    def load_profile(self, name: str):
        self.profile.load_profile_by_name(name + '.json')
        if self.start_time_ms is None:
            self.start_time_ms = time.time() * 1000
        self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)
        log.debug('Name: ' + name + ' Profile: ' + self.profile.name)

    def send_profile(self, name: str, data: list, start_ms: float):
        self.broker.new_profile_all(Profile.convert_old_profile_ms(name, data, start_ms))

    def send_updated_profile(self, name: str, data: list, start_ms: float):
        self.broker.update_profile_all(Profile.convert_old_profile_ms(name, data, start_ms))

    def __zero_heat_zones(self):
        heats = []
        for i in range(len(self.zones)):
            heats.append(0)
        self.kiln_zones.set_heat_for_zones(heats)

    def set_heat_for_zone_number(self, heat: int, zone_number: int):
        self.kiln_zones.zones[zone_number - 1].set_heat_factor(heat / 100)

    def __compute_heats_for_zones(self, zones_status: list, tthz: list) -> list:
        target = self.__profile_checks(zones_status)
        heats = []
        for index, zone in enumerate(zones_status):
            zone.target = target
            zone.target_slope = self.profile.get_target_slope(
                (zone.time_ms - self.start_time_ms) / 1000)

            delta_t = (zone.time_ms - self.last_times[index]) / 1000
            self.last_times[index] = zone.time_ms

            # heat = self.__update_heat(target,
            #                           zone,
            #                           index,
            #                           delta_t)
            heat = self.update_heat_pid(target,
                                          zone.temperature,
                                          delta_t)
            heats.append(heat)
        return heats

    def __status_off(self, zones_status: list, tthz: list) -> list:
        if len(tthz[0]) > 0:
            self.min_temp = tthz[0][0]['temperature']  # Needed for hot start
        else:  # Zones are not initialized yet
            self.min_temp = 20
            log.warning('Control loop started before initializing Zones.')
        self.kiln_zones.all_heat_off()
        for index, zone in enumerate(zones_status):
            zone.target = 'Off'
            zone.target_slope = 0
            self.last_times[index] = zone.time_ms

        return zones_status

    @staticmethod
    def lagging_temp_time_heat(zones_status, start_time_ms):
        min_temp = 3000
        time_since_start = 0
        heat_factor = 0
        zone_index = None
        for index, zone in enumerate(zones_status):
            if zone.temperature < min_temp:
                min_temp = zone.temperature
                time_since_start = (zone.time_ms - start_time_ms) / 1000
                heat_factor = zone.heat_factor
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
            if self.controller_state.get_state().firing:  # Only finish once.
                self.controller_state.firing_finished()
                target = "Done"
                log.info('Firing finished.')
        else:
            if error > 5:  # Too cold, move segment times so it can catch up
                if heat_factor > 0.99:
                    update = self.profile.check_shift_profile(time_since_start, self.min_temp, zones_status[zone_index])

            if update:  # The profile has shifted, show the shift in the UI
                self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)

        return target

    def smooth_temperatures(self, t_t_h_z: list) -> list:
        zones_status = []
        for zone_index, t_t_h in enumerate(t_t_h_z):
            zone_status = ZoneStatus(time_ms=0, temperature=-3.0, curve_data=[])
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

                zone_status.time_ms = best_time
                zone_status.temperature = best_temp
                zone_status.curve_data = curve_data
                zone_status.heat_factor = t_t_h[-1]['heat_factor']
                zone_status.slope = slope
                zone_status.curvature = curvature
                zone_status.stderror = curvature
                zone_status.pstdev = curvature

                zones_status.append(zone_status)

        return zones_status

    def update_heat_pid(self, target: float, temp: float, delta_tm: float) -> float:

        if type(target) is not str:
            self.pid.setpoint = target
            heat = self.pid(temp, dt=delta_tm) / 100
        else:
            heat = 0

        return heat

    def __update_heat(self, target: float, zone: dataclass(), index: int, delta_tm: float) -> float:
        heat = zone.heat_factor

        self.skipped[index] += 1
        print(self.skipped[index])
        if self.skipped[index] < 9:
            return heat
        self.skipped[index] = 0

        future = 540  # seconds
        future_temp = self.profile.get_target_temperature(future +
                                                          (zone.time_ms - self.start_time_ms) / 1000,
                                                          future=True)
        if not isinstance(future_temp, str):
            temp = zone.temperature
            future_temp_error = future_temp - temp
            future_slope = future_temp_error / future  # This is the slope we need to hit the target temperature in
            # future seconds
            slope_error = future_slope - zone.slope

            mcp = self.zones[index].mCp
            hA = self.zones[index].hA
            zone_power = self.zones[index].power
            delta_power = mcp * slope_error + hA * future_temp_error  # In watts
            heat = self.last_heat[index] + delta_power / zone_power
            if heat > 1.0:
                heat = 1.0
            if heat < 0.0:
                heat = 0.0

            log.debug('******************************************************************')
            log.debug('temp: ' + str(temp))
            log.debug('Future temp: ' + str(future_temp))
            log.debug('Future temp at this slope: ' + str(zone.slope * future + temp))
            log.debug('Last Heat: ' + str(self.last_heat[index]))
            log.debug('Updated heat: ' + str(heat))
            log.debug('delta_power: ' + str(delta_power) + ' delta_leakage: ' + str(hA * future_temp_error))

        self.last_heat[index] = heat
        return heat
