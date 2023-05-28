from KilnElectronics import SSR
import pytest


def test_cycles_on_off():
    ssr = SSR(1)

    cycles_on, cycles_off = ssr.cycles_on_off(0.5)

    hf = cycles_on / (cycles_on + cycles_off)

    assert hf == 0.5
    assert cycles_on == 10
    assert cycles_off == 10

    cycles_on, cycles_off = ssr.cycles_on_off(0.05)
    hf = cycles_on / (cycles_on + cycles_off)
    assert hf == 0.05
    assert cycles_on == 1
    assert cycles_off == 19

    cycles_on, cycles_off = ssr.cycles_on_off(0.03)
    hf = cycles_on / (cycles_on + cycles_off)
    assert hf == pytest.approx(0.05)
    assert cycles_on == 1
    assert cycles_off == 19

    for i in range(1, 100):
        heat_factor = i / 100
        cycles_on, cycles_off = ssr.cycles_on_off(heat_factor)
        ssr.set_heat(heat_factor)
        hf = ssr.get_heat_factor()
        error = heat_factor - hf
        print(str(heat_factor) + '  hf: ' + str(hf))
        print('Error: ' + str(error))
        print('On: ' + str(cycles_on) + ' Off: ' + str(cycles_off))
        print(ssr.on_off)
        assert len(ssr.on_off) == ssr.resolution
        assert abs(error) < 0.0201

def test_full_on_full_off():
    ssr = SSR(1)

    ssr.set_heat(0)
    hf = ssr.get_heat_factor()

    assert hf == 0
    assert len(ssr.on_off) == 20

    ssr.set_heat(1)
    hf = ssr.get_heat_factor()

    assert hf == 1
    assert len(ssr.on_off) == 20

def test_more():
    ssr = SSR(1)

    ssr.set_heat(0.13)
    hf = ssr.get_heat_factor()

    assert hf == 0.15
    assert len(ssr.on_off) == 20

    ssr.set_heat(0.63)
    hf = ssr.get_heat_factor()

    assert hf == 0.65
    assert len(ssr.on_off) == 20

def test_set_cycles_list():
    ssr = SSR(None)

    onoff = ssr.set_cycles_list(0.3)

    ons = [x for x in onoff if x]
    assert len(ons) == 6

    ssr.set_heat(0.3)
    assert ssr.heat_factor == 0.3
    onoff = ssr.set_cycles_list(0.2)
    assert onoff == [True, False, False, False, False, True, False, False, False, False, True, False, False, False,
                     False, True, False, False, False, False]

    ssr.set_heat(0.38)
    assert ssr.heat_factor == 0.4

    ssr.set_heat(0.23)
    assert ssr.heat_factor == 0.25
    onoff = ssr.set_cycles_list(0.23)
    assert onoff == [True, False, False, False, True, False, False, False, True, False, False, False, True, False,
                     False, False, True, False, False, False]

    onoff = ssr.set_cycles_list(0.42)
    assert onoff == [True, False, False, True, False, True, False, False, True, False, True, False, False, True, False, True, False, False, True, False]

    ssr.set_heat(0.51)
    assert ssr.heat_factor == 0.5
    onoff = ssr.set_cycles_list(0.5)
    assert onoff == [True, False, True, False, True, False, True, False, True, False, True, False, True, False, True,
                     False, True, False, True, False]

    ssr.set_heat(0.53)
    assert ssr.heat_factor == 0.55
