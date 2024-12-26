import logging
import board
from KilnElectronics import Max31855, Max31856, SSR
from KilnSimulator import ZoneTemps


log_level = 'INFO'
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger(__name__)

simulating = False

if simulating:
    zone_temps = ZoneTemps()
    sim_speed_up_factor = 1 # Do not run at high speed with MQTT on or you will blitz the server.
else:
    try:
        zone1 = {'name': 'Top',
                 'temperature_sensor': Max31855(board.D5),
                 'power_controller': SSR(board.D17)}
        zone2 = None  #{'name': 'Bottom',
                # 'temperature_sensor': Max31856(board.D6),
                # 'power_controller': SSR(board.D27)}
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
Kp = 25
Ki = 0.3
Kd = 500
mqtt = True
