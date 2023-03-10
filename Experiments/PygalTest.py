import pygal


date_chart = pygal.DateTimeLine(x_label_rotation=5,
                                x_value_formatter=lambda d: d.strftime('%H:%M:%S.%f')[:-3])

date_chart.add("Values", [
 (1677999459927/1000, 300),
 (1677999461993/1000, 412),
 (1677999495044/1000, 823),
 (1677999515094/1000, 672)])

# date_chart.render_in_browser()
date_chart.render_to_file('date_chart.svg')

date_chart.add("Values", [
 (1677999515094/1000, 300),
 (1677999516094/1000, 412),
 (1677999517094/1000, 823),
 (1677999518094/1000, 672)])

# date_chart.render_in_browser()
date_chart.render_to_file('date_chart.svg')

