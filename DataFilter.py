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
    mean = statistics.mean(y_list)

    return {'mean': mean, 'median': median, 'p_stand_dev': pstdev}


def linear(t_t_h: list) -> dict:
    # Linear regression added in 3.10.x
    vers = sys.version_info
    major = vers[0]
    minor = vers[1]
    vers = major + minor / 100
    if len(t_t_h) > 1 and vers >= 3.1:
        x_list = []
        y_list = []
        for time_temp in t_t_h:
            x_list.append(time_temp['time_ms'])
            y_list.append(time_temp['temperature'])

        result = statistics.linear_regression(x_list, y_list)
        return {'slope': result.slope, 'intercept': result.intercept}
    else:
        return None

