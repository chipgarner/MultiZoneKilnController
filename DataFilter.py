import logging
import statistics
import sys

from _decimal import Decimal
from fractions import Fraction
from typing import Dict, Any

log = logging.getLogger(__name__)

def median(t_t_h: list) -> dict[str, float] | None:
    y_list = []
    for time_temp in t_t_h:
        y_list.append(time_temp['temperature'])
    if len(y_list) < 1:
        return None

    median = statistics.median(y_list)
    try:
        pstdev = statistics.pstdev(y_list)
    except OverflowError as ex:
        pstdev = 0
        log.error(str(ex))

    mean = statistics.mean(y_list)

    return {'mean': mean, 'median': median, 'p_stand_dev': pstdev}


def linear(t_t_h: list) -> dict or None:
    # Linear regression added in Python 3.10.x, not on Pi as of April 2023
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
