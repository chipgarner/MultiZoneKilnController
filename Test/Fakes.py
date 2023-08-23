import MessageBroker

class TestBroker(MessageBroker.MessageBroker):
    def __init__(self):
        self.u_names_called = False
        self.UI_message = None
        MessageBroker.MessageBroker.__init__(self)

    def update_names(self, names: list):
        self.u_names_called = True

    def update_UI_status(self, UI_message: dict):
        self.UI_message = UI_message

    def new_profile_all(self, profile):
        pass

    def update_profile_all(self, profile):
        pass

class FakeBroker(MessageBroker.MessageBroker):
    def __init__(self):
        self.update_UI_calls = 0
        self.update_calls = 0
        self.update_names_calls = 0
        self.UI_message = None
        MessageBroker.MessageBroker.__init__(self)

    def update_UI_status(self, state: dict):
        self.update_UI_calls += 1
        self.UI_message = state

    def update_zones(self, zones: list):
        self.update_calls += 1
    def update_names(self, zones: list):
        self.update_names_calls += 1

    def update_tc_data(self, tc_data: list):
        pass

    def update_profile_all(self, profile):
        pass
    def new_profile_all(self, profile):
        pass

