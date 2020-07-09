from __future__ import absolute_import, division


def hex_to_rgb(h):
    if h is None:
        return 0, 0, 0
    h = h[1:7]
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def blend_two_colors(colour1, colour2):
    """
    """
    r = average(colour1[0], colour2[0])
    g = average(colour1[1], colour2[1])
    b = average(colour1[2], colour2[2])
    return r, g, b


def average(a, b):
    return round((a + b) / 2)
