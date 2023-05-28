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
    assert onoff == [True, False, False, True, False, False, True, False, False, True, False, False, True, False, True,
                     False, True, False, True, False]

    ssr.set_heat(0.51)
    assert ssr.heat_factor == 0.5
    onoff = ssr.set_cycles_list(0.5)
    assert onoff == [True, False, True, False, True, False, True, False, True, False, True, False, True, False, True,
                     False, True, False, True, False]

    ssr.set_heat(0.53)
    assert ssr.heat_factor == 0.55

def test_even():
    ssr = SSR(None)

    for i in range(1, 20):
        onoff = []
        hf = i/20
        cycles_on, cycles_off = ssr.cycles_on_off(hf)
        skips, mod = divmod(cycles_off, cycles_on)
        if mod > 0:  # Need to skip some number (n1) of skips and some number (n2) of skips + 1
            # n1 + n2 = ons: n1*skips + n2(skips + 1) = offs. Solve for n1 and n2
            n2 = cycles_off - skips * cycles_on
            n1 = cycles_on - n2

            print('hf: ' + str(hf) + ' Ons: ' + str(cycles_on) + ' Offs: ' + str(cycles_off))
            print('n1: ' + str(n1) + ' n2: ' + str(n2) + ' : ' + str(n1 / n2))
        else:
            n1 = cycles_on
            n2 = 0

        if n2 > 0: num_shorts = round(n1 /n2)
        else: num_shorts = 0

        if num_shorts >= 1:
            index = 0
            while index < ssr.resolution:
                # Longs
                onoff.append(True)
                for i in range(skips + 1):
                    onoff.append(False)
                #shorts, there may be more of these than longs
                for _ in range(num_shorts):
                    onoff.append(True)
                    for i in range(skips):
                        onoff.append(False)

                index = len(onoff) - 1
        else:
            index = 0
            while index < ssr.resolution:
                onoff.append(True)
                for i in range(skips):
                    onoff.append(False)

                index = len(onoff)

        onoff = onoff[:20]
        print(onoff)

