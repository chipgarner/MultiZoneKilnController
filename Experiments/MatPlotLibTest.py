from collections import deque
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.ticker import FuncFormatter


def init():
    line.set_ydata([np.nan] * len(x))
    return line,

def animate(i):
    # Add next value
    data.append(np.random.randint(0, max_rand))
    line.set_ydata(data)
    plt.savefig('e:\\python temp\\fig_{:02}'.format(i))
    print(i)
    return line,

max_x = 10
max_rand = 5

data = deque(np.zeros(max_x), maxlen=max_x)  # hold the last 10 values
x = np.arange(0, max_x)

fig, ax = plt.subplots()
ax.set_ylim(0, max_rand)
ax.set_xlim(0, max_x-1)
line, = ax.plot(x, np.random.randint(0, max_rand, max_x))
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '{:.0f}s'.format(max_x - x - 1)))
plt.xlabel('Seconds ago')

ani = animation.FuncAnimation(
    fig, animate, init_func=init, interval=500, blit=True, save_count=10)

plt.show()
