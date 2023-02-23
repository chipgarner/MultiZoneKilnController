from Controller import Controller
import Profile
import KilnZones


def test_loads_profile():
    controller = Controller("test-fast.json")

    assert type(controller.profile) == Profile.Profile
    assert len(controller.profile.data) == 6


def test_init_temp_sensors():
    controller = Controller("test-fast.json")

    # assert type(controller.temp_sensors) == KilnZones.KilnZones()
