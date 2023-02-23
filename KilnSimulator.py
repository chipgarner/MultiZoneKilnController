import logging

log = logging.getLogger(__name__)


class KilnSimulator:
    def __init__(self):
        self.temps = []
        self.sim_speedup = 1
        log.warning('Running simulator. In case you thought otherwise.')

    def update_sim(self):
        self.temps.append(33)

    def get_latest_temperature(self) -> float:
        return self.temps[-1]
