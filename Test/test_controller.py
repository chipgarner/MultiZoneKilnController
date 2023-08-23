from Controller import Controller
import Profile
from KilnZones import KilnZones, Zone
from KilnElectronics import Sim
from KilnSimulator import ZoneTemps
import os
from Fakes import FakeBroker

profiles_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'TestFiles/Profiles'))


zone_temps = ZoneTemps()

sim_speed_up_factor = 1
zone1 = Zone(Sim('1', sim_speed_up_factor, zone_temps))
zone2 = Zone(Sim('2', sim_speed_up_factor, zone_temps))
zone3 = Zone(Sim('3', sim_speed_up_factor, zone_temps))
zone4 = Zone(Sim('4', sim_speed_up_factor, zone_temps))
zones = [zone1, zone2, zone3, zone4]

def test_loads_profile():
    controller = Controller(FakeBroker(), ['zony'], 10)
    controller.profile.profiles_directory = profiles_directory

    controller.set_profile_by_name('test-fast')

    assert type(controller.profile) == Profile.Profile
    assert len(controller.profile.data) == 6


def test_init_zones():
    controller = Controller(FakeBroker(), zones, 10)

    assert type(controller.kiln_zones) == KilnZones
    assert not controller.controller_state.get_state()['firing']

    for zone in controller.zones:
        assert zone.kiln_elec.get_heat_factor() == 0


def test_loop_calls():
    broker = FakeBroker()
    controller = Controller(broker, zones, 10)
    controller.start_time_ms = 0

    controller.loop_calls()

    assert broker.update_UI_calls == 1
    assert broker.update_calls == 1
    assert broker.update_names_calls == 1
    assert broker.controller_callbacks is not None

def test_modes():
    controller = Controller(FakeBroker(), zones, 10)
    assert not controller.controller_state.get_state()['firing']

    controller.start_stop_firing()
    assert not controller.controller_state.get_state()['firing'] # Can't strt if profile is not set

    controller.profile.profiles_directory = profiles_directory
    controller.set_profile_by_name('test-fast')

    controller.start_stop_firing()
    assert controller.controller_state.get_state()['firing']

    assert not controller.controller_state.get_state()['manual']
    controller.auto_manual()
    assert controller.controller_state.get_state()['manual']

    controller.auto_manual()
    assert  not controller.controller_state.get_state()['manual']

def test_no_profile_selected_sends_list():
    controller = Controller(FakeBroker(), zones, 10)

    message = controller.get_profile_names()

    assert len(message) >= 3
    assert type(message[0]) is dict

def test_profile_selected_sends_list():
    controller = Controller(FakeBroker(), zones, 10)
    controller.set_profile_by_name('fast')

    message = controller.get_profile_names()

    assert type(message) is list
