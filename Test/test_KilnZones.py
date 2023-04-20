import time
import pytest
import KilnZones
import threading
from test_controller import FakeBroker
from KilnElectronics import Sim


def test_init_heating():
    zone1 = KilnZones.Zone(Sim())

    zone1.set_heat(0.1)

    assert zone1.kiln_elec.heat_factor == 0.1

    zones = KilnZones.KilnZones([zone1], FakeBroker())
    zones.set_heat_for_zones([0.2])

    assert zones.zones[0].kiln_elec.heat_factor == 0.2


def test_starts_time_temps_thread():
    zone1 = KilnZones.Zone(Sim())
    KilnZones.KilnZones([zone1], FakeBroker())

    found = False
    for thread in threading.enumerate():
        if thread.name == 'KilnZones':
            found = True

    assert found


def test_updates_times_temperatures():
    zone1 = KilnZones.Zone(Sim())
    zone1.set_heat(0.7)
    KilnZones.KilnZones([zone1], FakeBroker())
    time.sleep(0.1)  # Let the zones thread start

    t_t_h = zone1.get_times_temps_heat()

    assert t_t_h[0]['heat_factor'] == 0.7
    assert type(t_t_h[0]) == dict
    assert t_t_h[0]['temperature'] > 0

    now = time.time() * 1000
    delta_t = now - t_t_h[0]['time_ms'] # delta_t should be small
    # assert delta_t > -1 # It goes further negative if the Simulator speedup is greater than 1.
    assert delta_t < 200 # millisconds


def test_bad_heat_factor_throws():
    zone1 = KilnZones.Zone(Sim())

    with pytest.raises(ValueError):
        zone1.set_heat(1.09)

