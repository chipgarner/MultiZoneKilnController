import sqlite3

db = sqlite3.connect('firing.db')
db.execute("CREATE TABLE IF NOT EXISTS data(time_ms INTEGER NOT NULL PRIMARY KEY, temperature FLOAT, heat_factor FLOAT);")
db.execute("CREATE TABLE IF NOT EXISTS profiles(INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL UNIQUE , segments TEXT NOT NULL );")

def update():
    time_ms = 1677994674555
    temperature = 27.1
    heat_factor = 0.3

    db.execute("INSERT INTO data(time_ms, temperature, heat_factor) VALUES (?, ?, ?);", (time_ms, temperature, heat_factor))
    db.commit()

# update()