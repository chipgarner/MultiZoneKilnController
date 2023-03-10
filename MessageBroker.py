import logging
import json

log = logging.getLogger(__name__)


class MessageBroker:
    def __init__(self):
        self.last_profile = None
        self.observers = []

    def add_observer(self, observer):
        if self.last_profile:
            p = {
                "name": self.last_profile.name,
                "data": self.last_profile.data,
                "type": "profile"
            }
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
