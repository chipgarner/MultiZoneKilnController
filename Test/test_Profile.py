import time

import Profile
import pytest
import os

test_profile = {"data": [[0, 100], [3600, 100], [10800, 1000], [14400, 1150], [16400, 1150], [19400, 700]], "type": "profile", "name": "fast"}
profiles_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'TestFiles/Profiles'))

def test_get_target_temperature():
    profile = Profile.Profile()
    profile.profiles_directory = profiles_directory
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
    profile.profiles_directory = profiles_directory
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
    profile.profiles_directory = profiles_directory
    profile.load_profile_by_name("test-cases.json")

    time, segment = profile.find_next_time_from_temperature(500)
    assert time == 4200
    assert segment == 2

    time, segment = profile.find_next_time_from_temperature(1023)
    assert time == 17876.0
    assert segment == 5


def test_find_x_given_y_on_line_from_two_points():
    profile = Profile.Profile()
    profile.profiles_directory = profiles_directory
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

def test_save_old_profile_as_new():
    old_profile = test_profile
    Profile.save_old_profile_as_new(old_profile)

def test_get_target_slope():
    profile = Profile.Profile()
    profile.profiles_directory = profiles_directory
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
    profile.profiles_directory = profiles_directory
    profiles = profile.get_profiles_names()

    assert len(profiles) >= 3
    assert {'name': 'test-fast'} in profiles

def test_delta_t_from_slope():
    profile = Profile.Profile()
    profile.profiles_directory = profiles_directory
    profile.load_profile_by_name("fast.json")
    profile.current_segment = 1

    time_since_start = 4300
    target = profile.get_target_temperature(time_since_start)
    min_temp = target - 6
    prev_point, next_point = profile.get_surrounding_points(time_since_start)
    slope = 350

    delta_t_prev, delta_t_next = profile.delta_ts_from_slope(slope, prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t_prev) == -138
    assert int(delta_t_next) == 1918


    time_since_start = 7000
    target = profile.get_target_temperature(time_since_start)
    min_temp = target - 6
    prev_point, next_point = profile.get_surrounding_points(time_since_start)

    delta_t_prev, delta_t_next = profile.delta_ts_from_slope(slope, prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t_prev) == -909
    assert int(delta_t_next) == 1147



def test_delta_t_from_steep_slope():
    profile = Profile.Profile()
    profile.profiles_directory = profiles_directory
    profile.load_profile_by_name("test-cases.json")
    profile.current_segment = 1

    time_since_start = 3800
    target = profile.get_target_temperature(time_since_start)
    min_temp = target - 6
    prev_point = profile.data[profile.current_segment]
    next_point = profile.data[profile.current_segment  + 1]
    slope = 300

    delta_t_prev, delta_t_next = profile.delta_ts_from_slope(slope, prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t_prev) == -928
    assert int(delta_t_next) == 2072

    time_since_start = 4201
    target = profile.get_target_temperature(time_since_start)
    min_temp = target - 6
    prev_point = profile.data[profile.current_segment]
    next_point = profile.data[profile.current_segment  + 1]

    delta_t_prev, delta_t_next = profile.delta_ts_from_slope(slope, prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t_prev) == -2927
    assert int(delta_t_next) == 73


def test_delta_t_from_wrong_segment():
    profile = Profile.Profile()
    profile.profiles_directory = profiles_directory
    profile.load_profile_by_name("test-cases.json")
    profile.current_segment = 0

    time_since_start = 3613 # Segment 1
    target = profile.get_target_temperature(time_since_start)
    min_temp = 199.66
    prev_point = profile.data[profile.current_segment]
    next_point = profile.data[profile.current_segment  + 1]
    slope = 250

    delta_t_prev, delta_t_next = profile.delta_ts_from_slope(slope, prev_point, next_point, time_since_start, min_temp)

    assert int(delta_t_prev) == 3617
    assert int(delta_t_next) == 17

def test_shift_profile():
    profile = Profile.Profile()
    profile.profiles_directory = profiles_directory
    profile.load_profile_by_name("test-cases.json")
    profile.current_segment = 1

    t1 = profile.data[1][0]
    t2 = profile.data[2][0]
    t4 = profile.data[4][0]
    t6 = profile.data[6][0]

    assert t2 == 4200

    time_since_start = 3613
    min_temp = 300
    zones_status = [{'slope': 400, 'stderror': 9}]
    zone_index = 0
    profile.last_profile_change = time.time() - 650

    update = profile.check_shift_profile(time_since_start, min_temp, zones_status, zone_index)

    # 200 degrees to go at 100 degrees per hour,
    assert update
    assert round(profile.data[1][0]) == 2713
    assert round(profile.data[2][0]) == 5413
    assert  round(profile.data[4][0]) == 15613
    assert round(profile.data[6][0]) == 20613

    target_slope = profile.get_target_slope(3650)
    assert int(target_slope) == 400

    zones_status = [{'slope': 200, 'stderror': 9}]
    profile.check_shift_profile(time_since_start, min_temp, zones_status, zone_index)

    target_slope = profile.get_target_slope(3650)
    assert int(target_slope) == 200