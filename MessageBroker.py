import logging
import json
import threading

from geventwebsocket import WebSocketError

log = logging.getLogger(__name__)


class MessageBroker:
    def __init__(self):
        self.observers = []
        # self.db = DbInsertSelect.DbInsertSelect()

        # Callbacks from Controller.py
        self.controller_callbacks = None

        self.original_profile = None
        self.updated_profile = None
        self.profile_names = None

        self.lock = threading.Lock()

    # Callback functions for access to Controller.p
    def set_controller_functions(self, contoller_callbacks: dict):
        self.controller_callbacks = contoller_callbacks

    def start_stop_firing(self):
        self.controller_callbacks['start_stop']()

    def auto_manual(self):
        self.controller_callbacks['auto_manual']()

    def set_heat_for_zone(self, heat, zone):
        self.controller_callbacks['set_heat_for_zone'](heat, zone)

    def set_profile(self, profile_name: str):
        self.controller_callbacks['set_profile_by_name'](profile_name)

    def add_observer(self, observer):
        names = self.controller_callbacks['get_profile_names']()

        if self.original_profile is not None:
            self.update_profile(observer, self.original_profile)
        self.observers.append(observer)

        if self.updated_profile is not None:
            self.update_profile_all(self.updated_profile)
        if names is not None:
            self.profile_names = names
            self.update_names(names)

    def update_names(self, names: list):
        profile_names = {
            'profile_names': names
        }
        names_json = json.dumps(profile_names)
        log.debug("Names " + names_json)
        self.send_socket(names_json)

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
        self.original_profile = profile
        prof = {
            'profile': profile,
        }
        prof_json = json.dumps(prof)
        log.debug("New " + prof_json)
        self.send_socket(prof_json)


    def update_profile_all(self, profile):
        self.updated_profile = profile
        prof = {
            'profile_update': profile,
        }
        prof_json = json.dumps(prof)
        log.debug("Update " + prof_json)
        self.send_socket(prof_json)

    def update_UI_status(self, UI_message: dict):
        status = {
            'status': UI_message
        }
        message = json.dumps(status)
        self.send_socket(message)
        log.debug('Status sent: ' + message)

    def update_zones(self, zones_status_array: list):
        # self.update_thingsboard(times_temps_heats_for_zones) SIMULATOR SPEEDUP to 1 !!!= TODO fix mqtt
        # self.db.send_time_stamped_message(tthz) TODO
        zones = {
            'zones_status_array': zones_status_array,
        }
        message = json.dumps(zones)
        self.send_socket(message)

    def send_socket(self, message):
        for observer in self.observers:
            try:
                with self.lock:
                    observer.send(message)
            except WebSocketError:
                self.observers.remove(observer)
                log.info('Observer deleted, socket error.')

    def update_tc_data(self, tc_data: list):
        thermocouple_data = { 'thermocouple_data': tc_data}
        message = json.dumps(thermocouple_data)
        self.send_socket(message)