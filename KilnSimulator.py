import logging
import time

log = logging.getLogger(__name__)
# log.level = logging.INFO

# Each zone has its own simulator.

class KilnSimulator:
    def __init__(self, speed_up_factor: int):
        self.latest_temperature = 27 # Temperatures are in degrees Centigrade
        self.latest_time = time.time()
        self.sim_speedup = speed_up_factor
        log.warning('Running simulator. In case you thought otherwise.')

        self.t_environment = 27 # Degrees C
        self.power = 3000 # Kiln power watts
        self.heat_loss = 1.5 # Conductive plus heat lost to the environment, watts/degrees C
        self.kiln_thermal_mass_inverted = 2e-5 # c/ws, compute heating rate from power
        self.radiation = 0.5e-8 # w/K^4 radiation from elements to kiln
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
        # surrounding bricks) to the kiln by radiation. Radiation works much better at higher temperatures
        # (temperature to the 4th power), which is why things even out at higher temperatures. Finally, the
        # thermocouples will be at some temperature between t-elements and t_kiln. This is not inculded here as
        # leaving it out gives a longer time delay, which is worse for control design.

        pf = self.power * heat_factor
        log.debug('Power factor watts: ' + str(pf))
        loss = self.heat_loss * (self.t_elements - self.t_environment)
        log.debug('eat loss watts: ' + str(loss))
        power = pf - loss
        power_to_kiln = ((self.t_elements + 273)**4 - (self.latest_temperature + 273) **4) * self.radiation\
                        - self.heat_loss * (self.latest_temperature - self.t_environment) * 3
        elements_rate = (power - power_to_kiln) * self.kiln_thermal_mass_inverted * 50 # It's a guess for the elements +
        self.t_elements = self.t_elements + elements_rate * delta_time
        log.debug('Elements temperature: ' + str(self.t_elements))
        # Radiant transfer to kiln. Elements thermal mass should include nearby stuff.

        log.debug('Zone power: ' + str(power_to_kiln))
        rate = power_to_kiln * self.kiln_thermal_mass_inverted
        temperature = self.latest_temperature + rate * delta_time
        return temperature


#  This is for testing
if __name__ == '__main__':
    sim = KilnSimulator(100)

    while True:
        sim.update_sim(0.6)
        temp = sim.get_latest_temperature()
        print(temp)
        time.sleep(0.7)
