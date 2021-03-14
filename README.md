# python-bulletml - BulletML for Python

BulletML is the Bullet Markup Language. BulletML can describe the
barrage of bullets in shooting games. (For example Progear, Psyvariar,
Gigawing2, G DARIUS, XEVIOUS, ...) This module parses and executes
BulletML scripts in Python. All data structures in it are
renderer-agnostic. A sample renderer for Pygame is included. The full
API documentation is contained in its Python docstrings.

In addition to the standard BulletML XML format, this module supports
an equivalent YAML format. For convenience, two simple collision
routines are provided, `bulletml.overlaps` for stationary circles and
`bulletml.collides` for moving circles.

More information is available at
[the BulletML homepage](http://www.asahi-net.or.jp/~cs8k-cyu/bulletml/index_e.html),
or
[the python-bulletml homepage](https://yukkurigames.com/python-bulletml/).

    $ ./bulletml-runner examples/*/*.xml

Use Page Up and Page Down to switch between bullet definitions, S to
respawn the bullet pattern, and Enter to restart it.


## Installing

BulletML requires Python 2.6 or later. It should work on Python 3. It
has no dependencies outside the CPython standard library.

    $ ./setup.py build
    $ sudo ./setup.py install


## License

The BulletML specification is the work of Kenta Cho.

All example BulletML files in the examples folder are released into
the public domain. Everything else is covered by the following
license:

Copyright 2010 Joe Wreschnig

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
