import time
import pytest
import KilnZones
import threading
from Fakes import FakeBroker
from KilnElectronics import Sim
from KilnSimulator import ZoneTemps

zone_temps = ZoneTemps()

def test_init_heating():
    zone1 = KilnZones.Zone('Test', Sim('Test', 1, zone_temps))

    zone1.set_heat_factor(0.1)

    assert zone1.kiln_elec.get_heat_factor() == 0.1

    zones = KilnZones.KilnZones([zone1], FakeBroker())
    zones.set_heat_for_zones([0.2])

    assert zones.zones[0].kiln_elec.get_heat_factor() == 0.2


def test_starts_time_temps_thread():
    zone1 = KilnZones.Zone('Test', Sim('Test', 1, zone_temps))
    KilnZones.KilnZones([zone1], FakeBroker())

    found = False
    for thread in threading.enumerate():
        if thread.name == 'KilnZones':
            found = True

    assert found


def test_updates_times_temperatures():
    zone1 = KilnZones.Zone('Test', Sim('Test', 1, zone_temps))
    zone1.set_heat_factor(0.7)
    KilnZones.KilnZones([zone1], FakeBroker())
    time.sleep(1)  # Let the zones thread start and TC read

    t_t_h = zone1.get_time_temp_heat()

    assert t_t_h['heat_factor'] == 0.7
    assert type(t_t_h) == dict
    assert t_t_h['temperature'] > 0

    now = time.time() * 1000
    delta_t = now - t_t_h['time_ms'] # delta_t should be small
    # assert delta_t > -1 # It goes further negative if the Simulator speedup is greater than 1.
    assert delta_t - 1000 < 10 # millisconds, subtracte wait time for tc read.

    last_heat_timme = zone1.get_last_heat_change_time()
    assert type(last_heat_timme) == int
    assert last_heat_timme == 2 # This is basically the TC read delay and round off


def test_bad_heat_factor_throws():
    zone1 = KilnZones.Zone('Test', Sim('Test', 1, zone_temps))

    with pytest.raises(ValueError):
        zone1.set_heat_factor(1.09)

