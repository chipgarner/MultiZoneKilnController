import logging
from Notifiers.MQTT import publisher
from Notifiers.MQTT.Secrets import TEST_SECRET

log = logging.getLogger(__name__)
# Notifiers can be API, MQTT, database ...

class Notifier():
    def __init__(self):
        self.publisher = publisher.Publisher(TEST_SECRET)

    def update(self, times_temps_heats_for_zones: list):
        self.update_thingsboard(times_temps_heats_for_zones)

    def update_thingsboard(self, times_temps_heats_for_zones: list):
        for latest_t_t_h in times_temps_heats_for_zones[0]:
        # latest_t_t_h = times_temps_heats_for_zones[-1]

            time_in_milliseconds = latest_t_t_h['time_ms']

            temp = latest_t_t_h['temperature']
            message = {'T1 56': temp}
            time_stamped_message = {"ts": time_in_milliseconds, "values": message}

            if not self.publisher.send_time_stamped_message(str(time_stamped_message)):
                # TODO handle this
                log.error('Sending failed.')
