from abc import ABC, abstractmethod

# Notifiers can be API, MQTT, database ...

class Notifier(ABC):

    @abstractmethod
    def send_time_stamped_message(self, a_message: str) -> bool:
        # Requires a json string of the format: {"ts": time_in_milliseconds, "values": {'T Zone 1': 77, 'T Zone 2': 75}}
        # Time is linux timestamp, e.g. round(time.time() * 1000) . values are one or more name/value pairs.
        # Works with ThingsBoard and SQLite
        pass