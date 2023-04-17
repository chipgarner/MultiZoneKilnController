from Controller import Controller
import Profile
import KilnZones

class FakeBroker:
    def __init__(self):
        self.update_calls = 0
        self.start = None
        self.stop = None

    def update_status(self, state, times_temps_heats_for_zones: list):
        self.update_calls += 1
    def set_controller_functions(self, start_firing, stop_firing):
        self.start = start_firing
        self.stop = stop_firing

zone1 = KilnZones.SimZone('Zone 1')
zone2 = KilnZones.SimZone('Zone2')
zone3 = KilnZones.SimZone('Zone3')
zone4 = KilnZones.SimZone('Zone3')
zones = [zone1, zone2, zone3, zone4]

def test_loads_profile():
    controller = Controller("test-fast.json", FakeBroker(), ['zony'], 10)

    assert type(controller.profile) == Profile.Profile
    assert len(controller.profile.data) == 6


def test_init_zones():
    controller = Controller("test-fast.json", FakeBroker(), zones, 10)

    assert type(controller.kiln_zones) == KilnZones.KilnZones
    assert controller.state == 'IDLE'

    for zone in controller.zones:
        assert zone.heat_factor == 0


def test_loop_calls():
    broker = FakeBroker()
    controller = Controller("test-fast.json", broker, zones, 10)

    controller.loop_calls()

    assert broker.update_calls == 1
    assert broker.start is not None
    assert broker.stop is not None