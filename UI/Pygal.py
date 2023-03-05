import pygal

class Pygal:
    def __init__(self):
        self.time_chart = pygal.DateTimeLine(x_label_rotation=5,
                                x_value_formatter=lambda d: d.strftime('%H:%M:%S.%f')[:-3])

    def plot(self,  times_temps_heats_for_zones: dict):
        t_t_h = times_temps_heats_for_zones['Zone 1']
        times_temps = []
        for time_temp in t_t_h:
            times_temps.append((time_temp['time_ms'] / 1000, time_temp['temperature']))
        self.time_chart.add("Values", times_temps)

        # date_chart.render_in_browser()
        self.time_chart.render_to_file('time_chart.svg')


#  This is for testing
if __name__ == '__main__':
    pg = Pygal()

    times_temps_heats_for_zones = {'Zone 1': [{'time_ms': 1678012236849, 'temperature': 55.386877503916445, 'heat_factor': 0.5}, {'time_ms': 1678012237852, 'temperature': 54.29107309783632, 'heat_factor': 0.5}, {'time_ms': 1678012238855, 'temperature': 54.23951844825202, 'heat_factor': 0.5}, {'time_ms': 1678012239858, 'temperature': 53.70861045126481, 'heat_factor': 0.5}, {'time_ms': 1678012240866, 'temperature': 54.17719685387979, 'heat_factor': 0.5}, {'time_ms': 1678012241873, 'temperature': 54.3715833444422, 'heat_factor': 0.5}, {'time_ms': 1678012242876, 'temperature': 54.622752028897914, 'heat_factor': 0.5}, {'time_ms': 1678012243879, 'temperature': 55.70600673368867, 'heat_factor': 0.5}, {'time_ms': 1678012244882, 'temperature': 55.11415498744986, 'heat_factor': 0.5}, {'time_ms': 1678012245885, 'temperature': 54.82106373661255, 'heat_factor': 0.5}, {'time_ms': 1678012246892, 'temperature': 54.061994007520326, 'heat_factor': 0.5}]}

    pg.plot(times_temps_heats_for_zones)