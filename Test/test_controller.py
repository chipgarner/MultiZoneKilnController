from Controller import Controller
import Profile
from KilnZones import KilnZones, Zone
from KilnElectronics import Sim
import os

profiles_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'TestFiles/Profiles'))

class FakeBroker:
    def __init__(self):
        self.update_UI_calls = 0
        self.update_calls = 0
        self.update_names_calls = 0
        self.start = None
        self.stop = None

    def update_UI_status(self, state: dict):
        self.update_UI_calls += 1
    def update_zones(self, zones: list):
        self.update_calls += 1
    def update_names(self, zones: list):
        self.update_names_calls += 1
    def set_controller_functions(self, broker_to_controller_callbacks: dict):
        self.start = broker_to_controller_callbacks['start_stop']
        self.stop = self.start
    def update_tc_data(self, tc_data: list):
        pass

    def update_profile_all(self, profile):
        pass
    def new_profile_all(self, profile):
        pass

sim_speed_up_factor = 1
zone1 = Zone(Sim('1', sim_speed_up_factor))
zone2 = Zone(Sim('2', sim_speed_up_factor))
zone3 = Zone(Sim('3', sim_speed_up_factor))
zone4 = Zone(Sim('4', sim_speed_up_factor))
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
        assert zone.kiln_elec.heat_factor == 0


def test_loop_calls():
    broker = FakeBroker()
    controller = Controller(broker, zones, 10)
    controller.start_time_ms = 0

    controller.loop_calls()

    assert broker.update_UI_calls == 2
    assert broker.update_calls == 1
    assert broker.update_names_calls == 1
    assert broker.start is not None
    assert broker.stop is not None

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
