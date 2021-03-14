"""BulletML parser.

BulletML is the Bullet Markup Language. BulletML can describe the
barrage of bullets in shooting games. (For example Progear, Psyvariar,
Gigawing2, G DARIUS, XEVIOUS, ...) This module parses and executes
BulletML scripts in Python. All data structures in it are
renderer-agnostic. A sample renderer for Pygame is included. The full
API documentation is contained in its Python docstrings.

In addition to the standard BulletML XML format, this module supports
an equivalent YAML format. For convenience, two simple collision
routines are provided, bulletml.overlaps for stationary circles and
bulletml.collides for moving circles.

More information is available at the BulletML homepage,
http://www.asahi-net.or.jp/~cs8k-cyu/bulletml/index_e.html, or the
python-bulletml homepage, https://yukkurigames.com/python-bulletml/.


Basic Usage:

    from bulletml import Bullet, BulletML

    doc = BulletML.FromDocument(open("test.xml", "rU"))
    player = ...  # On your own here, but it needs x and y fields.
    rank = 0.5    # Player difficulty, 0 to 1

    bullet = Bullet.FromDocument(doc, x, y, target=player, rank=rank)
    bullets = [bullet]
    ...
    for bullet in bullets:
        bullets.extend(bullet.step()) # step() returns new Bullets
    ...

For drawing, you're on your own, but Bullet instances have a number of
attributes that can be used to influence it.

"""

from bulletml.parser import BulletML
from bulletml.impl import Bullet
from bulletml.collision import overlaps, collides, collides_all

VERSION = (3,)
VERSION_STRING = ".".join(map(str, VERSION))

__all__ = ["VERSION", "VERSION_STRING", "Bullet", "BulletML",
           "overlaps", "collides", "collides_all"]
