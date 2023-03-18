import time

import Controller
import ControllerSocket
import logging


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'
logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")

controller = Controller.Controller("fast.json", ControllerSocket.ControllerSocket())
time.sleep(0.1)
controller.control_loop()

