# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

__author__ = "Charlie Powell <cp2004.github@gmail.com"
__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (c) Charlie Powell 2020-2021 - released under the terms of the AGPLv3 License"

import subprocess
import threading
from time import sleep, tzname


def hex_to_rgb(h):
    if h is None:
        return 0, 0, 0
    h = h[1:7]
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def apply_color_correction(settings, r, g, b):
    red = blue = green = white = 0
    # Use white LEDs if white override is enabled
    if r == g == b == 255 and settings["white_override"] is True:
        white = int((int(settings["white_brightness"]) / 100) * 255)
    else:
        red = int_0_255(r * (int(settings["red"]) / 100))
        green = int_0_255(g * (int(settings["green"]) / 100))
        blue = int_0_255(b * (int(settings["blue"]) / 100))

    return int_0_255(red), int_0_255(green), int_0_255(blue), int_0_255(white)


def blend_two_colors(colour1, colour2, percent_of_c1=None):
    """"""
    if percent_of_c1:
        colour1 = [x * percent_of_c1 for x in colour1]
        percent_of_c2 = 1 - percent_of_c1
        colour2 = [x * percent_of_c2 for x in colour2]

    r = average(colour1[0], colour2[0])
    g = average(colour1[1], colour2[1])
    b = average(colour1[2], colour2[2])
    return tuple([int_0_255(r), int_0_255(g), int_0_255(b)])


def average(a, b):
    return int((a + b) / 2)


def milli_sleep(m_secs):
    if not isinstance(m_secs, float):
        m_secs = float(m_secs)
    sleep(m_secs / 1000)


def q_poll_sleep(secs, queue):
    """
    Polls the queue before sleeping, so that we can abort effect if necessary
    :param secs: time in seconds
    :param queue: multiprocessing.queue() object
    :return: bool: False if we should not proceed, true if we can
    """
    if not isinstance(secs, float):
        secs = float(secs)
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
    if not isinstance(m_secs, int):
        m_secs = int(m_secs)
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


def run_system_command(command, password=None):
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    if password:
        stdout, stderr = process.communicate("{}\n".format(password).encode())
    else:
        stdout, stderr = process.communicate()

    if (
        stderr
        and "Sorry" in stderr.decode("utf-8")
        or "no password" in stderr.decode("utf-8")
    ):
        # .decode for Python 2/3 compatibility, make sure utf-8
        return stdout.decode("utf-8"), "password"
    else:
        return stdout.decode("utf-8"), None


def get_timezone():
    return tzname


def start_daemon_thread(target, args=(), kwargs=None, name="WS281x LED Status thread"):
    if kwargs is None:
        kwargs = {}
    t = threading.Thread(
        target=target,
        args=args,
        kwargs=kwargs,
        name=name,
    )
    t.daemon = True
    t.start()
    return t


def start_daemon_timer(interval, target, args=(), kwargs=None):
    if kwargs is None:
        kwargs = {}
    t = threading.Timer(interval=interval, function=target, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t


def int_0_255(value):
    return max(min(int(value), 255), 0)


def clear_queue(q):
    while not q.empty():
        q.get(False)
