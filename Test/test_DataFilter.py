import DataFilter
import testdata
import pytest


def test_linear():
    filter = DataFilter

    result = filter.linear(testdata.test_data)

    assert result['slope'] == pytest.approx(0.0, abs=1e-3)
    assert result['intercept'] == pytest.approx(-38919854.462626, abs=1e-3)

def test_linear_hotter():
    filter = DataFilter

    result = filter.linear(testdata.test_data_hot)

    assert result['slope'] == pytest.approx(0.0, abs=1e-3)
    assert result['intercept'] == pytest.approx(41461847.65215, abs=1e-3)

def test_median():
    filter = DataFilter

    result = filter.median(testdata.test_data_hot)

    assert result['median'] == pytest.approx(1098.6489, abs=0.01)
    assert result['p_stand_dev'] == pytest.approx(0.61527517)
