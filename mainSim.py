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

sim_speed_up_factor = 10
zone1 = Zone(Sim('1', sim_speed_up_factor))
zone2 = Zone(Sim('2', sim_speed_up_factor))
zone3 = Zone(Sim('3', sim_speed_up_factor))
zone4 = Zone(Sim('4', sim_speed_up_factor))
zone1.kiln_elec.kiln_sim.power = zone1.kiln_elec.kiln_sim.power + 600
zone3.kiln_elec.kiln_sim.power = zone3.kiln_elec.kiln_sim.power - 600
zone4.kiln_elec.kiln_sim.power = zone4.kiln_elec.kiln_sim.power + 600
zone1.kiln_elec.kiln_sim.heat_loss = zone1.kiln_elec.kiln_sim.heat_loss + 3
zone3.kiln_elec.kiln_sim.heat_loss = zone3.kiln_elec.kiln_sim.heat_loss - 3
zone3.kiln_elec.kiln_sim.heat_loss = zone4.kiln_elec.kiln_sim.heat_loss - 3
zones = [zone1, zone2, zone3]

loop_delay = 20
loop_delay = loop_delay / sim_speed_up_factor
log.info('Sim speed up factor is ' + str(sim_speed_up_factor))

broker = Server.broker
controller = Controller.Controller(broker, zones, loop_delay)
time.sleep(0.1)
controller.control_loop()

