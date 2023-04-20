import time

import Controller
import Server
from KilnZones import Zone
from KilnElectronics import Sim, Max31856, FakeSwitches
import logging
from threading import Thread


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

zone1 = Zone(Max31856(FakeSwitches()))
zones = [zone1]

loop_delay = 10

broker = Server.broker
controller = Controller.Controller("fast.json", broker, zones, loop_delay)
time.sleep(0.1)
controller.control_loop()

