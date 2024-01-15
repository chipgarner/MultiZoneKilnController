import time
import Controller
import Server
from KilnZones import Zone
import logging
from threading import Thread
import config
from KilnElectronics import Electronics

log = logging.getLogger(__name__)

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

zones = []
if config.zone1 is not None:
    kiln_elec = Electronics(config.zone1['temperature_sensor'], config.zone1['power_controller'])
    zone1 = Zone(config.zone1['name'], kiln_elec, 2500, 10,  0.37)
    zones.append(zone1)
if config.zone2 is not None:
    kiln_elec = Electronics(config.zone2['temperature_sensor'], config.zone2['power_controller'])
    zone2 = Zone(config.zone2['name'], kiln_elec, 2500, 10,  0.37)
    zones.append(zone2)
if config.zone3 is not None:
    kiln_elec = Electronics(config.zone3['temperature_sensor'], config.zone3['power_controller'])
    zone3 = Zone(config.zone3['name'], kiln_elec, 2500, 10,  0.37)
    zones.append(zone3)
if config.zone4 is not None:
    kiln_elec = Electronics(config.zone4['temperature_sensor'], config.zone4['power_controller'])
    zone4 = Zone(config.zone4['name'], kiln_elec, 2500, 10,  0.37)
    zones.append(zone4)

broker = Server.broker
controller = Controller.Controller(broker, zones)
controller.control_loop.control_loop(config.loop_delay)
