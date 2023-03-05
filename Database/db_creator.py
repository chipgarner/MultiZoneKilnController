import sqlite3

db = sqlite3.connect('sqlite/firing.db')
db.execute("CREATE TABLE data(time_ms INTEGER PRIMARY KEY, temperature FLOAT, heat_factor FLOAT);")
