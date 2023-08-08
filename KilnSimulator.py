import logging
import time

log = logging.getLogger(__name__)
# log.level = logging.INFO

# One instance to allow for heat transfer between zones. (Could use a singleton)
class ZoneTemps:
    def __init__(self):
        self.old_temps = {}
        self.new_temps = {}

    def add_new_temp(self, zone_name, temp):
        self.new_temps.update({zone_name: temp})

    def set_old_temps_to_new(self):
        self.old_temps = self.new_temps

    def get_temps(self):
        return self.old_temps

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
        self.radiative_coupling = 0.2e-8  # w/K^4 radiation between adjacent zones
        self.t_elements = 27

    def update_sim(self, heat_factor: float, zone_temps: dict, zone_name: str):
        now = time.time()
        delta_time = (now - self.latest_time) * self.sim_speedup
        self.latest_temperature = self.find_temperature(delta_time, heat_factor, zone_temps, zone_name)
        self.latest_time = now

    def get_latest_temperature(self) -> float:
        return self.latest_temperature

    def find_temperature(self, delta_time, heat_factor, zone_old_temps: dict, zone_name: str):
        # Two lumped heat capacities kiln model. This assumes two temperatures, t-elements and t_kiln
        # Heat is lost by conduction and convection to the environement.Heat loss is proportional to T - T environement.
        # This is split between the usually higher t_elements and t_kiln. Heat is transferred from the elements (plus
        # surrounding bricks) to the kiln by radiation. Radiation works much better at higher temperatures
        # (temperature to the 4th power), which is why things even out at higher temperatures. Finally, the
        # thermocouples will be at some temperature between t-elements and t_kiln. This is not inculded here as
        # leaving it out gives a longer time delay, which is worse for control design.

        # Radiant heat transfer coupling between zones added 08/07/2023

        pf = self.power * heat_factor
        log.debug('Power factor watts: ' + str(pf))
        loss = self.heat_loss * (self.t_elements - self.t_environment)
        log.debug('Heat loss watts: ' + str(loss))
        power = pf - loss
        power_to_zone = ((self.t_elements + 273)**4 - (self.latest_temperature + 273) **4) * self.radiation\
                        - self.heat_loss * (self.latest_temperature - self.t_environment) * 3
        elements_rate = (power - power_to_zone) * self.kiln_thermal_mass_inverted * 50 # It's a guess for the elements +
        power_to_zone = power_to_zone + self.radiative_coupling_gain(zone_old_temps, zone_name)
        self.t_elements = self.t_elements + elements_rate * delta_time # TODO this is high with power off to this zone
        log.info('Elements temperature: ' + str(self.t_elements))
        # Radiant transfer to kiln. Elements thermal mass should include nearby stuff.

        log.info('Zone power: ' + str(power_to_zone))
        rate = power_to_zone * self.kiln_thermal_mass_inverted
        temperature = self.latest_temperature + rate * delta_time
        log.info('Temp: ' + str(temperature))
        return temperature

    def radiative_coupling_gain(self, zone_old_temps: dict, zone_name: str):
        coupling_power = 0
        keys = zone_old_temps.keys()
        if len(keys) > 1:
            temps = list(zone_old_temps.values())
            index = -1
            for i, key in enumerate(keys):
                if key == zone_name:
                    index = i
            log.info(temps)
            log.info(index)
            if index == 0:
                coupling_power = self.coupling(temps[index + 1], temps[index])

            if index == 1:
                coupling_power = self.coupling(temps[index - 1], temps[index])

        log.info('Coupling: ' + str(coupling_power))

        return coupling_power

    def coupling(self, t1: float, t2: float) -> float:
        return ((t1 + 273) **4 - (t2 + 273) **4) * self.radiative_coupling


#  This is for testing
if __name__ == '__main__':
    sim = KilnSimulator(100)

    while True:
        sim.update_sim(0.6)
        temp = sim.get_latest_temperature()
        print(temp)
        time.sleep(0.7)
