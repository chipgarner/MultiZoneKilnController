import time
import json
import os

class FilesHandler:
    def __init__(self):
        self.firing_name = None
        self.full_path = None

    def create_firing_file_name(self) -> str:
        name = time.strftime("%Y %m %d %H", time.localtime())
        return name

    def start_firing(self, profile):
        self.firing_name = self.create_firing_file_name()

        file_name = self.firing_name + '.' + 'json'
        self.full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Firings/', file_name + "\n"))

        with open(self.full_path, 'w') as f:
            f.write(json.dumps(profile))

    def save_update(self, update_message):
        if self.full_path is not None:
            with open(self.full_path, 'a') as f:
                f.write(update_message + "\n")