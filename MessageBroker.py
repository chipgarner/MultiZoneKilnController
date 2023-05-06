import logging
import json
import time

from geventwebsocket import WebSocketError

from Database import DbInsertSelect

log = logging.getLogger(__name__)


class MessageBroker:
    def __init__(self):
        self.current_profile = None
        self.observers = []
        self.db = DbInsertSelect.DbInsertSelect()

        # Callbacks from Controller.py
        self.controller_callbacks = None

        # TODO
        # self.last_profile = {'name': 'fast',
        #                      'segments': [{'time': 0, 'temperature': 100}, {'time': 3600, 'temperature': 100},
        #                                   {'time': 10800, 'temperature': 1000}, {'time': 14400, 'temperature': 1150},
        #                                   {'time': 16400, 'temperature': 1150}, {'time': 19400, 'temperature': 700}]}
        # self.last_profile = self.profile_to_ms(self.last_profile)
        self.current_profile = None
        self.updated_profile = None
        self.prof_sent = False
        self.count = 0

    # Callback functions for access to Controller.p
    def set_controller_functions(self, contoller_callbacks: dict):
        self.controller_callbacks = contoller_callbacks

    def start_stop_firing(self):
        self.controller_callbacks['start_stop']()

    def auto_manual(self):
        self.controller_callbacks['auto_manual']()

    def set_heat_for_zone(self, heat, zone):
        self.controller_callbacks['set_heat_for_zone'](heat, zone)

    def add_observer(self, observer):
        self.update_profile(observer, self.current_profile)
        self.observers.append(observer)

        if self.updated_profile is not None:
            self.update_profile_all(self.updated_profile)

    def update_profile(self, observer, profile):
        prof = {
            'profile': profile,
        }
        prof_json = json.dumps(prof)
        try:
            observer.send(prof_json)
        except Exception as ex:
            log.error("Could not send profile to front end: " + str(ex))


    # Send to all observers
    def new_profile_all(self, profile):
        self.current_profile = profile
        prof = {
            'profile': profile,
        }
        prof_json = json.dumps(prof)
        self.send_socket(prof_json)


    def update_profile_all(self, profile):
        self.updated_profile = profile
        prof = {
            'profile_update': profile,
        }
        prof_json = json.dumps(prof)
        self.send_socket(prof_json)

    def update_status(self, state: str, manual: bool, zones_status_array: list):
        # self.update_thingsboard(times_temps_heats_for_zones) SIMULATOR SPEEDUP to 1 !!!= TODO fix mqtt
        # self.db.send_time_stamped_message(tthz) TODO

        status = {
            'state': state,
            'manual': manual,
            'zones_status_array': zones_status_array,
        }
        message = json.dumps(status)

        log.debug('Sending websocket length: ' + str(len(message)))
        log.debug('Sending websocket: ' + str(message))

        self.send_socket(message)


    def send_socket(self, message):
        for observer in self.observers:
            try:
                observer.send(message)
            except WebSocketError:
                self.observers.remove(observer)
                log.info('Observer deleted, socket error.')

    def update_tc_data(self, tc_data: list):
        thermocouple_data = { 'thermocouple_data': tc_data}
        message = json.dumps(thermocouple_data)
        self.send_socket(message)