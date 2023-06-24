import MessageBroker
from Controller import Controller
from KilnZones import KilnZones, Zone
from KilnElectronics import Sim

sim_speed_up_factor = 1
zone1 = Zone(Sim('1', sim_speed_up_factor))
zone2 = Zone(Sim('2', sim_speed_up_factor))
zone3 = Zone(Sim('3', sim_speed_up_factor))
zone4 = Zone(Sim('4', sim_speed_up_factor))
zones = [zone1, zone2, zone3, zone4]

class TestBroker(MessageBroker.MessageBroker):
    def __init__(self):
        self.u_names_called = False
        self.UI_message = None
        MessageBroker.MessageBroker.__init__(self)

    def update_names(self, names: list):
        self.u_names_called = True

    def update_UI_status(self, UI_message: dict):
        self.UI_message = UI_message

    def new_profile_all(self, profile):
        pass

    def update_profile_all(self, profile):
        pass


def test_UI_adds_observer_idle():
    broker = TestBroker()
    controller = Controller(broker, zones, 10)

    broker.add_observer('me')

    assert controller.controller_state.get_UI_status()['label'] == 'IDLE'
    assert broker.UI_message == {
            'label': 'IDLE',
            'StartStop': 'Start',
            'StartStopDisabled': True,
            'Manual': False,
            'ManualDisabled': True,
            'ProfileName': 'None',
            'ProfileSelectDisabled': False,
        }

def test_choose_profile():
    broker = TestBroker()
    controller = Controller(broker, zones, 10)
    broker.add_observer('me')

    broker.set_profile("fast")

    assert broker.UI_message == {
            'label': 'IDLE',
            'StartStop': 'Start',
            'StartStopDisabled': False,
            'Manual': False,
            'ManualDisabled': True,
            'ProfileName': 'fast',
            'ProfileSelectDisabled': False,
        }
