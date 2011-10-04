from time import sleep
from worker import delayable


@delayable
def add(x, y, delay=None):
    # Simulate your work here, preferably something interesting so Python doesn't sleep
    sleep(delay or (x + y if 0 < x + y < 5 else 3))
    return x + y
