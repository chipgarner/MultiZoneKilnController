from Profile import Profile
from KilnZones import KilnZones


class Controller:
    def __init__(self, file: str):
        self.profile = Profile(file)
        # self.temp_sensors = KilnZones()
        pass
