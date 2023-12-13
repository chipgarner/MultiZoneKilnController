import Slope

# tth = [{'time_ms': 1691856261404, 'temperature': 27.656006608690678, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856263473, 'temperature': 25.936898991154976, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856265529, 'temperature': 26.51306607170794, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856267579, 'temperature': 26.991332865371334, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856269634, 'temperature': 27.735744101027436, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856271694, 'temperature': 28.169041947784383, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856273742, 'temperature': 27.087971014907957, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856275789, 'temperature': 26.633801074349996, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856277843, 'temperature': 25.799218810945273, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856279897, 'temperature': 28.485112042086165, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856281944, 'temperature': 27.973454421944325, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856283998, 'temperature': 27.204327773237534, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856286055, 'temperature': 28.264523126826234, 'heat_factor': 0.0, 'error': 0},
#        {'time_ms': 1691856288110, 'temperature': 26.488900951951592, 'heat_factor': 0.0, 'error': 0}]


def test_this():
    slope_instance = Slope.Slope(4)

    slope = slope_instance.slope(0, 0, 100, 0)
    assert slope == (None, None, None)

    slope_instance.slope(0, 1, 100, 0)
    slope_instance.slope(0, 1, 100, 0)
    slope_instance.slope(0, 1, 100, 0)
    slope = slope_instance.slope(0, 1, 100, 0)
    assert abs(slope[0]) < 0.001

    slope = slope_instance.slope(0, 10, 101, 0)
    assert int(slope[0]) == 262


def test_index():
    slope_instance = Slope.Slope(4)

    slope = slope_instance.slope(3, 0, 100, 0)
    assert slope == (None, None, None)
    slope = slope_instance.slope(3, 0, 100, 0)
    assert slope == (None, None, None)
    slope = slope_instance.slope(3, 0, 100, 0)
    assert slope == (None, None, None)
    slope = slope_instance.slope(3, 0, 100, 0)
    assert slope == (None, None, None)

    slope = slope_instance.slope(3, 1, 100, 0)
    assert slope[0] < -0.523
    assert slope[1] < -1047
    assert type(slope[2]) is list

    slope = slope_instance.slope(3, 100, 101, 0)
    assert int(slope[0]) == 14
    assert int(slope[1]) == -41


def test_get_latest_min_temp():
    slope = Slope.Slope(3)

    min_temp = slope.get_latest_min_temp()

    assert min_temp == 0

    slope.slope(2, 0, 108, 0)
    slope.slope(1, 0, 107, 0)
    slope.slope(0, 0, 106, 0)

    min_temp = slope.get_latest_min_temp()
    assert min_temp == 106

    slope.slope(2, 10, 105, 0)
    slope.slope(1, 10, 101, 0)
    slope.slope(0, 10, 103, 0)

    min_temp = slope.get_latest_min_temp()
    assert min_temp == 101


