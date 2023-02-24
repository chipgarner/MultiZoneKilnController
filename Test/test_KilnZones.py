import pytest

import KilnZones
import threading


def test_init_heating():
    zone1 = KilnZones.SimZone()

    zone1.set_heat(0.1)

    assert zone1.heat_factor == 0.1

    zones = KilnZones.KilnZones([zone1])
    zones.set_heat_for_zones([0.2])

    assert zones.zones[0].heat_factor == 0.2


def test_starts_time_temps_thread():
    zone1 = KilnZones.SimZone()
    KilnZones.KilnZones([zone1])

    found = False
    for thread in threading.enumerate():
        if thread.name == 'KilnZones':
            found = True

    assert found


def test_updates_times_temperatures():
    zone1 = KilnZones.SimZone()
    zone1.set_heat(0.7)
    KilnZones.KilnZones([zone1])

    t_t_h = zone1.get_times_temps_heat()

    assert t_t_h[0][2] == 0.7
    assert type(t_t_h[0]) == tuple
    assert t_t_h[0][1] > 0  # Temperature
    assert t_t_h[0][0] > 0  # Time
    assert t_t_h[0][0] < 0.2


def test_bad_heat_factor_throws():
    zone1 = KilnZones.SimZone()

    with pytest.raises(ValueError):
        zone1.set_heat(1.09)

