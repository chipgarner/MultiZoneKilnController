import statistics
import time
import logging

import Predictor
import Profile
from KilnZones import KilnZones
import DataFilter
import pid
import Slope
import ControllerState
from dataclasses import dataclass, asdict
import config

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
        if self.controller_state.get_state().firing:
            self.controller_state.firing_off()
            log.info('Stop firing.')
        else:
            if self.controller_state.firing_on():
                self.control_loop.start_firing()
                log.info('Start firing.')

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
    name: str = None
    time_ms: int = None
    temperature: float = None
    curve_data: list = None
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
        self.temp_error_moving = []
        self.skipped = []
        for _ in zones:
            self.last_times.append(0)
            self.last_heat.append(0)#TODO ??? seems to be zero, not used?
            self.temp_error_moving.append([0])

            self.skipped.append(0)

        self.pid = pid.PID(20, 0.005, 20, setpoint=27, sample_time=None, output_limits=(0, 100))

        self.min_temp = 0

    def control_loop(self, loop_delay: int):
        time.sleep(2)  # Let other threads start
        self.__zero_heat_zones()
        while True:
            self.update_loop()
            time.sleep(loop_delay)

    def update_loop(self):
        tthz = self.kiln_zones.get_times_temps_heating_for_zones()
        zones_status = self.smooth_temperatures(tthz)

        if self.controller_state.get_state().firing:
            target = self.__profile_checks(zones_status)
            if type(target) is not str: #  Firing has now finished if it is a string
                heats = self.__compute_heats_for_zones(zones_status, target)
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

    def __compute_heats_for_zones(self, zones_status: list, target: float) -> list:
        heats = []
        for index, zone in enumerate(zones_status):
            heat = zone.heat_factor

            zone.target = target
            zone.target_slope = self.profile.get_target_slope(
                (zone.time_ms - self.start_time_ms) / 1000) * 3600 #  Degrees per hour

            temp_error = target - zone.temperature
            self.temp_error_moving[index].append(temp_error)
            if len(self.temp_error_moving[index]) > 25:
                self.temp_error_moving[index].pop(0)

            self.skipped[index] += 1
            if self.skipped[index] > 5:
                self.skipped[index] = 0

                delta_time= (zone.time_ms - self.last_times[index]) / 1000
                self.last_times[index] = zone.time_ms

                if config.control_method =='PID':
                    heat = self.update_heat_pid(target,
                                                zone.temperature,
                                                delta_time)
                else:
                    heat = self.__update_heat(target,
                                          zone,
                                          index,
                                          delta_time)

            heats.append(heat)
        return heats

    def __status_off(self, zones_status: list, tthz: list) -> list:
        if len(tthz[0]) > 0:
            self.min_temp = tthz[0]['temperature']  # Needed for hot start
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
                # Allow time for the slope to stabilize
                if heat_factor > 0.99 and self.zones[zone_index].get_last_heat_change_time() > 600:
                    update = self.profile.check_shift_profile(time_since_start, self.min_temp, zones_status[zone_index])

            if update:  # The profile has shifted, show the shift in the UI
                self.send_updated_profile(self.profile.name, self.profile.data, self.start_time_ms)

        return target

    def smooth_temperatures(self, t_t_h_z: list) -> list:
        zones_status = []
        for zone_index, t_t_h in enumerate(t_t_h_z):
            zone_status = ZoneStatus()
            best_temp = t_t_h['temperature']
            best_time = t_t_h['time_ms']

            slope, curvature, curve_data = self.slope.slope(zone_index, best_time, best_temp, t_t_h['heat_factor'])

            prediction = []
            for i in range(0, 25):
                predict_start = best_time / 1000
                predict_time = i * 5 + predict_start
                start_temp = best_temp
                power = t_t_h['heat_factor']
                power_change = 0.0
                power_change_start = 0
                if self.zones[zone_index].get_last_heat_change_time() is not None:
                    # TODO simulator kludge
                    last_heat_time_change = ((self.zones[zone_index].get_last_heat_change_time()
                                             - self.start_time_ms / 1000)
                                             * config.sim_speed_up_factor + self.start_time_ms / 1000)
                    power_change_start = last_heat_time_change
                    power_change = self.zones[zone_index].last_heat_change

                T = Predictor.predict_temperature(predict_time,
                                                predict_start,
                                                start_temp,
                                                power,
                                                power_change,
                                                power_change_start)
                time_ms = predict_time * 1000
                prediction.append({'time_ms': time_ms, 'temperature': T})


            zone_status.name = self.zones[zone_index].name
            zone_status.time_ms = best_time
            zone_status.temperature = best_temp
            zone_status.curve_data = prediction
            zone_status.heat_factor = t_t_h['heat_factor']
            zone_status.slope = slope
            zone_status.curvature = self.profile.current_segment
            zone_status.stderror = curvature

            zone_status.pstdev = round(statistics.fmean(self.temp_error_moving[zone_index]))

            zones_status.append(zone_status)

        return zones_status

    def update_heat_pid(self, target: float, temp: float, delta_tm: float) -> float:
        self.pid.setpoint = target
        heat = self.pid(temp, dt=delta_tm) / 100
        return heat

    def __update_heat(self, target: float, zone: dataclass(), index: int, delta_tm: float) -> float:
        heat = zone.heat_factor

        future = 300  # seconds
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
