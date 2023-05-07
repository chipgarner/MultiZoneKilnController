from Controller import ControllerState

def test_firing_on():
    c_state = ControllerState()

    assert not c_state.firing_on()

    # Can't start firing if no profile has been chosen.
    state = c_state.get_state()
    assert not state['firing']
    assert state['profile_chosen'] == False

    assert c_state.choosing_profile()
    state = c_state.get_state()
    assert state['profile_chosen']

    assert c_state.firing_on()
    state = c_state.get_state()
    assert state['firing']

def test_cant_choose_profile_while_firing():
    c_state = ControllerState()
    assert c_state.choosing_profile()
    c_state.firing_on()

    assert not c_state.choosing_profile()
    state = c_state.get_state()
    assert state['profile_chosen']

    assert c_state.firing_off() # Can shut firing off any time
    state = c_state.get_state()
    assert not state['firing']

def test_cant_switch_manual_unless_firing():
    c_state = ControllerState()
    assert c_state.choosing_profile()

    assert not c_state.manual_on()
    state = c_state.get_state()
    assert not state['manual']

    assert c_state.firing_on()

    assert c_state.manual_on()
    state = c_state.get_state()
    assert state['manual']


