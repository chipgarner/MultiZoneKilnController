import time
import json
import os

class FilesHandler:
    def __init__(self):
        self.firing_name = None
        self.full_path = None
        self.firings_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '.', 'Firings'))

    def create_firing_file_name(self) -> str:
        name = time.strftime("%Y %m %d %H", time.localtime()) + '.json'
        return name

    def start_firing(self, profile):
        firing_name = self.create_firing_file_name()

        self.full_path = os.path.join(self.firings_directory, firing_name)

        with open(self.full_path, 'w') as f:
            f.write(json.dumps(profile))

    def save_update(self, update_message):
        if self.full_path is not None:
            with open(self.full_path, 'a') as f:
                f.write(update_message + "\n")

    def  get_full_path(self):
        return self.full_path


    @staticmethod
    def get_last_line(full_path: str) -> str:
        with open(full_path, 'r') as firing:
            for line in firing:
                pass
        return line

    def check_for_restart(self) -> str:
        restart_file_path = None
        files = [f for f in os.listdir(self.firings_directory)
                 if os.path.isfile(os.path.join(self.firings_directory, f))]

        if files is not None:
            files.sort()
            path = os.path.join(self.firings_directory, files[-1])
            line = self.get_last_line(path)
            if line is not None:
                line = json.loads(line)
                time_ms = line["zones_status_array"][0]["time_ms"]
                age = (time.time() - time_ms/1000) /3600  # Hours
                if age < 2:
                    restart_file_path = path

            return restart_file_path
