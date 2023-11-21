import time

import Controller
import Server
from KilnZones import Zone
from KilnElectronics import Sim
from KilnSimulator import ZoneTemps
import logging
from threading import Thread


log_level = logging.INFO
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger(__name__)

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

zone_temps = ZoneTemps()

sim_speed_up_factor = 100
zone1 = Zone(Sim('Fred', sim_speed_up_factor, zone_temps), 3000, 20, 0.457)
zone2 = Zone(Sim('George', sim_speed_up_factor, zone_temps), 3000, 20, 0.457)
# zone3 = Zone(Sim('3', sim_speed_up_factor, zone_temps))
# zone4 = Zone(Sim('4', sim_speed_up_factor, zone_temps))
zone1.kiln_elec.kiln_sim.power = zone1.kiln_elec.kiln_sim.power - 400
# zone3.kiln_elec.kiln_sim.power = zone3.kiln_elec.kiln_sim.power - 300
# zone4.kiln_elec.kiln_sim.power = zone4.kiln_elec.kiln_sim.power + 300
zone1.kiln_elec.kiln_sim.heat_loss = zone1.kiln_elec.kiln_sim.heat_loss + 0.4
# zone3.kiln_elec.kiln_sim.heat_loss = zone3.kiln_elec.kiln_sim.heat_loss - 0.4
# zone3.kiln_elec.kiln_sim.heat_loss = zone4.kiln_elec.kiln_sim.heat_loss + 0.4
# Middle zones don't have a lid or floor.
# zone2.kiln_elec.kiln_sim.area_load = 0.157
# zone3.kiln_elec.kiln_sim.area_load = 0.157
#
zones = [zone1, zone2]

loop_delay = 20
loop_delay = loop_delay / sim_speed_up_factor
log.info('Sim speed up factor is ' + str(sim_speed_up_factor))

log.info('Zone temps: ' + str(zone_temps.new_temps))

broker = Server.broker
controller = Controller.Controller(broker, zones, loop_delay)
time.sleep(0.1)
controller.control_loop()


