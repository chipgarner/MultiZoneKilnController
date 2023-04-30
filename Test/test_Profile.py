import Profile
import pytest

test_profile = {"data": [[0, 100], [3600, 100], [10800, 1000], [14400, 1150], [16400, 1150], [19400, 700]], "type": "profile", "name": "fast"}

def test_get_target_temperature():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-fast.json")

    temperature = profile.get_target_temperature(3000)
    assert int(temperature) == 200

    temperature = profile.get_target_temperature(6004)
    assert temperature == 801.0


def test_find_time_from_temperature():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-fast.json")

    time = profile.find_next_time_from_temperature(500)
    assert time == 4800

    time = profile.find_next_time_from_temperature(2004)
    assert time == 10857.6

    time = profile.find_next_time_from_temperature(1900)
    assert time == 10400.0


def test_find_time_odd_profile():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-cases.json")

    time = profile.find_next_time_from_temperature(500)
    assert time == 4200

    time = profile.find_next_time_from_temperature(2023)
    assert time == 16676.0


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

    t_slope = profile.get_target_slope(3000)
    assert t_slope == 0

    t_slope = profile.get_target_slope(3599)
    assert t_slope == 0

    t_slope = profile.get_target_slope(3600)
    assert t_slope == 900.0


    t_slope = profile.get_target_slope(18000)
    assert t_slope == pytest.approx(-1860.0)

def test_udate_profile():
    profile = Profile.Profile()
    profile.load_profile_by_name("test-fast.json")

    profile.update_profile(10, 201, 12)
    assert profile.current_segment == 0  # It started

    profile.update_profile(10, 27, 12)

    assert profile.data[3][0] == 14422

    profile.update_profile(20, 199, 12)
    assert profile.current_segment == 0
    assert profile.data[3][0] == 14422

    assert profile.get_target_temperature(3700) == 219.5
    profile.update_profile(3700, 223, 12)
    assert profile.data[3][0] == 14422

def test_get_profiles_list():
    profile = Profile.Profile()

    profiles = profile.get_profiles_names()

    assert len(profiles) >= 3
    assert "test-fast.json" in profiles