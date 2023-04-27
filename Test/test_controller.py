from Controller import Controller
import Profile
from KilnZones import KilnZones, Zone
from KilnElectronics import Sim


class FakeBroker:
    def __init__(self):
        self.update_calls = 0
        self.start = None
        self.stop = None

    def update_status(self, state, manual, times_temps_heats_for_zones: list):
        self.update_calls += 1
    def set_controller_functions(self, start_stop_firing, auto_manual):
        self.start = start_stop_firing
        self.stop = start_stop_firing
    def update_tc_data(self, tc_data: list):
        pass

    def update_profile_all(self, profile):
        pass

zone1 = Zone(Sim())
zone2 = Zone(Sim())
zone3 = Zone(Sim())
zone4 = Zone(Sim())
zones = [zone1, zone2, zone3, zone4]

def test_loads_profile():
    controller = Controller("test-fast.json", FakeBroker(), ['zony'], 10)

    assert type(controller.profile) == Profile.Profile
    assert len(controller.profile.data) == 6


def test_init_zones():
    controller = Controller("test-fast.json", FakeBroker(), zones, 10)

    assert type(controller.kiln_zones) == KilnZones
    assert controller.state == 'IDLE'

    for zone in controller.zones:
        assert zone.kiln_elec.heat_factor == 0


def test_loop_calls():
    broker = FakeBroker()
    controller = Controller("test-fast.json", broker, zones, 10)
    controller.start_time_ms = 0

    controller.loop_calls()

    assert broker.update_calls == 1
    assert broker.start is not None
    assert broker.stop is not None

def test_modes():
    controller = Controller("test-fast.json", FakeBroker(), zones, 10)

    assert controller.state == "IDLE"

    controller.start_stop_firing()
    assert controller.state == "FIRING"

    assert not controller.manual
    controller.auto_manual()
    assert controller.manual

    controller.auto_manual()
    assert  not controller.manual