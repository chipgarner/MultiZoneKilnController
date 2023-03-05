import sqlite3, random, time
db = sqlite3.connect('test.db')
db.execute("CREATE TABLE data(dt INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT);")

t = 1600000000
for i in range(1000*1000):
    if random.randint(0, 100) == 0:  # timestamp increases of 1 second with probability 1%
        t += 1
    db.execute("INSERT INTO data(dt, label) VALUES (MAX(?, (SELECT seq FROM sqlite_sequence) + 1), 'hello');", (t*10000, ))
db.commit()

# t will range in a ~ 10 000 seconds window
t1, t2 = 1600005000*10000, 1600005100*10000  # time range of width 100 seconds (i.e. 1%)
start = time.time()
for _ in db.execute("SELECT 1 FROM data WHERE dt BETWEEN ? AND ?", (t1, t2)):
    pass
print(time.time()-start)
