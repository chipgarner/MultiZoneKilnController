import time

import board
import digitalio
import Controller
import Server
from KilnZones import Zone
from KilnElectronics import Max31856, Max31855, FakeSwitches, SSR
import logging
from threading import Thread


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

htop = digitalio.DigitalInOut(board.D17) # These are the GPIO pins the heaters are soldered to.
htop.direction = digitalio.Direction.OUTPUT
hbottom = digitalio.DigitalInOut(board.D27)
hbottom.direction = digitalio.Direction.OUTPUT
zone1 = Zone(Max31855(SSR(htop)))
zone2 = Zone(Max31856(SSR(hbottom)))
zones = [zone1, zone2]

loop_delay = 10

broker = Server.broker
controller = Controller.Controller("fast.json", broker, zones, loop_delay)
time.sleep(0.1)
controller.control_loop()

