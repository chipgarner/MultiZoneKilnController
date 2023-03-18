import logging
import json


import websockets, asyncio

log = logging.getLogger(__name__)

class ControllerSocket:

    def update(self, times_temps_heats_for_zones: dict):
        log.debug('Updating: ' + str(times_temps_heats_for_zones))
        self.xmit_loop(json.dumps(times_temps_heats_for_zones))  # TODO use the same tech on server and here. don't close every timme?

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
