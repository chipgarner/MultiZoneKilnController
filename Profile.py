import json
import os
from os.path import isfile, join
import logging
import time
import copy
from typing import Union, Tuple

log = logging.getLogger(__name__)

def convert_old_profile(old_profile: dict) ->  dict:
    new_segments = []
    for i, t_t in enumerate(old_profile['data']):
        new_segments.append({"time": t_t[0], "temperature": t_t[1]})
    new_profile = {"name": old_profile['name'], "segments": new_segments}

    return new_profile

# TODO use actual (not time since start) segment in minutes (hours?0
def save_old_profile_as_new(old_profile: dict):
    new_profile = convert_old_profile(old_profile)
    last_seg_time = 0
    for segment in new_profile['segments']:
        seg_time = segment['time'] - last_seg_time
        last_seg_time = segment['time']
        segment['time'] = seg_time / 60

    new_profile['segments'] = new_profile['segments'][1:]

    file_name = new_profile['name'] + '.' + 'json'
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'NewProfiles/', file_name))
    with open(path, 'w') as f:
        f.write(json.dumps(new_profile))


def convert_old_profile_ms(name: str, segments: list, start_ms: float) ->  dict:
    new_segments = []
    for i, t_t in enumerate(segments):
        new_segments.append({"time": t_t[0], "temperature": t_t[1], "time_ms": t_t[0] * 1000 + start_ms})
    new_profile = {"name": name, "segments": new_segments}

    return new_profile

class Profile:
    def __init__(self):
        self.profiles_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Profiles'))

        self.original = None
        self.data = None
        self.name = None
        self.current_segment = None
        self.segment_start = None

    def load_profile_by_name(self, file: str):
        profile_path = os.path.join(self.profiles_directory, file)
        log.debug(profile_path)
        with open(profile_path) as infile:
            profile_json = json.dumps(json.load(infile))

        prf = json.loads(profile_json)
        self.name = prf["name"]
        self.data = sorted(prf["data"])
        self.original = copy.deepcopy(self.data)

    def get_profiles_names(self) -> list:
        profile_names = []
        files = [f for f in os.listdir(self.profiles_directory) if isfile(join(self.profiles_directory, f))]
        for file in files:
            profile_names.append({'name': file.split('.')[0]})
        return profile_names

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

    def find_next_time_from_temperature(self, temperature: float) -> Tuple[float, int]:
        time = 0  # The seek function will not do anything if this returns zero, no useful intersection was found
        segment = 0
        for index, point in enumerate(self.data):
            if point[1] >= temperature:
                if index > 0:  # Zero here would be before the first segment
                    if self.data[index - 1][1] <= temperature:  # We have an intersection
                        time = self.find_x_given_y_on_line_from_two_points(temperature, self.data[index - 1], point)
                        segment = index - 1
                        if time == 0:
                            if self.data[index - 1][1] == point[1]:  # It's a flat segment that matches the temperature
                                time = self.data[index - 1][0]
                                break

        return time, segment

    def hot_start(self, temperature: float) -> float:
        t_time, segment = self.find_next_time_from_temperature(temperature)
        self.current_segment = segment
        self.segment_start = time.time() - self.data[segment][0]
        return t_time


    def get_surrounding_points(self, time):
        if time > self.get_duration():
            return None, None

        prev_point = self.data[self.current_segment]
        next_point = self.data[self.current_segment + 1]

        return prev_point, next_point

    def get_target_temperature(self, time: float) -> Union[float, str]:
        if time > self.get_duration():
            return 'Done'
        if self.current_segment is None:
            return self.data[0][1]

        prev_point, next_point = self.get_surrounding_points(time)

        if time > next_point[0]: temp = next_point[1]
        else:
            incl = float(next_point[1] - prev_point[1]) / float(next_point[0] - prev_point[0])
            temp = prev_point[1] + (time - prev_point[0]) * incl
        return temp

    def get_target_slope(self, time_seconds: float) -> float:
        if time_seconds > self.get_duration():
            return 0
        if self.current_segment is None:
            return 0

        (prev_point, next_point) = self.get_surrounding_points(time_seconds)

        slope = (next_point[1] - prev_point[1]) / (next_point[0] - prev_point[0])
        slope = slope * 3600 # C/hr

        return slope

    def check_shift_profile(self, time_since_start, min_temp) -> bool:
        update = False
        if self.current_segment is not None:
            prev_point = self.data[self.current_segment]
            next_point = self.data[self.current_segment + 1]
            segment_age = time_since_start - prev_point[0]
            if segment_age > 600: # Let the controller get established on the segment
                if min_temp - prev_point[1] > 5: # Avoid divide by small number or negative temp slope
                    # +2 to reduce PID induced stall on very steep segments on jump at 600 seconds
                    delta_t = self.delta_t_from_slope(prev_point, next_point, time_since_start, min_temp + 2)
                    for index, time_temp in enumerate(self.data):
                        if index > self.current_segment:
                            time_temp[0] += delta_t
                    update = True
                    log.debug('delta_t: ' + str(delta_t))
                    log.debug('min_temp: ' + str(min_temp))
        return update

    def delta_t_from_slope(self, prev_point, next_point, time_since_start, min_temp):
        delta_t = (next_point[1] - prev_point[1]) * (time_since_start - prev_point[0]) \
        / (min_temp - prev_point[1]) + prev_point[0] - next_point[0]

        return delta_t

    def check_switch_segment(self, time_since_start: float) -> Tuple[bool, bool]:
        segment_change = False
        update = False

        # Don't change the segment until temperature is met or exceeded
        if self.current_segment is None:

                self.current_segment = 0
                segment_change = True
                self.segment_start = time.time()
                for time_temp in self.data:
                    time_temp[0] += time_since_start
                update = True  # Shift profile start on start of first segment
        else:
            # Require both time and temperature to swtich to the next segment
            if time_since_start >= self.data[self.current_segment + 1][0]:
                self.current_segment += 1
                segment_change = True
                self.segment_start = time.time()

        return segment_change, update
