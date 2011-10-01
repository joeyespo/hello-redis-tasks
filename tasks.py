from time import sleep
from worker import delayable


@delayable
def add(x, y, delay=None):
    # Simulate work, preferably something interesting so Python doesn't sleep
    sleep(delay or x + y)
    return x + y
