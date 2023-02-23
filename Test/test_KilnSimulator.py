import KilnSimulator


def test_initial_temperature():
    sim = KilnSimulator.KilnSimulator()

    temp = sim.get_latest_temperature()

    assert temp == 27


def test_find_temperature():
    sim = KilnSimulator.KilnSimulator()

    temp = sim.find_temperature(0.1, 0.5)

    assert temp == 27.0117

