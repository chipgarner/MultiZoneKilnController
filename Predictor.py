def predict_power_change(predict_time: int, start_temp: float, power_change: float,
                         power_change_start: float) -> float:
    p = 0

    # These are chosen such that e.g. 1/p_slope = 180 seconds at start_temp = 100C, 20 seconds at 1000C
    # The response to power changes is much faster at high temperatures, this is a linear approximation.
    # The power getting to the ware ramps up after the electric power is increased.
    a = 4.9383e-5
    b = 6.1728e-4
    if predict_time > power_change_start:
        p_slope = start_temp * a + b
        ramp_time = 1 / p_slope
        if predict_time <= ramp_time + power_change_start:  # This is within the power ramp up time.
            p = power_change * p_slope * (predict_time - power_change_start)
        else:
            p = power_change
    return p


def predict_temperature(predict_time: int, predict_start: int, start_temp: float, power: float, power_change: float,
                        power_change_start: float) -> float:
    mc = 20 * 850
    hA = .37 * 3.5
    p = power + predict_power_change(predict_time, start_temp, power_change, power_change_start)
    p = p * 3000
    return (predict_time - predict_start) * (p - hA *(start_temp - 27)) / mc + start_temp
