import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from random import randrange
import time

start = time.time()
fig = plt.figure(figsize=(6, 3))
x = [0.0]
y = [0]

ln, = plt.plot(x, y, '-')


def update(frame):

    x.append(x[-1] + (time.time() - start) / 60)
    y.append(y[-1] + randrange(0, 2) + 1)

    ln.set_data(x, y)
    fig.gca().relim()
    fig.gca().autoscale_view()
    return ln,


animation = FuncAnimation(fig, update, interval=500)
plt.show()