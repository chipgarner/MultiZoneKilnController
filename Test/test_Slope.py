import Slope

def test_this():
    slope_instance = Slope.Slope(4)

    slope = slope_instance.slope(0, 0, 100, 0)
    assert slope == ('NA', 1)

    slope = slope_instance.slope(0, 1, 100, 0)
    assert slope[0] == 0.0

    slope = slope_instance.slope(0, 100, 101, 0)
    assert slope[0] == 36000.0


def test_index():
    slope_instance = Slope.Slope(4)

    slope = slope_instance.slope(3, 0, 100, 0)
    assert slope == ('NA', 1)

    slope = slope_instance.slope(3, 1, 100, 0)
    assert slope == (0.0, 2)

    slope = slope_instance.slope(3, 100, 101, 0)
    assert slope == (36000.0, 3)

def test_restart():
    slope_instance = Slope.Slope(4)

    slope = slope_instance.slope(3, 0, 100, 0)
    slope = slope_instance.slope(3, 1, 100, 0)
    slope = slope_instance.slope(3, 100, 101, 0)
    assert slope[0] == 36000.0

    assert len(slope_instance.long_smoothed_t_t_h_z[3]) == 3

    slope_instance.restart()
    assert len(slope_instance.long_smoothed_t_t_h_z[3]) == 0

    slope = slope_instance.slope(3, 0, 100, 0)
    assert slope == ('NA', 1)
    assert len(slope_instance.long_smoothed_t_t_h_z[3]) == 1