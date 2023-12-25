import board
from KilnElectronics import Max31855, Max31856, SSR
from KilnSimulator import ZoneTemps

LOG_LEVEL = 'INFO'

simulating = False

if simulating:
    zone_temps = ZoneTemps()
    sim_speed_up_factor = 100
else:
    zone1 = {'name': 'Top',
             'temperture_sensor': Max31855(board.D5),
             'power_controller': SSR(board.D17)}
    zone2 = {'name': 'Bottom',
             'temperture_sensor': Max31856(board.D6),
             'power_controller': SSR(board.D27)}
    zone3 = None
    zone4 = None

loop_delay = 20