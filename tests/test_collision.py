import collections

from tests import TestCase, add

from bulletml import collision

Dummy = collections.namedtuple("Dummy", "x y px py radius")

class Toverlaps(TestCase):
    def test_inside(self):
        self.failUnless(collision.overlaps(
            Dummy(0, 0, 0, 0, 10),
            Dummy(0, 0, 0, 0, 1)))

    def test_near(self):
        self.failUnless(collision.overlaps(
            Dummy(0, 0, 0, 0, 1),
            Dummy(0.5, 0.5, 0, 0, 1)))

    def test_far(self):
        self.failIf(collision.overlaps(
            Dummy(0, 0, 0, 0, 1),
            Dummy(20, 20, 0, 0, 1)))
add(Toverlaps)

class Tcollides(TestCase):
    def test_cross(self):
        a = Dummy(0, 0, 100, 100, 1)
        b = Dummy(0, 100, 100, 0, 1)
        self.failUnless(collision.collides(a, b))

    def test_miss(self):
        a = Dummy(0, 0, 100, 75, 1)
        b = Dummy(0, 100, 75, 0, 1)
        self.failIf(collision.collides(a, b))

    def test_stationary(self):
        a = Dummy(100, 0, 100, 0, 1)
        b = Dummy(0, 100, 100, 0, 1)
        self.failUnless(collision.collides(a, b))
add(Tcollides)

class Tcollides_all(TestCase):
    def test_cross(self):
        a = Dummy(0, 0, 100, 100, 1)
        b = Dummy(100, 100, 0, 100, 1)
        c = Dummy(0, 100, 100, 0, 1)
        collides = collision.collides_all(a, [a, b, c])
        self.failUnlessEqual(collides, [a, c])
add(Tcollides_all)
