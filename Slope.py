import logging
import math

from scipy import stats
from scipy import optimize
from typing import Tuple

log = logging.getLogger(__name__)

class Slope:
    def __init__(self, num_zones: int):
        self.long_smoothed_t_t_h_z = None
        self.num_zones = num_zones
        self.restart()

    # TODO Average heat factor is likely to become important.
    def slope(self, zone_index: int, best_time: float, best_temp: float, heat_factor: float) \
            -> Tuple[float, float, float, list]:
        self.long_smoothed_t_t_h_z[zone_index].append({'time_ms': best_time,
                                                  'temperature': best_temp,
                                                  'heat_factor': heat_factor})
        if len(self.long_smoothed_t_t_h_z[zone_index]) > 30:
            self.long_smoothed_t_t_h_z[zone_index].pop(0)

        # if len(self.long_smoothed_t_t_h_z[zone_index]) > 1:
        #     t_t_h = self.long_smoothed_t_t_h_z[zone_index]
        #     slope, stderror, final_temp = self.linear_r_degrees_per_hour(t_t_h)
        #
        # else:
        #     slope = 'NA'
        #     stderror = 'NA'
        #     final_temp = None

        if len(self.long_smoothed_t_t_h_z[zone_index]) > 4:
            slope, curvature, curve_data = self.cubic_curve_fit(self.long_smoothed_t_t_h_z[zone_index])
            stderror = 0.0

        else:
            slope = None
            stderror = None
            curve_data = None
            curvature = None
        stderror = curvature
        return slope, curvature, stderror, curve_data

    def linear_r_degrees_per_hour(self, tth: list) -> Tuple[float or str, float or str, float]:
        slope, stderror, final_temp = self.linear_regression(tth)
        if slope is not None:
            slope = slope * 3600 # degrees C per hour
            stderror = stderror * 3600
        return slope, stderror, final_temp

    def linear_regression(self, tth: list) -> Tuple[float, float, float]:
        times = []
        temps = []
        t_initial = tth[0]['time_ms'] / 1000  #Normalize time since epoch, seconds
        for tt in tth:
            times.append(tt['time_ms'] / 1000 - t_initial)
            temps.append(tt['temperature'])
        result = stats.linregress(times, temps)
        # slope, intercept, rvalue, pvalue, stderr, intercept_stderr

        if math.isnan(result.slope):
            final_temp = None
        else:
            final_temp = result.slope * times[-1] + result.intercept

        return result.slope, result.stderr, final_temp # Values in degrees C per second, degrees C

    def cubic_curve_fit(self, tth: list):
        def cubic_poly(x, a, b, c, d, e) -> Tuple[float, float, list]:
            return a*x**3 + b*x**2 + c*x + d

        times = []
        temps = []
        t_initial = tth[0]['time_ms'] / 1000  #Normalize time since epoch, seconds
        for tt in tth:
            times.append(tt['time_ms'] / 1000 - t_initial)
            temps.append(tt['temperature'])

        result = optimize.curve_fit(cubic_poly, times, temps)
        log.debug('Curve fit results: ' + str(result[0]))

        x = times[-1]
        a = result[0][0]
        b = result[0][1]
        c = result[0][2]
        d = result[0][3]

        end_slope = 3*a*x**2 + 2*b*x + c
        curvature = 6*a*x + 2*b

        curve_data = []
        for time in times:
            curve_temp = a*time**3 + b*time**2 + c*time + d
            curve_times_ms = (t_initial + time) * 1000
            curve_data.append({'time_ms': curve_times_ms, 'temperature': curve_temp})

        return end_slope, curvature, curve_data

    def restart(self):
        log.debug('Slope restart called.')
        self.long_smoothed_t_t_h_z = []
        for _ in range(self.num_zones):
            self.long_smoothed_t_t_h_z.append([])

    def get_latest_min_temp(self) -> float: # TODO only used in tests
        min_temp = 0
        log.debug(str(self.long_smoothed_t_t_h_z[0]))
        if len(self.long_smoothed_t_t_h_z[0]) > 0:
            min_temp = 3000
            for tthz in self.long_smoothed_t_t_h_z:
                for tth in tthz:
                    if tth['temperature'] < min_temp:
                        min_temp = tth['temperature']

        return min_temp

