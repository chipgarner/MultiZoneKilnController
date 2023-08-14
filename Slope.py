import logging
import math

from scipy import stats
from typing import Tuple

log = logging.getLogger(__name__)

class Slope:
    def __init__(self, num_zones: int):
        self.long_smoothed_t_t_h_z = None
        self.num_zones = num_zones
        self.restart()

    # TODO Average heat factor is likely to become important.
    def slope(self, zone_index: int, best_time: float, best_temp: float, heat_factor: float) -> Tuple[float, float]:
        self.long_smoothed_t_t_h_z[zone_index].append({'time_ms': best_time,
                                                  'temperature': best_temp,
                                                  'heat_factor': heat_factor})
        if len(self.long_smoothed_t_t_h_z[zone_index]) > 20:
            self.long_smoothed_t_t_h_z[zone_index].pop(0)

        if len(self.long_smoothed_t_t_h_z[zone_index]) > 1:
            t_t_h = self.long_smoothed_t_t_h_z[zone_index]
            slope, stderror = self.linear_r_degrees_per_hour(t_t_h)

        else:
            slope = 'NA'
            stderror = 'NA'

        return slope, stderror

    def linear_r_degrees_per_hour(self, tth: list) -> Tuple[float | str, float | str]:
        slope, stderror = self.linear_regression(tth)
        if math.isnan(slope):
            slope = 'NA'
            stderror = 'NA'
        else:
            slope = slope * 3600 # degrees C per hour
            stderror = stderror * 3600
        return slope, stderror

    def linear_regression(self, tth: list) -> Tuple[float, float]:
        times = []
        temps = []
        t_initial = tth[0]['time_ms'] / 1000  #Normalize time since epoch, seconds
        for tt in tth:
            times.append(tt['time_ms'] / 1000 - t_initial)
            temps.append(tt['temperature'])
        result = stats.linregress(times, temps)
        # slope, intercept, rvalue, pvalue, stderr, intercept_stderr

        return result.slope, result.stderr # Values in degrees C per second,


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

