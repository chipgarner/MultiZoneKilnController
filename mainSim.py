import time

import Controller
import Server
from KilnZones import Zone
from KilnSimulator import SimZone
import logging
from threading import Thread


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

zone1 = Zone('Zone 1', SimZone())
zone2 = Zone('Zone2', SimZone())
zone3 = Zone('Zone3', SimZone())
zone4 = Zone('Zone3', SimZone())
zone1.sim_zone.kiln_sim.power = zone1.sim_zone.kiln_sim.power + 600
zone3.sim_zone.kiln_sim.power = zone3.sim_zone.kiln_sim.power - 600
zone4.sim_zone.kiln_sim.power = zone4.sim_zone.kiln_sim.power + 600
zone1.sim_zone.kiln_sim.heat_loss = zone1.sim_zone.kiln_sim.heat_loss + 3
zone3.sim_zone.kiln_sim.heat_loss = zone3.sim_zone.kiln_sim.heat_loss - 3
zone3.sim_zone.kiln_sim.heat_loss = zone4.sim_zone.kiln_sim.heat_loss - 3
zones = [zone1, zone2, zone3, zone4]

loop_delay = 10
if zone1.sim_zone.kiln_sim.sim_speedup is not None:
    loop_delay = loop_delay / zone1.sim_zone.kiln_sim.sim_speedup
    log.info('Sim speed up factor is ' + str(zone1.sim_zone.kiln_sim.sim_speedup))

broker = Server.broker
controller = Controller.Controller("fast.json", broker, zones, loop_delay)
time.sleep(0.1)
controller.control_loop()

