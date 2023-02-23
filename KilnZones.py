from abc import ABC, abstractmethod
# Supports multiple sensors for multiple zone kilns.
# Sensors are on one thread. You can't call sensors from separate threads if they share the SPI/


class KilnZones(ABC):
    def __init__(self):

        pass

    @abstractmethod
    def get_time_temps(self):
        pass