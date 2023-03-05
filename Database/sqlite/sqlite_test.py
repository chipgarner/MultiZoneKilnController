import sqlite3, random, time
db = sqlite3.connect('test_4.db')
# db.execute("CREATE TABLE data(time_ms INTEGER PRIMARY KEY, temperature FLOAT, heat_factor FLOAT);")
#
# t = 1600000000
# for i in range(1000*1000):
#     t += 1
#     db.execute("INSERT INTO data(time_ms, temperature, heat_factor) VALUES (?, ?, ?);", (t, 37.876, 0.8))
# db.commit()

# t will range in a ~ 10 000 seconds window
t1, t2 = 1600005000, 1600005100  # time range of width 100 seconds (i.e. 1%)
start = time.time()
for it in db.execute("SELECT time_ms, temperature, heat_factor FROM data WHERE time_ms BETWEEN ? AND ?", (t1, t2)):
    print(it)
    pass
print(time.time()-start)
