import time

import Controller
import Server
from KilnZones import Zone
from KilnElectronics import Sim

import logging
from threading import Thread
import config

log = logging.getLogger(__name__)

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

zone1 = Zone(Sim('Fred', config.sim_speed_up_factor, config.zone_temps), 3000, 20, 0.37)
zone2 = Zone(Sim('George', config.sim_speed_up_factor, config.zone_temps), 3000, 20, 0.37)
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

loop_delay = config.loop_delay / config.sim_speed_up_factor
log.info('Sim speed up factor is ' + str(config.sim_speed_up_factor))

log.info('Zone temps: ' + str(config.zone_temps.new_temps))

broker = Server.broker
controller = Controller.Controller(broker, zones)
controller.control_loop.control_loop(loop_delay)


