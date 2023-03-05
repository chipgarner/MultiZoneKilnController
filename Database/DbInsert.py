import sqlite3
from Notifiers import Notifier


class DbInsert(Notifier):
    def __init__(self):
        self.db = sqlite3.connect('firing.db')

    def send_time_stamped_message(self, a_message: str) -> bool:
        self.db.execute("INSERT INTO data(time_ms, temperature, heat_factor) VALUES (?, ?, ?);", (t, 37.876, 0.8))
        self.db.commit()
