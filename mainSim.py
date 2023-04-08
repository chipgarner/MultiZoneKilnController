import time

import Controller
import Server
from KilnZones import KilnZones, SimZone
import logging
from threading import Thread


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

zone1 = SimZone('Zone 1')
zone2 = SimZone('Zone2')
zone3 = SimZone('Zone3')
zones = [zone1, zone2, zone3]

loop_delay = 30
if zone1.sim_speedup is not None:
    loop_delay = loop_delay / zone1.sim_speedup
    log.info('Sim speed up factor is ' + str(zone1.sim_speedup))

broker = Server.broker
controller = Controller.Controller("fast.json", broker, zones, loop_delay)
time.sleep(0.1)
controller.control_loop()

