import logging
import time
from Notifiers import Notifier

import paho.mqtt.client as mqtt

from Notifiers.MQTT import check_internet


class Publisher(Notifier.Notifier):
    def __init__(self, access):
        self.logger = logging.getLogger(__name__)

        self.access = access

        self.mqtt_client = None
        self.start_mqtt_client()
        self.reconnect_tries = 0

    def start_mqtt_client(self):
        self.mqtt_client = mqtt.Client(client_id=self.getserial(), clean_session=False)
        self.mqtt_client.on_publish = self.on_publish

        #  Queued messages, e.g. while there is no internet, will collect and be sent to the broker
        #  quickly. Most brokers limit incoming messages, e.g. 20 per second.
        MAX_QUEUED_MESSAGES = 20
        self.mqtt_client.max_queued_messages_set(MAX_QUEUED_MESSAGES)

        self.mqtt_client.enable_logger(self.logger)
        self.mqtt_client.username_pw_set(self.access, None)
        try:
            self.mqtt_client.connect("mqtt.thingsboard.cloud", 1883, 0)
        except Exception as ex:
            self.logger.error('Publisher could not connect. ' + str(ex))

        self.mqtt_client.loop_start()
        self.logger.debug('Client loop started')

    def getserial(self):
        # Extract Raspberry Pi serial number from "cpuinfo" file
        cpu_serial = "0000000000001234"
        try:
            f = open('/proc/cpuinfo', 'r')
            for line in f:
                if line[0:6] == 'Serial':
                    cpu_serial = line[10:26]
            f.close()
        except:
            cpu_serial = "ERROR000000000"

        self.logger.info('Serial number: ' + cpu_serial)

        return cpu_serial

    def send_time_stamped_message(self, a_message: str) -> bool:
        return self.publish(a_message)

    def check_connection(self, rc):
        if rc == mqtt.MQTT_ERR_QUEUE_SIZE or rc == mqtt.MQTT_ERR_NO_CONN:
            internet = check_internet.check_internet_connection()
            self.logger.debug('Publish error code, que max or no conn. Internet: ' + str(internet))
            if internet:
                if self.reconnect_tries < 5:
                    try:
                        self.mqtt_client.reconnect()
                    except Exception as ex:
                        self.logger.error('Paho error in reconnect: ' + str(ex))
                        time.sleep(2)
                    self.reconnect_tries += 1
                else:  # This isn't working, start over. Broker disconnect?
                    self.mqtt_client.disconnect()
                    self.mqtt_client.loop_stop()
                    time.sleep(1)
                    self.mqtt_client = None
                    self.start_mqtt_client()
                    self.reconnect_tries = 0

            return False
        else:
            self.reconnect_tries = 0
            return True

    def publish(self, a_message):
        self.logger.debug('Publishing on mqtt, message: ' + a_message)
        infot = self.mqtt_client.publish('v1/devices/me/telemetry', a_message, qos=1)
        self.logger.debug('Paho info before checks =: ' + str(infot))

        if self.check_connection(infot.rc):
            try:
                infot.wait_for_publish(2)
                self.logger.debug('Paho info wait =: ' + str(infot))

                if infot.rc != 0:
                    self.logger.error('mqttc publish returned rc = ' + str(infot.rc))

                return True
            except RuntimeError:  # This is very intermittent, it should recover.
                self.logger.warning('Could not publish MQTT message.')
                return False
            except ValueError as ex:
                self.logger.warning(str(ex))
                if "ERR_QUEUE_SIZE" in str(ex):  # This should be checked above in check_connection()
                    return False
                else:
                    raise ex
        else:
            return False

    def on_publish(self, _, __, message_id):
        self.logger.debug('Published, id = ' + str(message_id))

    def stop(self):
        self.mqtt_client.disconnect()
