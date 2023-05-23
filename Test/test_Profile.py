import Profile
import pytest

test_profile = {"data": [[0, 100], [3600, 100], [10800, 1000], [14400, 1150], [16400, 1150], [19400, 700]], "type": "profile", "name": "fast"}

def test_get_target_temperature():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-fast.json")
    profile.current_segment = 0

    temperature = profile.get_target_temperature(3000)
    assert int(temperature) == 200

    temperature = profile.get_target_temperature(6004)
    assert temperature == 200 # Segment is stil 0, can't go above 200

    profile.current_segment = 1
    temperature = profile.get_target_temperature(6004)
    assert temperature == 801.0


def test_find_time_from_temperature():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-fast.json")

    time, segment = profile.find_next_time_from_temperature(500)
    assert time == 4800
    assert segment == 1

    time, segment = profile.find_next_time_from_temperature(2004)
    assert time == 10857.6
    assert segment == 2

    time, segment = profile.find_next_time_from_temperature(1900)
    assert time == 10400.0
    assert segment == 1

def test_find_time_odd_profile():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-cases.json")

    time, segment = profile.find_next_time_from_temperature(500)
    assert time == 4200
    assert segment == 2

    time, segment = profile.find_next_time_from_temperature(1023)
    assert time == 17876.0
    assert segment == 5


def test_find_x_given_y_on_line_from_two_points():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-fast.json")


    y = 500
    p1 = [3600, 200]
    p2 = [10800, 2000]
    time = profile.find_x_given_y_on_line_from_two_points(y, p1, p2)

    assert time == 4800

    y = 500
    p1 = [3600, 200]
    p2 = [10800, 200]
    time = profile.find_x_given_y_on_line_from_two_points(y, p1, p2)

    assert time == 0

    y = 500
    p1 = [3600, 600]
    p2 = [10800, 600]
    time = profile.find_x_given_y_on_line_from_two_points(y, p1, p2)

    assert time == 0

    y = 500
    p1 = [3600, 500]
    p2 = [10800, 500]
    time = profile.find_x_given_y_on_line_from_two_points(y, p1, p2)

    assert time == 0

def test_convert_old_profile():
    old_profile = test_profile
    new_profile = Profile.convert_old_profile(old_profile)

    assert 'fast' == new_profile['name']
    assert type(new_profile['segments']) is list
    assert new_profile['segments'][0] == {'time': 0, 'temperature': 100}
    assert new_profile['segments'][5] == {'time': 19400, 'temperature': 700}

def test_get_target_slope():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-fast.json")
    profile.current_segment = 0

    t_slope = profile.get_target_slope(3000)
    assert t_slope == 0

    t_slope = profile.get_target_slope(3599)
    assert t_slope == 0

    profile.current_segment = 1
    t_slope = profile.get_target_slope(3600)
    assert t_slope == 900.0

    profile.current_segment = 4
    t_slope = profile.get_target_slope(18000)
    assert t_slope == pytest.approx(-1860.0)

def test_get_profiles_list():
    profile = Profile.Profile()

    profiles = profile.get_profiles_names()

    assert len(profiles) >= 3
    assert {'name': 'test-fast'} in profiles

def test_delta_t_from_slope():
    profile = Profile.Profile()
    profile.load_profile_by_name("fast.json")
    profile.current_segment = 1

    time_since_start = 4300
    target = profile.get_target_temperature(time_since_start)
    min_temp = target - 6
    prev_point, next_point = profile.get_surrounding_points(time_since_start)

    delta_t = profile.delta_t_from_slope(prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t) == 530


    time_since_start = 7000
    target = profile.get_target_temperature(time_since_start)
    min_temp = target - 6
    prev_point, next_point = profile.get_surrounding_points(time_since_start)

    delta_t = profile.delta_t_from_slope(prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t) == 103



def test_delta_t_from_steep_slope():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-cases.json")
    profile.current_segment = 1

    time_since_start = 3800
    target = profile.get_target_temperature(time_since_start)
    min_temp = target - 6
    prev_point = profile.data[profile.current_segment]
    next_point = profile.data[profile.current_segment  + 1]

    delta_t = profile.delta_t_from_slope(prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t) == 38


    time_since_start = 4201
    target = profile.get_target_temperature(time_since_start)
    min_temp = target - 6
    prev_point = profile.data[profile.current_segment]
    next_point = profile.data[profile.current_segment  + 1]

    delta_t = profile.delta_t_from_slope(prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t) == 13

# 2023-05-15 07:14:36,632 DEBUG Profile: delta_t: -3600.0
# 2023-05-15 07:14:36,632 DEBUG Profile: min_temp: 199.6605512332587
# 2023-05-15 07:14:36,632 DEBUG Controller: target: 206.35399999999981
# 2023-05-15 07:14:36,733 DEBUG Profile: delta_t: -2.2737367544323206e-13
# 2023-05-15 07:14:36,733 DEBUG Profile: min_temp: 200.00684420783344
# 2023-05-15 07:14:36,733 DEBUG Controller: target: 500.0
def test_delta_t_from_wrong_segment():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-cases.json")
    profile.current_segment = 0

    time_since_start = 3613 # Segment 1
    target = profile.get_target_temperature(time_since_start)
    min_temp = 199.66
    prev_point = profile.data[profile.current_segment]
    next_point = profile.data[profile.current_segment  + 1]

    delta_t = profile.delta_t_from_slope(prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t) == -3600
