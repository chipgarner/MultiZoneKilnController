import time
import Controller
import Server
from KilnZones import Zone
import logging
from threading import Thread
import config
from KilnElectronics import Electronics


log_level = config.LOG_LEVEL
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("MultiController")

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

zones = []
if config.zone1 is not None:
    kiln_elec = Electronics(config.zone1['temperture_sensor'], config.zone1['power_controller'])
    zone1 = Zone(kiln_elec, 2500, 10,  0.37)
    zones.append(zone1)
if config.zone2 is not None:
    kiln_elec = Electronics(config.zone2['temperture_sensor'], config.zone2['power_controller'])
    zone2 = Zone(kiln_elec, 2500, 10,  0.37)
    zones.append(zone2)
if config.zone3 is not None:
    kiln_elec = Electronics(config.zone3['temperture_sensor'], config.zone3['power_controller'])
    zone3 = Zone(kiln_elec, 2500, 10,  0.37)
    zones.append(zone3)
if config.zone4 is not None:
    kiln_elec = Electronics(config.zone4['temperture_sensor'], config.zone4['power_controller'])
    zone4 = Zone(kiln_elec, 2500, 10,  0.37)
    zones.append(zone4)

broker = Server.broker
controller = Controller.Controller(broker, zones, config.loop_delay)
time.sleep(0.1)
controller.control_loop()
