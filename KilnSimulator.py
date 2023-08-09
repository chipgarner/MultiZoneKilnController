import logging
import time

log = logging.getLogger(__name__)
log.level = logging.DEBUG

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
    def __init__(self, zone_name: str, speed_up_factor: int, zone_temps: ZoneTemps):
        self.latest_temperature = 27 # Temperatures are in degrees Centigrade
        self.latest_time = time.time()
        self.sim_speedup = speed_up_factor
        log.warning('Running simulator. In case you thought otherwise.')

        zone_temps.add_new_temp(zone_name, 27)
        self.zone_temps = zone_temps
        self.zone_name = zone_name

        self.t_environment = 27 # Degrees C
        self.t_elements = 27
        self.power = 3000 # Kiln power watts for this zone
        self.steve_b = 5.669e-8 # Stephan-Boltzmann constant w/m**2/K**4
        self.area_el = 0.157 # m**2, Effective area of elements in square meters. Estimate used for conducti0n and radiation.
        self.area_load = 0.325 # m**2, Zone heat loss area not incuding elements area, e.g. Zone one top and side wall.
        self.area_adjacent_zones = 0.168 # m**2, Area
        self.heat_loss = 5.0 # Conductive/convective heat loss resistance through kiln walls, watts/m**2/degrees C
        self.heat_capacity = 850 # J/kg/degrees C, ceramic materials are similar.
        self.elements_mass = 1 # kg, include part of the nearby bricks. (This is a guess.)
        self.load_mass = 20 # kg, the ware and kiln shelves

    def update_sim(self, heat_factor: float):
        now = time.time()
        delta_time = (now - self.latest_time) * self.sim_speedup
        self.latest_temperature = self.find_temperature(delta_time, heat_factor)
        self.latest_time = now

    def get_latest_temperature(self) -> float:
        return self.latest_temperature

    def find_temperature(self, delta_time, heat_factor):
        # Two lumped heat capacities kiln model. This assumes two temperatures, t-elements and t_kiln
        # Heat is lost by conduction and convection to the environement.
        # This assumes convection in the kiln is not important, it becomes much less important at higher
        # tempertures.

        # Radiant heat transfer coupling between zones added 08/07/2023

        power_in = self.power * heat_factor
        log.debug('Power factor watts: ' + str(power_in))
        # Heat lost from the elements direclty through the kiln walls
        loss_elements = self.area_el * self.heat_loss * (self.t_elements - self.t_environment)
        log.debug('Elements loss watts: ' + str(loss_elements))
        # Assumes all the power (heat) to the load (ware plus shelves) is via thermal radiation
        power_to_load = self.steve_b * self.area_el * ((self.t_elements + 273)**4 - (self.latest_temperature + 273) **4)
        log.debug('Load input power watts: ' + str(power_to_load))
        # This is from the differential equation for lumped heat capacity: q = -Cm(dT/dt). q here is the power stored in
        # the elements.
        delta_t_elements = (delta_time / (self.elements_mass * self.heat_capacity)) * \
                           (power_in - loss_elements - power_to_load)
        self.t_elements = self.t_elements + delta_t_elements
        log.info('Elements temperature: ' + str(self.t_elements))

        loss_load = self.heat_loss * self.area_load * (self.latest_temperature - self.t_environment)
        coupling_gain = self.radiative_coupling_gain(self.zone_temps.get_temps(), self.zone_name)
        log.debug('Coupling gain: ' + str(coupling_gain))
        delta_t_load =  (delta_time / (self.load_mass * self.heat_capacity)) * \
                        (power_to_load - loss_load + coupling_gain)
        temperature = self.latest_temperature + delta_t_load

        # power_to_zone = ((self.t_elements + 273)**4 - (self.latest_temperature + 273) **4) * self.radiation\
        #                 - self.heat_loss * (self.latest_temperature - self.t_environment) * 3
        # elements_rate = (power - power_to_zone) * self.kiln_thermal_mass_inverted * 50 # It's a guess for the elements +
        # power_to_zone = power_to_zone + self.radiative_coupling_gain(self.zone_temps.get_temps(), self.zone_name)
        # self.t_elements = self.t_elements + elements_rate * delta_time # TODO this is high with power off to this zone
        # log.info('Elements temperature: ' + str(self.t_elements))
        # # Radiant transfer to kiln. Elements thermal mass should include nearby stuff.
        #
        # log.info('Zone power: ' + str(power_to_zone))
        # rate = power_to_zone * self.kiln_thermal_mass_inverted
        # temperature = self.latest_temperature + rate * delta_time

        log.info('Temp: ' + str(temperature))
        self.update_zone_temps(temperature)
        return temperature

# Heat transfer bertween adjacent Zones
    def radiative_coupling_gain(self, zone_old_temps: dict, zone_name: str):
        coupling_power = 0
        keys = zone_old_temps.keys()
        num_zones = len(keys)
        if num_zones > 1:
            temps = list(zone_old_temps.values())
            index = -1
            for i, key in enumerate(keys):
                if key == zone_name:
                    index = i
            log.info(temps)
            log.info(index)
            if index == 0:
                coupling_power = self.coupling(temps[index + 1], temps[index])

            elif index == 1:
                coupling_power = self.coupling(temps[index - 1], temps[index])

                if num_zones > 2:
                    coupling_power = coupling_power + self.coupling(temps[index + 1], temps[index])

            elif index == 2:
                coupling_power = self.coupling(temps[index - 1], temps[index])

                if num_zones > 3:
                    coupling_power = coupling_power + self.coupling(temps[index + 1], temps[index])

            elif index == 3: # Four zones max
                coupling_power = self.coupling(temps[index - 1], temps[index])

        log.info('Coupling: ' + str(coupling_power))

        return coupling_power

    def coupling(self, t1: float, t2: float) -> float:
        return self.steve_b * self.area_adjacent_zones * ((t1 + 273) **4 - (t2 + 273) **4)

    # This is for radiative coupling, the heat transfer between zones
    def update_zone_temps(self, temperature):
        self.zone_temps.add_new_temp(self.zone_name, temperature)
        keys = self.zone_temps.new_temps.keys()
        if self.zone_name == list(keys)[len(keys) - 1]: # It's the last (bottom) zone
            self.zone_temps.set_old_temps_to_new()


#  This is for testing
if __name__ == '__main__':
    sim = KilnSimulator(100)

    while True:
        sim.update_sim(0.6)
        temp = sim.get_latest_temperature()
        print(temp)
        time.sleep(0.7)
