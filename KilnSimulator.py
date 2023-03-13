import logging
import time

log = logging.getLogger(__name__)

# Each zone has its own simulator.


class KilnSimulator:
    def __init__(self):
        self.latest_temperature = 27 # Temperatures are in degrees Centigrade
        self.latest_time = time.time()
        self.sim_speedup = 10
        log.warning('Running simulator. In case you thought otherwise.')

        self.t_environment = 27 # Degrees C
        self.power = 6000 # Kiln power watts
        self.heat_loss = 4.3 # Conductive plus heat lost to the environment, watts/degrees C
        self.kiln_thermal_mass = 3.9e-5 # c/ws, compute heating rate from power

    def update_sim(self, heat_factor: float):
        now = time.time()
        delta_time = (now - self.latest_time) * self.sim_speedup
        self.latest_temperature = self.find_temperature(delta_time, heat_factor)
        self.latest_time = now

    def get_latest_temperature(self) -> float:
        return self.latest_temperature

    def find_temperature(self, delta_time, heat_factor):
        power = self.power * heat_factor - self.heat_loss * (self.latest_temperature - self.t_environment)
        rate = power * self.kiln_thermal_mass
        temperature = self.latest_temperature + rate * delta_time
        return temperature


#  This is for testing
if __name__ == '__main__':
    sim = KilnSimulator()
    sim.sim_speedup = 100

    while True:
        sim.update_sim(0.6)
        temp = sim.get_latest_temperature()
        print(temp)
        time.sleep(1)
