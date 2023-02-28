import Controller
from MQTT.publisher import Publisher
from MQTT.Secrets import TEST_SECRET
import time
import logging



log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'

logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")



pub = Publisher(TEST_SECRET)

# message = {'T1 56': 77, 'T2 55': 75}
# time_in_seconds = round(time.time() * 1000)
# time_stamped_message = {"ts": time_in_seconds, "values": message}
# pub.send_message(str(time_stamped_message))
#
# {'ts': 50.09812355041504, 'values': {'T1 56': 32.8371357381851}}

controller = Controller.Controller("test-fast.json", pub.send_message)
controller.control_loop()

