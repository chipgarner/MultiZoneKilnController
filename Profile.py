import json


class Profile():
    def __init__(self, json_data):
        obj = json.loads(json_data)
        self.name = obj["name"]
        self.data = sorted(obj["data"])

    def get_duration(self):
        return max([t for (t, x) in self.data])

    #  x = (y-y1)(x2-x1)/(y2-y1) + x1
    @staticmethod
    def find_x_given_y_on_line_from_two_points(y, point1, point2):
        if point1[0] > point2[0]: return 0  # time2 before time1 makes no sense in kiln segment
        if point1[1] >= point2[1]: return 0 # Zero will crach. Negative temeporature slope, we don't want to seek a time.
        x = (y - point1[1]) * (point2[0] -point1[0] ) / (point2[1] - point1[1]) + point1[0]
        return x

    def find_next_time_from_temperature(self, temperature):
        time = 0 # The seek function will not do anything if this returns zero, no useful intersection was found
        for index, point2 in enumerate(self.data):
            if point2[1] >= temperature:
                if index > 0: #  Zero here would be before the first segment
                    if self.data[index - 1][1] <= temperature: # We have an intersection
                        time = self.find_x_given_y_on_line_from_two_points(temperature, self.data[index - 1], point2)
                        if time == 0:
                            if self.data[index - 1][1] == point2[1]: # It's a flat segment that matches the temperature
                                time = self.data[index - 1][0]
                                break

        return time

    def get_surrounding_points(self, time):
        if time > self.get_duration():
            return (None, None)

        prev_point = None
        next_point = None

        for i in range(len(self.data)):
            if time < self.data[i][0]:
                prev_point = self.data[i - 1]
                next_point = self.data[i]
                break

        return (prev_point, next_point)

    #  x = (y-y1)(x2-x1)/(y2-y1) + x1
    @staticmethod
    def find_x_given_y_on_line_from_two_points(y, point1, point2):
        if point1[0] > point2[0]: return 0  # time2 before time1 makes no sense in kiln segment
        if point1[1] >= point2[1]: return 0 # Zero will crach. Negative temeporature slope, we don't want to seek a time.
        x = (y - point1[1]) * (point2[0] -point1[0] ) / (point2[1] - point1[1]) + point1[0]
        return x

    def find_next_time_from_temperature(self, temperature):
        time = 0 # The seek function will not do anything if this returns zero, no useful intersection was found
        for index, point2 in enumerate(self.data):
            if point2[1] >= temperature:
                if index > 0: #  Zero here would be before the first segment
                    if self.data[index - 1][1] <= temperature: # We have an intersection
                        time = self.find_x_given_y_on_line_from_two_points(temperature, self.data[index - 1], point2)
                        if time == 0:
                            if self.data[index - 1][1] == point2[1]: # It's a flat segment that matches the temperature
                                time = self.data[index - 1][0]
                                break

        return time


### Not in use
    def get_next_point(self, now):
        next_point = None  # Handle error if nothing found
        for i in range(len(self.data)):
            if now < self.data[i][0]:
                next_point = i
                break

        return next_point

    def shift_remaining_segments(self, now, shift_seconds):
        next_point = self.get_next_point(now)
        for i in range(len(self.data)):
            if i >= next_point:
                self.data[i][0] += shift_seconds
#####

    def get_target_temperature(self, time):
        if time > self.get_duration():
            return 0

        (prev_point, next_point) = self.get_surrounding_points(time)

        incl = float(next_point[1] - prev_point[1]) / float(next_point[0] - prev_point[0])
        temp = prev_point[1] + (time - prev_point[0]) * incl
        return temp

