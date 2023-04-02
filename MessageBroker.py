import logging
import json
import time

from geventwebsocket import WebSocketError

from Database import DbInsertSelect

log = logging.getLogger(__name__)


class MessageBroker:
    def __init__(self):
        self.last_profile = None
        self.observers = []
        self.db = DbInsertSelect.DbInsertSelect()

        # Callbacks from Controller.py
        self.controller_start_firing = None
        self.controller_stop_firing = None


        # TODO
        self.last_profile = {'name': 'fast',
                             'segments': [{'time': 0, 'temperature': 100}, {'time': 3600, 'temperature': 100},
                                          {'time': 10800, 'temperature': 1000}, {'time': 14400, 'temperature': 1150},
                                          {'time': 16400, 'temperature': 1150}, {'time': 19400, 'temperature': 700}]}
        self.last_profile = self.profile_to_ms(self.last_profile)
        self.prof_sent = False
        self.count = 0

    # Callback functions for access to Controller.p
    def set_controller_functions(self, start_firing, stop_firing):
        self.controller_start_firing = start_firing
        self.controller_stop_firing = stop_firing

    def start_firing(self):
        self.controller_start_firing()
    def stop_firing(self):
        self.controller_stop_firing()

    def profile_to_ms(self, profile):
        now = time.time()
        for segment in profile['segments']:
            segment['time_ms'] = round((segment['time'] + now) * 1000)
        return profile

    def add_observer(self, observer):
        self.update_profile(observer, self.last_profile)
        self.observers.append(observer)

    def update_profile(self, observer, profile):
        prof = {
            'profile': profile,
        }
        prof_json = json.dumps(prof)
        try:
            observer.send(prof_json)
        except Exception as ex:
            log.error("Could not send profile to front end: " + str(ex))

    def update(self, times_temps_heats_for_zones: dict):
        # self.update_thingsboard(times_temps_heats_for_zones) SIMULATOR SPEEDUP to 1 !!!= TODO fix mqtt
        tthz = times_temps_heats_for_zones
        log.debug('Updating: ' + str(tthz))

        # self.db.send_time_stamped_message(tthz)

        message = json.dumps([tthz['Zone 1']])
        for observer in self.observers:
            try:
                observer.send(message)
            except WebSocketError:
                self.observers.remove(observer)
                log.info('Observer deleted, socket error.')
