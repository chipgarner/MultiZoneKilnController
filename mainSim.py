import time

import Controller
import Server
from KilnZones import Zone
from KilnElectronics import Sim
import logging
from threading import Thread


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

zone1 = Zone(Sim())
zone2 = Zone(Sim())
zone3 = Zone(Sim())
zone4 = Zone(Sim())
zone1.kiln_elec.kiln_sim.power = zone1.kiln_elec.kiln_sim.power + 600
zone3.kiln_elec.kiln_sim.power = zone3.kiln_elec.kiln_sim.power - 600
zone4.kiln_elec.kiln_sim.power = zone4.kiln_elec.kiln_sim.power + 600
zone1.kiln_elec.kiln_sim.heat_loss = zone1.kiln_elec.kiln_sim.heat_loss + 3
zone3.kiln_elec.kiln_sim.heat_loss = zone3.kiln_elec.kiln_sim.heat_loss - 3
zone3.kiln_elec.kiln_sim.heat_loss = zone4.kiln_elec.kiln_sim.heat_loss - 3
zones = [zone1, zone2]

loop_delay = 10
if zone1.kiln_elec.kiln_sim.sim_speedup is not None:
    loop_delay = loop_delay / zone1.kiln_elec.kiln_sim.sim_speedup
    log.info('Sim speed up factor is ' + str(zone1.kiln_elec.kiln_sim.sim_speedup))

broker = Server.broker
controller = Controller.Controller("fast.json", broker, zones, loop_delay)
time.sleep(0.1)
controller.control_loop()

