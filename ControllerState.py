from dataclasses import dataclass, asdict


@dataclass
class UI_status:
    label: str = 'IDLE'
    StartStop: str = 'Start'
    StartStopDisabled: bool = True
    Manual: bool = False
    ManualDisabled: bool = True
    ProfileName: str = 'None'
    ProfileSelectDisabled: bool = False


@dataclass
class Controller_State:
    firing: bool = False
    profile_chosen: bool = False
    manual: bool = False


# This class limits the possible states to the ones we want. For example, don't start the firing without
# first choosing a profile. All the logic is in one place, instead of repeating logic on the front end.
# Updates the UI on any stat changes
class ControllerState:
    def __init__(self, update_ui):
        self.__controller_state = Controller_State()
        self.update_ui = update_ui

        # This avoids repeating logic on the front end.
        self.__UI_status = UI_status()

        self.update_ui(self.get_UI_status_dict())

    def get_UI_status_dict(self):
        return asdict(self.__UI_status)

    def get_state(self):
        return self.__controller_state

    def firing_on(self) -> bool:
        worked = False
        if self.__controller_state.profile_chosen:
            self.__controller_state.firing = True

            self.__UI_status.label = 'FIRING'
            self.__UI_status.StartStop = 'Stop'
            self.__UI_status.StartStopDisabled = False
            self.__UI_status.Manual = False
            self.__UI_status.ManualDisabled = False
            self.__UI_status.ProfileSelectDisabled = True

            worked = True

            self.update_ui(self.get_UI_status_dict())
        return worked

    def firing_finished(self):
        self.firing_off()
        self.__UI_status.label = 'Done'
        self.__UI_status.StartStopDisabled = True
        self.__UI_status.ProfileSelectDisabled = True

        self.update_ui(self.get_UI_status_dict())

    def firing_off(self) -> bool:
        self.__controller_state.firing = False

        self.__UI_status.label = 'IDLE'
        self.__UI_status.StartStop = 'Start'
        self.__UI_status.StartStopDisabled = False
        self.__UI_status.Manual = False
        self.__UI_status.ManualDisabled = True
        self.__UI_status.ProfileSelectDisabled = False

        self.update_ui(self.get_UI_status_dict())

        return True

    def choosing_profile(self, name) -> bool:
        worked = False
        if not (self.__controller_state.firing or self.__controller_state.manual):
            self.__controller_state.profile_chosen = True
            self.__UI_status.ProfileName = name

            self.__UI_status.label = 'IDLE'
            self.__UI_status.StartStop = 'Start'
            self.__UI_status.StartStopDisabled = False
            self.__UI_status.Manual = False
            self.__UI_status.ManualDisabled = True
            self.__UI_status.ProfileSelectDisabled = False

            worked = True

            self.update_ui(self.get_UI_status_dict())
        return worked

    def manual_on(self) -> bool:
        worked = False
        if self.__controller_state.firing:
            self.__controller_state.manual = True

            self.__UI_status.label = 'MANUAL'
            self.__UI_status.StartStop = 'Stop'
            self.__UI_status.StartStopDisabled = False
            self.__UI_status.Manual = True
            self.__UI_status.ManualDisabled = False
            self.__UI_status.ProfileSelectDisabled = True

            worked = True

            self.update_ui(self.get_UI_status_dict())
        return worked

    def manual_off(self) -> bool:
        self.__controller_state.manual = False

        self.__UI_status.label = 'FIRING'
        self.__UI_status.StartStop = 'Stop'
        self.__UI_status.StartStopDisabled = False
        self.__UI_status.Manual = False
        self.__UI_status.ManualDisabled = False
        self.__UI_status.ProfileSelectDisabled = True

        self.update_ui(self.get_UI_status_dict())

        return True
