import logging
from typing import Tuple

log = logging.getLogger(__name__)
log.level = logging.INFO



class Slope:
    def __init__(self, num_zones: int):
        self.long_smoothed_t_t_h_z = None
        self.num_zones = num_zones
        self.restart()

    # TODO Average heat factor is likely to become important.
    def slope(self, index: int, best_time: float, best_temp: float, heat_factor: float) -> Tuple[float, int]:
        self.long_smoothed_t_t_h_z[index].append({'time_ms': best_time,
                                                  'temperature': best_temp,
                                                  'heat_factor': heat_factor})
        if len(self.long_smoothed_t_t_h_z[index]) > 100:
            self.long_smoothed_t_t_h_z[index].pop(0)
        log.debug('Long_data: ' + str(len(self.long_smoothed_t_t_h_z[index])))

        if len(self.long_smoothed_t_t_h_z[index]) > 1:
            t_t_h = self.long_smoothed_t_t_h_z[index]
            slope = (t_t_h[-1]['temperature'] - t_t_h[0]['temperature']) / \
                    (t_t_h[-1]['time_ms'] - t_t_h[0]['time_ms']) * 3.6e6
            if len(t_t_h) > 12: # Average over nearby values
                slope += (t_t_h[-3]['temperature'] - t_t_h[2]['temperature']) / \
                        (t_t_h[-3]['time_ms'] - t_t_h[2]['time_ms']) * 3.6e6
                slope += (t_t_h[-5]['temperature'] - t_t_h[4]['temperature']) / \
                        (t_t_h[-5]['time_ms'] - t_t_h[4]['time_ms']) * 3.6e6
                slope = slope / 3
        else:
            slope = 'NA'

        return slope, len(self.long_smoothed_t_t_h_z[index]) # Data length

    def restart(self):
        self.long_smoothed_t_t_h_z = []
        for _ in range(self.num_zones):
            self.long_smoothed_t_t_h_z.append([])
