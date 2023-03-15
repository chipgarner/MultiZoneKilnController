import statistics
import sys


def median(t_t_h: list) -> dict:
    y_list = []
    for time_temp in t_t_h:
        y_list.append(time_temp['temperature'])
    if len(y_list) < 1:
        return None

    median = statistics.median(y_list)
    pstdev = statistics.pstdev(y_list)

    return {'median': median, 'p_stand_dev': pstdev}


def linear(t_t_h: list) -> dict:
    if len(t_t_h) > 1 & sys.version_info<(3,10,0):
        x_list = []
        y_list = []
        for time_temp in t_t_h:
            x_list.append(time_temp['time_ms'])
            y_list.append(time_temp['temperature'])

        result = statistics.linear_regression(x_list, y_list)
        return {'slope': result.slope, 'intercept': result.intercept}
    else:
        return None

