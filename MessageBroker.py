import logging
import json

from geventwebsocket import WebSocketError

from Database import DbInsertSelect

log = logging.getLogger(__name__)


class MessageBroker:
    def __init__(self):
        self.last_profile = None
        self.observers = []
        self.db = DbInsertSelect.DbInsertSelect()

        # TODO
        profile_data = self.db.get_profile_by_name('fast')
        self.last_profile = {'name': 'fast', 'data': profile_data}


    def add_observer(self, observer):
        if self.last_profile:
            p = json.dumps(self.last_profile)
            #     {
            #     "name": self.last_profile.name,
            #     "data": self.last_profile.data,
            # }
        else:
            p = None

        backlog = {
            'type': "backlog",
            'profile': p,
            # 'log': self.lastlog_subset(),
            # 'started': self.started
        }
        print(backlog)
        backlog_json = json.dumps(backlog)
        try:
            print(backlog_json)
            observer.send(backlog_json)
        except:
            log.error("Could not send backlog to new observer")

        self.observers.append(observer)

    def update(self, times_temps_heats_for_zones: str):
        # self.update_thingsboard(times_temps_heats_for_zones) SIMULATOR SPEEDUP to 1 !!!= TODO fix mqtt
        tthz = json.loads(times_temps_heats_for_zones)
        log.debug('Updating: ' + str(tthz))

        # self.db.send_time_stamped_message(tthz)

        message = json.dumps(tthz['Zone 1'])
        for observer in self.observers:
            try:
                observer.send(message)
            except WebSocketError:
                self.observers.remove(observer)
                log.info('Observer deleted, socket error.')
