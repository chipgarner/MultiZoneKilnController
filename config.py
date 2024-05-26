import logging
import board
from KilnElectronics import Max31855, Max31856, SSR
from KilnSimulator import ZoneTemps


log_level = 'INFO'
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger(__name__)

simulating = True

if simulating:
    zone_temps = ZoneTemps()
    sim_speed_up_factor = 10
else:
    try:
        zone1 = {'name': 'Top',
                 'temperature_sensor': Max31855(board.D5),
                 'power_controller': SSR(board.D17)}
        zone2 = {'name': 'Bottom',
                 'temperature_sensor': Max31856(board.D6),
                 'power_controller': SSR(board.D27)}
        zone3 = None
        zone4 = None
    except AttributeError as err:
        log.error('No valid blinka board found, simulating is False. ')
        raise (err)

loop_delay = 5 # Seconds
moving_average_length = 5 # Number of measurements to average, time depends on how often temperature is read at the
# sensors.
slope_smoothing_length = 60 # Multiply times loop_delay for time.
control_method = 'PID'
mqtt = False
