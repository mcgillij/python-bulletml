import os
import glob

from bulletml import BulletML, Bullet, bulletyaml
from tests import TestCase, add

class Texamples_xml(TestCase):
    pass

class Texamples_yaml(TestCase):
    pass

class Texamples_repr(TestCase):
    pass

class Texamples_run(TestCase):
    pass

for filename in glob.glob("examples/*/*.xml"):
    basename = os.path.basename(filename)[:-4].replace("-", "_")

    def test_xml(self, filename=filename):
        BulletML.FromDocument(open(filename, "rU"))
    setattr(Texamples_xml, "test_" + basename, test_xml)

    try:
        import yaml
    except ImportError:
        pass
    else:
        def test_yaml(self, filename=filename):
            doc = BulletML.FromDocument(open(filename, "rU"))
            doc = yaml.load(yaml.dump(doc))
            doc = yaml.load(yaml.dump(doc))
        setattr(Texamples_yaml, "test_" + basename, test_yaml)

    def test_repr(self, filename=filename):
        doc = BulletML.FromDocument(open(filename, "rU"))
        repr(doc)
    setattr(Texamples_repr, "test_" + basename, test_repr)

    def test_run(self, filename=filename):
        doc = BulletML.FromDocument(open(filename, "rU"))
        bullets = [Bullet.FromDocument(doc)]
        for i in range(100):
            for bullet in bullets:
                bullets.extend(bullet.step())
    setattr(Texamples_run, "test_" + basename, test_run)
                

add(Texamples_xml)
add(Texamples_yaml)
add(Texamples_repr)
add(Texamples_run)
