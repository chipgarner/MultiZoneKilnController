import time
import logging
from Profile import Profile
from KilnZones import KilnZones, SimZone


log_level = logging.DEBUG
log_format = '%(asctime)s %(levelname)s %(name)s: %(message)s'

logging.basicConfig(level=log_level, format=log_format)
log = logging.getLogger("Controller")


class Controller:
    def __init__(self, file: str, notifier):
        self.notifier = notifier
        self.profile = Profile(file)
        zone = SimZone()
        self.loop_delay = 10

        if zone.sim_speedup is not None:
            self.loop_delay = self.loop_delay / zone.sim_speedup
            log.info('Sim speed up factor is ' + str(zone.sim_speedup))

        self.zones = [zone]
        self.kiln_zones = KilnZones(self.zones)

        log.info('Controller initialized, all initialization complete.')

    def control_loop(self):
        self.__zero_heat_zones()
        while True:
            t_t_h = self.kiln_zones.get_times_temps_heat_for_zones()
            heats = self.__update_zones_heat(t_t_h)
            self.kiln_zones.set_heat_for_zones(heats)
            self.__notify(t_t_h)
            time.sleep(self.loop_delay)

    def __zero_heat_zones(self):
        heats = []
        for i in range(len(self.zones)):
            heats.append(0)
        self.kiln_zones.set_heat_for_zones(heats)

    def __update_zones_heat(self, t_t_h: list) -> list:
        latest_t_t_h = t_t_h[-1]
        temp = latest_t_t_h[0]['temperature']
        heat = 0.5
        if temp > 500:
            heat = 1.0
        heats = []
        for i in range(len(self.zones)):
            heats.append(heat)

        return heats

    def __notify(self, t_t_h: list):
        self.notifier.update(t_t_h)
        # log.debug('t_t_h temp time length ' + str(len(t_t_h[0])))
        # log.debug(str(t_t_h))
        #
        # latest_t_t_h = t_t_h[-1]
        #
        # time_in_milliseconds = latest_t_t_h[0]['time_ms']
        #
        # temp = latest_t_t_h[0]['temperature']
        # message = {'T1 56': temp}
        # time_stamped_message = {"ts": time_in_milliseconds, "values": message}
        #
        # if not self.send_time_stamped_message(str(time_stamped_message)):
        #     # TODO handle this
        #     log.error('Sending failed.')


def send_message(message):
    log.info(message)
#  This is for testing
if __name__ == '__main__':
    controller = Controller("test-fast.json", send_message)
    controller.control_loop()
