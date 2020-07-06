from __future__ import division


def hex_to_rgb(h):
    if h is None:
        return 0, 0, 0
    h = h[1:7]
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
