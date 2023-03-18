import logging
import json
from Notifiers.MQTT import publisher
from Notifiers.MQTT.Secrets import TEST_SECRET
#TODO connect this to messagebroker and allow sending to mqtt, no web sockets here.
from Experiments import Pygal
import websockets, asyncio

log = logging.getLogger(__name__)
# Notifiers can be API, MQTT, database ...

class Notifier:
    def __init__(self):
        pass
        # self.publisher = publisher.Publisher(TEST_SECRET)
        # self.db_inserter = DbInsert.DbInsert()
        # self.pygal = Pygal.Pygal()

    def update(self, times_temps_heats_for_zones: dict):
        # self.update_thingsboard(times_temps_heats_for_zones) SIMULATOR SPEEDUP to 1 !!!
        log.debug('Updating: ' + str(times_temps_heats_for_zones))
        # self.db_inserter.send_time_stamped_message(times_temps_heats_for_zones)
        # self.pygal.plot(times_temps_heats_for_zones)
        self.xmit_loop(json.dumps(times_temps_heats_for_zones))  # TODO use the same tech on server and here. don't close every timme?

    def update_thingsboard(self, times_temps_heats_for_zones: list):
        listed = []
        for latest_t_t_h in times_temps_heats_for_zones[0]:
        # latest_t_t_h = times_temps_heats_for_zones[-1]

            time_in_milliseconds = latest_t_t_h['time_ms']

            temp = latest_t_t_h['temperature']
            message = {'T1 56': temp}
            time_stamped_message = {"ts": time_in_milliseconds, "values": message}
            listed.append(time_stamped_message)

        if not self.publisher.send_time_stamped_message(str(listed)):
                # TODO handle this
            log.error('Sending failed.')

    @staticmethod
    async def forward(message):
        url = 'ws://localhost:8081/controller'
        async with websockets.connect(url) as websocket:
            await websocket.send(message)


    def xmit_loop(self, message):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.forward(message))
        except ConnectionRefusedError as ex:
            log.error(ex)
