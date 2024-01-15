import pytest

import Predictor


def test_power_change():
    predict_time = 1
    start_temp = 27
    power_change = 0.1
    power_change_start = 2  # start is after predict_time, return zero
    power = Predictor.predict_power_change(predict_time,
                                           start_temp,
                                           power_change,
                                           power_change_start)
    assert power == 0

    predict_time = 515 #  After the change in power is complete, return power_change
    power = Predictor.predict_power_change(predict_time,
                                           start_temp,
                                           power_change,
                                           power_change_start)
    assert power == 0.1

    predict_time = 21.999 # Near the end of the change time, predict input power change
    start_temp = 1000
    power = Predictor.predict_power_change(predict_time,
                                           start_temp,
                                           power_change,
                                           power_change_start)
    assert power == pytest.approx(0.09999556)


def test_predict_temperature():
    predict_time = 200
    predict_start = 0
    start_temp = 27
    power_change = 0.1
    power = 0.5
    power_change_start = 2
    temperature = Predictor.predict_temperature(predict_time,
                                                predict_start,
                                                start_temp,
                                                power,
                                                power_change,
                                                power_change_start)

    assert temperature == pytest.approx(65.0204)
