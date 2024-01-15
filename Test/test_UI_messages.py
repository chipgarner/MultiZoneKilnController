from Fakes import FakeBroker
from Controller import Controller
from KilnZones import Zone
from KilnElectronics import Sim
from KilnSimulator import  ZoneTemps

zone_temps = ZoneTemps()

sim_speed_up_factor = 1
zone1 = Zone('Top', Sim('1', sim_speed_up_factor, zone_temps))
zone2 = Zone('Next', Sim('Test', sim_speed_up_factor, zone_temps))
zone3 = Zone('Here', Sim('3', sim_speed_up_factor, zone_temps))
zone4 = Zone('Bottom', Sim('4', sim_speed_up_factor, zone_temps))
zones = [zone1, zone2, zone3, zone4]


def test_UI_adds_observer_idle():
    broker = FakeBroker()
    controller = Controller(broker, zones)

    broker.add_observer('me')

    assert controller.controller_state.get_UI_status_dict()['label'] == 'IDLE'
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
    broker = FakeBroker()
    controller = Controller(broker, zones)
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
