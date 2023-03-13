import DataFilter
import testdata
import pytest

def test_y():
    filter = DataFilter.DataFilter()

    results = filter.regression(testdata.test_data)

def test_linear():
    filter = DataFilter.DataFilter()

    result = filter.linear(testdata.test_data)

    assert result['slope'] == pytest.approx(0.0, abs=1e-3)
    assert result['intercept'] == pytest.approx(-38919854.462626, abs=1e-3)
    assert result['R_sq'] == 0.016152537348421703

def test_linear_hotter():
    filter = DataFilter.DataFilter()

    result = filter.linear(testdata.test_data_hot)

    assert result['slope'] == pytest.approx(0.0, abs=1e-3)
    assert result['intercept'] == pytest.approx(-38919854.462626, abs=1e-3)
    assert result['R_sq'] == 0.016152537348421703