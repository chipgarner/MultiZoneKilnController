import sqlite3
import time


con = sqlite3.connect("test.db")
cur = con.cursor()
# cur.execute("CREATE TABLE Zone1(epoch_time, temperature, heat)")
ttime = time.time()
cur.execute("""
    INSERT INTO Zone1 VALUES
        (tt, 1969, 0.6),
        (time.time(), 1971, 0.7)
""")
con.commit()