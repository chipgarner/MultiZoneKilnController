import time

import Controller
import Server
import logging
from threading import Thread


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")

server_thread = Thread(target=Server.server, name="server", daemon=True)
server_thread.start()

broker = Server.broker
controller = Controller.Controller("fast.json", broker)
time.sleep(0.1)
controller.control_loop()

