"""BulletYAML implementation.

BulletYAML is a translation of BulletML into YAML. The structure is
mostly the same as the XML version, except BulletRef/FireRef/ActionRef
elements are only used if they contain parameters, as YAML has its own
intra-document references. Parameterless references are turned into
direct YAML references.

If PyYAML is installed, importing this module automatically registers
BulletYAML tags with the default loader and dumper.

Example BulletYAML document:
    !BulletML
    type: vertical
    actions:
      - !ActionDef
        actions:
        - !FireDef
          bullet: !BulletDef {}

"""

from bulletml import parser

def register(Loader=None, Dumper=None):
    """Register BulletYAML types for a Loader and Dumper."""
    for cls in [parser.Direction, parser.ChangeDirection,
                parser.Speed, parser.ChangeSpeed, parser.Wait,
                parser.Tag, parser.Untag, parser.Vanish,
                parser.Repeat, parser.Accel, parser.BulletDef,
                parser.BulletRef, parser.ActionDef, parser.ActionRef,
                parser.FireDef, parser.FireRef, parser.Offset,
                parser.Appearance, parser.If, parser.BulletML]:

        def add(cls, loader, dumper):
            """Register a class in a new variable scope."""
            tag = "!" + cls.__name__
            if loader:
                def construct(loader, node):
                    """Construct an object."""
                    return loader.construct_yaml_object(node, cls)
                loader.add_constructor(tag, construct)
            if dumper:
                def represent(dumper, obj):
                    """Represent an object."""
                    return dumper.represent_yaml_object(tag, obj, cls)
                dumper.add_representer(cls, represent)

        add(cls, Loader, Dumper)

try:
    import yaml
except ImportError:
    pass
else:
    register(yaml, yaml)
