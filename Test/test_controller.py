from Controller import Controller
import Profile
import KilnZones

class FakeNotifier:
    def update(self, times_temps_heats_for_zones: list):
        pass

def test_loads_profile():
    controller = Controller("test-fast.json", FakeNotifier())

    assert type(controller.profile) == Profile.Profile
    assert len(controller.profile.data) == 6


def test_init_zones():
    controller = Controller("test-fast.json", FakeNotifier())

    assert type(controller.kiln_zones) == KilnZones.KilnZones
