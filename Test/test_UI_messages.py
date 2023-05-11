import MessageBroker
from Controller import Controller
from KilnZones import KilnZones, Zone
from KilnElectronics import Sim


zone1 = Zone(Sim())
zone2 = Zone(Sim())
zone3 = Zone(Sim())
zone4 = Zone(Sim())
zones = [zone1, zone2, zone3, zone4]

class TestBroker(MessageBroker.MessageBroker):
    def __init__(self):
        self.u_names_called = False
        MessageBroker.MessageBroker.__init__(self)

    def update_names(self, names: list):
        self.u_names_called = True


def test_UI_adds_observer_idle():
    broker = TestBroker()
    controller = Controller(broker, zones, 10)

    broker.add_observer('me')

    assert broker.u_names_called

    assert controller.controller_state.get_UI_status()['label'] == 'IDLE'