import sqlite3


class DbInsert:
    def __init__(self):
        self.db = sqlite3.connect('Database/firing.db')

    def send_time_stamped_message(self, times_temps_heats_for_zones: dict):

        for time_temp_heat in times_temps_heats_for_zones['Zone 1']: # Only one zone for now
            time_ms = time_temp_heat['time_ms']
            temperature = time_temp_heat['temperature']
            heat_factor = time_temp_heat['heat_factor']
            self.db.execute("INSERT INTO data(time_ms, temperature, heat_factor) VALUES (?, ?, ?);",
                       (time_ms, temperature, heat_factor))
        self.db.commit()
