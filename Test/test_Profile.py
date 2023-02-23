from Profile import Profile


def test_get_target_temperature():
    profile = Profile("test-fast.json")

    temperature = profile.get_target_temperature(3000)
    assert int(temperature) == 200

    temperature = profile.get_target_temperature(6004)
    assert temperature == 801.0


def test_find_time_from_temperature():
    profile = Profile("test-fast.json")

    time = profile.find_next_time_from_temperature(500)
    assert time == 4800

    time = profile.find_next_time_from_temperature(2004)
    assert time == 10857.6

    time = profile.find_next_time_from_temperature(1900)
    assert time == 10400.0


def test_find_time_odd_profile():
    profile = Profile("test-cases.json")

    time = profile.find_next_time_from_temperature(500)
    assert time == 4200

    time = profile.find_next_time_from_temperature(2023)
    assert time == 16676.0


def test_find_x_given_y_on_line_from_two_points():
    profile = Profile("test-fast.json")

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
