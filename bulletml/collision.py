"""Simple collision check.

This module provides simple collision checking appropriate for
shmups. It provides routines to check whether two moving circles
collided during the past frame.

An equivalent C-based version will be used automatically if it was
compiled and installed with the module. If available, it will be noted
in the docstrings for the functions.

Basic Usage:

    from bulletml.collision import collides

    for bullet in bullets:
        if collides(player, bullet): ... # Kill the player.
"""

from __future__ import division

def overlaps(a, b):
    """Return true if two circles are overlapping.

    Usually, you'll want to use the 'collides' method instead, but
    this one can be useful for just checking to see if the player has
    entered an area or hit a stationary oject.

    (This function is unoptimized.)
    """

    dx = a.x - b.x
    dy = a.y - b.y
    try:
        radius = a.radius + b.radius
    except AttributeError:
        radius = getattr(a, 'radius', 0.5) + getattr(b, 'radius', 0.5)

    return dx * dx + dy * dy <= radius * radius

def collides(a, b):
    """Return true if the two moving circles collide.

    a and b should have the following attributes:

    x, y - required, current position
    px, py - not required, defaults to x, y, previous frame position
    radius - not required, defaults to 0.5

    (This function is unoptimized.)

    """
    # Current locations.
    xa = a.x
    xb = b.x
    ya = a.y
    yb = b.y

    # Treat b as a point, we only need one radius.
    try:
        radius = a.radius + b.radius
    except AttributeError:
        radius = getattr(a, 'radius', 0.5) + getattr(b, 'radius', 0.5)

    # Previous frame locations.
    try: pxa = a.px
    except KeyError: pxa = xa
    try: pya = a.py
    except KeyError: pya = ya
    try: pxb = b.px
    except KeyError: pxb = xb
    try: pyb = b.py
    except KeyError: pyb = yb

    # Translate b's final position to be relative to a's start.
    # And now, circle/line collision.
    dir_x = pxa + (xb - xa) - pxb
    dir_y = pya + (yb - ya) - pyb

    diff_x = pxa - pxb
    diff_y = pya - pyb
    if (dir_x < 0.0001 and dir_x > -0.0001
        and dir_y < 0.0001 and dir_y > -0.0001):
        # b did not move relative to a, so do point/circle.
        return diff_x * diff_x + diff_y * diff_y < radius * radius

    # dot(diff, dir) / dot(dir, dir)
    t = (diff_x * dir_x + diff_y * dir_y) / (dir_x * dir_x + dir_y * dir_y)
    if t < 0:
        t = 0
    elif t > 1:
        t = 1

    dist_x = pxa - (pxb + dir_x * t)
    dist_y = pya - (pyb + dir_y * t)

    # dist_sq < radius_sq
    return dist_x * dist_x + dist_y * dist_y <= radius * radius

def collides_all(a, others):
    """Filter the second argument to those that collide with the first.

    This is equivalent to filter(lambda o: collides(a, o), others),
    but is much faster when the compiled extension is available (which
    it is not currently).

    """
    return filter(lambda o: collides(a, o), others)

try:
    from bulletml._collision import collides, overlaps, collides_all
except ImportError:
    pass
