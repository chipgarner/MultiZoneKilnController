class KilnSimulator:
    def __init__(self):
        self.temps = []

    def update_sim(self):
        self.temps.append(33)

    def get_latest_temperature(self) -> float:
        return self.temps[-1]

