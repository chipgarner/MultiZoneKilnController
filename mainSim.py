import time

import Controller
import Server
from KilnZones import SimZone
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
zone4 = SimZone('Zone3')
zone1.kiln_sim.power = zone1.kiln_sim.power + 600
zone3.kiln_sim.power = zone3.kiln_sim.power - 600
zone4.kiln_sim.power = zone4.kiln_sim.power + 600
zone1.kiln_sim.heat_loss = zone1.kiln_sim.heat_loss + 3
zone3.kiln_sim.heat_loss = zone3.kiln_sim.heat_loss - 3
zone3.kiln_sim.heat_loss = zone4.kiln_sim.heat_loss - 3
zones = [zone1, zone2, zone3, zone4]

loop_delay = 10
if zone1.sim_speedup is not None:
    loop_delay = loop_delay / zone1.sim_speedup
    log.info('Sim speed up factor is ' + str(zone1.sim_speedup))

broker = Server.broker
controller = Controller.Controller("fast.json", broker, zones, loop_delay)
time.sleep(0.1)
controller.control_loop()

