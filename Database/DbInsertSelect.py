import sqlite3
import json


class DbInsertSelect:
    def __init__(self):
        self.db = sqlite3.connect('Database/firing.db')

    def send_time_stamped_message(self, times_temps_heats_for_zones: dict):
        for zone in times_temps_heats_for_zones:
            table_name = zone.replace(" ", "")
            for time_temp_heat in times_temps_heats_for_zones['Zone 1']: # Only one zone for now
                time_ms = time_temp_heat['time_ms']
                temperature = time_temp_heat['temperature']
                heat_factor = time_temp_heat['heat_factor']
                self.db.execute("INSERT INTO " + table_name + "(time_ms, temperature, heat_factor) VALUES (?, ?, ?);",
                           (time_ms, temperature, heat_factor))
            self.db.commit()

    def add_profile(self, name: str, profile: str):
        self.db.execute("INSERT INTO profiles(name, segments) VALUES (?, ?);",
                        (name, profile))

        self.db.commit()

    def get_profiles(self) -> list:
        cur = self.db.cursor()
        cur.execute("SELECT * FROM profiles")
        profiles = cur.fetchall()

        return profiles

    def get_profile_segments_by_name(self, name: str) -> str:
        cur = self.db.cursor()
        cur.execute("SELECT segments FROM profiles WHERE name = ?;", [name])
        segments = cur.fetchall()

        segs = '{"segments": segments[0][0]}'
        segments = json.loads(segs)

        return profile


import Profile
if __name__ == '__main__':
    profile = Profile.Profile("fast.json")
    name = profile.name
    data = profile.data
    try:
        DbInsertSelect().add_profile(name, json.dumps(data))
    except Exception as ex:
        print(ex)

    profiles = DbInsertSelect().get_profiles()
    print(profiles)

    profile = DbInsertSelect().get_profile_by_name("new_fast")
    assert type(profile) is list
    print(profile)

    profile = Profile.Profile("fast.json")
    profile = json.loads(profile.get_profile("fast.json"))
    new_fast = Profile.convert_old_profile(profile)
    new_fast['name'] = 'new_fast'
    DbInsertSelect().add_profile(new_fast['name'], str(new_fast['segments']))