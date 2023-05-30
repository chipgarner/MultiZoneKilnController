import MessageBroker
from Controller import Controller
from KilnZones import KilnZones, Zone
from KilnElectronics import Sim


zone1 = Zone(Sim('1'))
zone2 = Zone(Sim('2'))
zone3 = Zone(Sim('3'))
zone4 = Zone(Sim('4'))
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

    assert broker.u_names_called
    assert controller.controller_state.get_UI_status()['label'] == 'IDLE'
    assert len(broker.profile_names) > 2
    assert broker.UI_message == {
            'label': 'IDLE',
            'StartStop': 'Start',
            'StartStopDisabled': True,
            'Manual': False,
            'ManualDisabled': True,
            'ProfileName': 'None',
            'ProfileNames': broker.profile_names,
            'ProfileSelectDisabled': False,
        }

def test_choose_profile():
    broker = TestBroker()
    controller = Controller(broker, zones, 10)
    broker.add_observer('me')

    broker.set_profile("fast")

    assert len(broker.profile_names) > 2
    assert broker.UI_message == {
            'label': 'IDLE',
            'StartStop': 'Start',
            'StartStopDisabled': False,
            'Manual': False,
            'ManualDisabled': True,
            'ProfileName': 'fast.json',
            'ProfileNames': broker.profile_names,
            'ProfileSelectDisabled': False,
        }
