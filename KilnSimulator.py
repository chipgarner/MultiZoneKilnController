import logging
import time
import random

log = logging.getLogger(__name__)
log.level = logging.INFO

# Each zone has its own simulator.


class KilnSimulator:
    def __init__(self):
        self.latest_temperature = 27 # Temperatures are in degrees Centigrade
        self.latest_time = time.time()
        self.sim_speedup = 10
        log.warning('Running simulator. In case you thought otherwise.')

        self.t_environment = 27 # Degrees C
        self.power = 6000 # Kiln power watts
        self.heat_loss = 15 # Conductive plus heat lost to the environment, watts/degrees C
        self.kiln_thermal_mass_inverted = 3.9e-5 # c/ws, compute heating rate from power
        self.radiation = 1.03e-8 # w/K^4 radiation from elements to kiln
        self.t_elements = 27

    def update_sim(self, heat_factor: float):
        now = time.time()
        delta_time = (now - self.latest_time) * self.sim_speedup
        self.latest_temperature = self.find_temperature(delta_time, heat_factor)
        self.latest_time = now

    def get_latest_temperature(self) -> float:
        return self.latest_temperature

    def find_temperature(self, delta_time, heat_factor):
        # Two lumped heat capacities kiln model. This assumes two temperatures, t-elements and t_kiln
        # Heat is lost by conduction and convection to the environement.Heat loss is proportional to T - T environement.
        # This is split between the usually higher t_elements and t_kiln. Heat is transferred from the elements (plus
        # surronding bricks) to the kiln by radiation. Radiation works much better at higher temperatures
        # (temperature to the 4th power), which is why things even out at higher temperatures. Finally, the
        # thermocouples will be at some temperature between t-elements and t_kiln. This is not inculded here as it
        # gives a longer time delay, which is worse for control design.

        power = self.power * heat_factor - self.heat_loss * (self.t_elements - self.t_environment) / 4
        power_to_kiln = ((self.t_elements + 273)**4 - (self.latest_temperature + 273) **4) * self.radiation\
                        - self.heat_loss * (self.latest_temperature - self.t_environment) * 3 / 4
        elements_rate = (power - power_to_kiln) * self.kiln_thermal_mass_inverted * 50 # It's a guess for the elements +
        self.t_elements = self.t_elements + elements_rate * delta_time
        log.debug('Elements temperature: ' + str(self.t_elements))
        # Radiant transfer to kiln. Elements should include nearby stuff.

        log.debug(str(power_to_kiln))
        rate = power_to_kiln * self.kiln_thermal_mass_inverted
        temperature = self.latest_temperature + rate * delta_time
        return temperature


class SimZone:
    def __init__(self):
        # self.name = name
        self.heat_factor = 0
        self.times_temps_heat = []
        self.kiln_sim = KilnSimulator()
        self.sim_speedup = self.kiln_sim.sim_speedup
        self.start = time.time()
        self.latest_temp = 0
        k=self.kiln_sim.power

    # def get_times_temps_heat(self) -> list:
    #     t_t_h = self.times_temps_heat
    #     self.times_temps_heat = []
    #     return t_t_h
    #
    # def set_heat(self, heat_factor: float):
    #     if heat_factor > 1.0 or heat_factor < 0:
    #         log.error('Heat factor must be from zero through one. heat_factor: ' + str(heat_factor))
    #         raise ValueError
    #     self.heat_factor = heat_factor
    #
    # def update_time_temperature(self) -> dict:
    #     self.update_heating()
    #     temp, error = self.get_temperature()
    #     time_sim = (time.time() - self.start) * self.sim_speedup + self.start
    #     time_ms = round(time_sim * 1000)  # Thingsboard and SQLite require timestamps in milliseconds
    #     thermocouple_data = {'time_ms': time_ms, 'temperature': temp, 'heat_factor': self.heat_factor, 'error': error}
    #     self.times_temps_heat.append(thermocouple_data)
    #
    #     time.sleep(1 / self.sim_speedup) # Real sensors take time to read
    #     return thermocouple_data

    def update_heating(self):
        self.kiln_sim.update_sim(self.heat_factor)

    def get_temperature(self) -> tuple: # From the thermocouple board
        error = 0
        temperature = self.kiln_sim.get_latest_temperature()
        temperature += random.gauss(mu=0, sigma=0.65)

        # Record the error and use the latest good temperature
        if random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 1:
            error = 1
            temperature = self.latest_temp

        self.latest_temp = temperature
        time_sim = (time.time() - self.start) * self.sim_speedup + self.start
        time_ms = round(time_sim * 1000)  # Thingsboard and SQLite require timestamps in milliseconds

        time.sleep(0.7 / self.sim_speedup)  # Real sensors take time to read
        return time_ms, temperature, error


#  This is for testing
if __name__ == '__main__':
    sim = KilnSimulator()
    sim.sim_speedup = 100

    while True:
        sim.update_sim(0.6)
        temp = sim.get_latest_temperature()
        print(temp)
        time.sleep(0.7)
