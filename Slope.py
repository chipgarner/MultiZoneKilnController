import logging
import scipy
from typing import Tuple

log = logging.getLogger(__name__)
log.level = logging.DEBUG

class Slope:
    def __init__(self, num_zones: int):
        self.long_smoothed_t_t_h_z = None
        self.num_zones = num_zones
        self.restart()

    # TODO Average heat factor is likely to become important.
    def slope(self, index: int, best_time: float, best_temp: float, heat_factor: float) -> Tuple[float, float]:
        self.long_smoothed_t_t_h_z[index].append({'time_ms': best_time,
                                                  'temperature': best_temp,
                                                  'heat_factor': heat_factor})
        if len(self.long_smoothed_t_t_h_z[index]) > 20:
            self.long_smoothed_t_t_h_z[index].pop(0)

        if len(self.long_smoothed_t_t_h_z[index]) > 1:
            t_t_h = self.long_smoothed_t_t_h_z[index]
            slope, stderror = self.linear_regression(t_t_h)
            slope = slope * 3600 # degrees C per hour
            stderror = stderror * 3600
            # slope = (t_t_h[-1]['temperature'] - t_t_h[0]['temperature']) / \
            #         (t_t_h[-1]['time_ms'] - t_t_h[0]['time_ms']) * 3.6e6
            # if len(t_t_h) > 12: # Average over nearby values
            #     slope += (t_t_h[-3]['temperature'] - t_t_h[2]['temperature']) / \
            #             (t_t_h[-3]['time_ms'] - t_t_h[2]['time_ms']) * 3.6e6
            #     slope += (t_t_h[-5]['temperature'] - t_t_h[4]['temperature']) / \
            #             (t_t_h[-5]['time_ms'] - t_t_h[4]['time_ms']) * 3.6e6
            #     slope = slope / 3
        else:
            slope = 'NA'
            stderror = 'NA'

        return slope, stderror

    def linear_regression(self, tth: list) -> Tuple[float, float]:
        times = []
        temps = []
        t_initial = tth[0]['time_ms'] / 1000  #Normalize time since epoch, seconds
        for tt in tth:
            times.append(tt['time_ms'] / 1000 - t_initial)
            temps.append(tt['temperature'])
        result = scipy.stats.linregress(times, temps)
        # slope, intercept, rvalue, pvalue, stderr, intercept_stderr

        return result.slope, result.stderr # Values in degrees C per second,


    def restart(self):
        log.debug('Slope restart called.')
        self.long_smoothed_t_t_h_z = []
        for _ in range(self.num_zones):
            self.long_smoothed_t_t_h_z.append([])

    def get_latest_min_temp(self) -> float:
        min_temp = 0
        log.debug(str(self.long_smoothed_t_t_h_z[0]))
        if len(self.long_smoothed_t_t_h_z[0]) > 0:
            min_temp = 3000
            for tthz in self.long_smoothed_t_t_h_z:
                for tth in tthz:
                    if tth['temperature'] < min_temp:
                        min_temp = tth['temperature']

        return min_temp

