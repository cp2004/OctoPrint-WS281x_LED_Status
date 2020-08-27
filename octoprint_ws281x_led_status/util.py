from __future__ import absolute_import, division
from time import sleep


def hex_to_rgb(h):
    if h is None:
        return 0, 0, 0
    h = h[1:7]
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def blend_two_colors(colour1, colour2, percent_of_c1=None):
    """
    """
    if percent_of_c1:
        colour1 = [x * percent_of_c1 for x in colour1]
        percent_of_c2 = 1 - percent_of_c1
        colour2 = [x * percent_of_c2 for x in colour2]

    r = average(colour1[0], colour2[0])
    g = average(colour1[1], colour2[1])
    b = average(colour1[2], colour2[2])
    return tuple([int(r), int(g), int(b)])


def average(a, b):
    return round((a + b) / 2)


def milli_sleep(m_secs):
    sleep(m_secs / 1000)


def q_poll_sleep(secs, queue):
    """
    Polls the queue before sleeping, so that we can abort effect if necessary
    :param secs: time in seconds
    :param queue: multiprocessing.queue() object
    :return: bool: False if we should not proceed, true if we can
    """
    if not queue.empty():
        return False
    else:
        sleep(secs)
        return True


def q_poll_milli_sleep(m_secs, queue):
    """
        Polls the queue before sleeping, so that we can abort effect if necessary
        :param m_secs: time in milliseconds
        :param queue: multiprocessing.queue() object
        :return: bool: False if we should not proceed, true if we can
    """
    return q_poll_sleep(m_secs / 1000, queue)


def wheel(pos):
    """Get a 3 tuple r, g, b value for a position 0-255
    From Adafruit's strandtest.py
    :param pos: int 0-255
    :return tuple r, g, b from 0-255"""
    if pos < 85:
        return int(pos * 3), int(255 - pos * 3), 0
    elif pos < 170:
        pos -= 85
        return int(255 - pos * 3), 0, int(pos * 3)
    else:
        pos -= 170
        return 0, int(pos * 3), int(255 - pos * 3)
