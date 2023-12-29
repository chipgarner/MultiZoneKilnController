class HeatCompute:
    def __compute_heats_for_zones(self, zones_status: list, tthz: list) -> list:
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
            # heat = self.update_heat_pid(target,
            #                               zones_status[index]['temperature'],
            #                               delta_t)
            heats.append(heat)
        return heats
