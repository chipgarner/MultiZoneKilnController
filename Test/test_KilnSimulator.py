from KilnSimulator import KilnSimulator, ZoneTemps
import logging

def test_initial_temperature():
    zone_temps = ZoneTemps()
    sim = KilnSimulator('Zoney', 1, zone_temps)

    temp = sim.get_latest_temperature()

    assert temp == 27


def test_find_temperature(caplog):
    caplog.set_level(logging.DEBUG)
    zone_temps = ZoneTemps()
    sim = KilnSimulator('Zoney', 1, zone_temps)

    temp = sim.find_temperature(0.1, 0)

    assert temp == 27.0

    temp = sim.find_temperature(1.0, .5)
    temp = sim.find_temperature(1.0, .5)
    print(caplog.text)

    assert temp == 27.0


