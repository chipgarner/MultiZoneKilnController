import json
import os
import logging
import time
import copy

log = logging.getLogger(__name__)

def convert_old_profile(old_profile: dict) ->  dict:
    new_segments = []
    for i, t_t in enumerate(old_profile['data']):
        new_segments.append({"time": t_t[0], "temperature": t_t[1]})
    new_profile = {"name": old_profile['name'], "segments": new_segments}

    return new_profile

def convert_old_profile_ms(name: str, segments: list, start_ms: float) ->  dict:
    new_segments = []
    for i, t_t in enumerate(segments):
        new_segments.append({"time": t_t[0], "temperature": t_t[1], "time_ms": t_t[0] * 1000 + start_ms})
    new_profile = {"name": name, "segments": new_segments}

    return new_profile

class Profile:
    def __init__(self, file: str):
        json_data = self.get_profile(file)
        prf = json.loads(json_data)
        self.name = prf["name"]
        self.data = sorted(prf["data"])
        self.original = copy.deepcopy(self.data)
        self.current_segment = None
        self.segment_start = None

    @staticmethod
    def get_profile(file: str) -> str:
        profile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Profiles', file))
        log.debug(profile_path)
        with open(profile_path) as infile:
            profile_json = json.dumps(json.load(infile))

        return profile_json

    def get_duration(self) -> int:
        return max([t for (t, x) in self.data])

    #  x = (y-y1)(x2-x1)/(y2-y1) + x1
    @staticmethod
    def find_x_given_y_on_line_from_two_points(y: float, point1: list, point2: list) -> float:
        if point1[0] > point2[0]:
            return 0  # time2 before time1 makes no sense in kiln segment
        if point1[1] >= point2[1]:
            return 0  # Zero will crash. Negative temperature slope, we don't want to seek a time.
        x = (y - point1[1]) * (point2[0] - point1[0]) / (point2[1] - point1[1]) + point1[0]
        return x

    def find_next_time_from_temperature(self, temperature):
        time = 0  # The seek function will not do anything if this returns zero, no useful intersection was found
        for index, point2 in enumerate(self.data):
            if point2[1] >= temperature:
                if index > 0:  # Zero here would be before the first segment
                    if self.data[index - 1][1] <= temperature:  # We have an intersection
                        time = self.find_x_given_y_on_line_from_two_points(temperature, self.data[index - 1], point2)
                        if time == 0:
                            if self.data[index - 1][1] == point2[1]:  # It's a flat segment that matches the temperature
                                time = self.data[index - 1][0]
                                break

        return time

    def get_surrounding_points(self, time):
        if time > self.get_duration():
            return None, None

        prev_point = None
        next_point = None

        for i in range(len(self.data)):
            if time < self.data[i][0]:
                prev_point = self.data[i - 1]
                next_point = self.data[i]
                break

        return prev_point, next_point

    def get_target_temperature(self, time: float) -> float | str:
        if time > self.get_duration():
            return 'Off'

        (prev_point, next_point) = self.get_surrounding_points(time)

        incl = float(next_point[1] - prev_point[1]) / float(next_point[0] - prev_point[0])
        temp = prev_point[1] + (time - prev_point[0]) * incl
        return temp

    def get_target_slope(self, time_seconds: float) -> float:
        if time_seconds > self.get_duration():
            return 0

        (prev_point, next_point) = self.get_surrounding_points(time_seconds)

        slope = (next_point[1] - prev_point[1]) / (next_point[0] - prev_point[0])
        slope = slope * 3600 # C/hr

        return slope

    def update_profile(self, time_since_start, lowest_temp, delta_t) -> tuple[str | float, bool]:
        update = False
        target = self.get_target_temperature(time_since_start)
        if type(target) is str: return "Off", update

        error = target - lowest_temp
        if error > 5:
            if self.current_segment is not None:
                for index, time_temp in enumerate(self.data):
                    if index > self.current_segment:
                        time_temp[0] += delta_t
                update = True
        else:
            if error < 2:
                if self.current_segment is None:
                    self.current_segment = 0
                    self.segment_start = time.time()
                    for time_temp in self.data:
                        time_temp[0] += time_since_start
                    update = True
                else:
                    if time_since_start >= self.data[self.current_segment + 1][0]:
                        self.current_segment += 1
                        self.segment_start = time.time()

        return target, update
