"""BulletML parser.

This is based on the format described at
http://www.asahi-net.or.jp/~cs8k-cyu/bulletml/bulletml_ref_e.html.

Unless you are adding support for new actions, the only class you
should care about in here is BulletML.
"""

from __future__ import division

from math import sin, cos, radians, pi as PI

from xml.etree.ElementTree import ElementTree

# Python 3 moved this for no really good reason.
try:
    from sys import intern
except ImportError:
    pass

try:
    from io import StringIO
except ImportError:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

from bulletml.errors import Error
from bulletml.expr import NumberDef, INumberDef


__all__ = ["ParseError", "BulletML"]

PI_2 = PI * 2

class ParseError(Error):
    """Raised when an error occurs parsing the XML structure."""
    pass

def realtag(element):
    """Strip namespace poop off the front of a tag."""
    try:
        return element.tag.rsplit('}', 1)[1]
    except ValueError:
        return element.tag

class ParamList(object):
    """List of parameter definitions."""

    def __init__(self, params=()):
        self.params = list(params)

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        return cls([NumberDef(subelem.text) for subelem in element
                    if realtag(subelem) == "param"])

    def __call__(self, params, rank):
        return [param(params, rank) for param in self.params]

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.params)

class Direction(object):
    """Raw direction value."""

    VALID_TYPES = ["relative", "absolute", "aim", "sequence"]

    def __init__(self, type, value):
        if type not in self.VALID_TYPES:
            raise ValueError("invalid type %r" % type)
        self.type = intern(type)
        self.value = value

    def __getstate__(self):
        return [('type', self.type), ('value', self.value.expr)]

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(state["type"], NumberDef(state["value"]))

    @classmethod
    def FromXML(cls, doc, element, default="absolute"):
        """Construct using an ElementTree-style element."""
        return cls(element.get("type", default), NumberDef(element.text))

    def __call__(self, params, rank):
        return (radians(self.value(params, rank)), self.type)

    def __repr__(self):
        return "%s(%r, type=%r)" % (
            type(self).__name__, self.value, self.type)

class ChangeDirection(object):
    """Direction change over time."""

    def __init__(self, term, direction):
        self.term = term
        self.direction = direction

    def __getstate__(self):
        return [('frames', self.term.expr),
                ('type', self.direction.type),
                ('value', self.direction.value.expr)]

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(INumberDef(state["frames"]),
                      Direction(state["type"], NumberDef(state["value"])))

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        for subelem in list(element):
            tag = realtag(subelem)
            if tag == "direction":
                direction = Direction.FromXML(doc, subelem)
            elif tag == "term":
                term = INumberDef(subelem.text)
        try:
            return cls(term, direction)
        except UnboundLocalError as exc:
            raise ParseError(str(exc))

    def __call__(self, owner, action, params, rank, created):
        frames = self.term(params, rank)
        direction, type = self.direction(params, rank)
        action.direction_frames = frames
        action.aiming = False
        if type == "sequence":
            action.direction = direction
        else:
            if type == "absolute":
                direction -= owner.direction
            elif type != "relative": # aim or default
                action.aiming = True
                direction += owner.aim - owner.direction

            # Normalize to [-pi, pi).
            direction = (direction + PI) % PI_2 - PI
            if frames <= 0:
                owner.direction += direction
            else:
                action.direction = direction / frames

    def __repr__(self):
        return "%s(term=%r, direction=%r)" % (
            type(self).__name__, self.term, self.direction)

class Speed(object):
    """Raw speed value."""

    VALID_TYPES = ["relative", "absolute", "sequence"]

    def __init__(self, type, value):
        if type not in self.VALID_TYPES:
            raise ValueError("invalid type %r" % type)
        self.type = intern(type)
        self.value = value

    def __getstate__(self):
        return [('type', self.type), ('value', self.value.expr)]

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(state["type"], NumberDef(state["value"]))

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        return cls(element.get("type", "absolute"), NumberDef(element.text))

    def __call__(self, params, rank):
        return (self.value(params, rank), self.type)

    def __repr__(self):
        return "%s(%r, type=%r)" % (type(self).__name__, self.value, self.type)

class ChangeSpeed(object):
    """Speed change over time."""

    def __init__(self, term, speed):
        self.term = term
        self.speed = speed

    def __getstate__(self):
        return [('frames', self.term.expr),
                ('type', self.speed.type),
                ('value', self.speed.value.expr)]

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(INumberDef(state["frames"]),
                      Speed(state["type"], NumberDef(state["value"])))

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        for subelem in list(element):
            tag = realtag(subelem)
            if tag == "speed":
                speed = Speed.FromXML(doc, subelem)
            elif tag == "term":
                term = INumberDef(subelem.text)
        try:
            return cls(term, speed)
        except UnboundLocalError as exc:
            raise ParseError(str(exc))

    def __call__(self, owner, action, params, rank, created):
        frames = self.term(params, rank)
        speed, type = self.speed(params, rank)
        action.speed_frames = frames
        if frames <= 0:
            if type == "absolute":
                owner.speed = speed
            elif type == "relative":
                owner.speed += speed
        elif type == "sequence":
            action.speed = speed
        elif type == "relative":
            action.speed = speed / frames
        else:
            action.speed = (speed - owner.speed) / frames

    def __repr__(self):
        return "%s(term=%r, speed=%r)" % (
            type(self).__name__, self.term, self.speed)

class Wait(object):
    """Wait for some frames."""

    def __init__(self, frames):
        self.frames = frames

    def __getstate__(self):
        return dict(frames=self.frames.expr)

    def __setstate__(self, state):
        self.__init__(INumberDef(state["frames"]))

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        return cls(INumberDef(element.text))

    def __call__(self, owner, action, params, rank, created):
        action.wait_frames = self.frames(params, rank)
        return True

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.frames)

class Tag(object):
    """Set a bullet tag."""

    def __init__(self, tag):
        self.tag = tag

    def __getstate__(self):
        return dict(tag=self.tag)

    def __setstate__(self, state):
        self.__init__(state["tag"])

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        return cls(element.text)

    def __call__(self, owner, action, params, rank, created):
        owner.tags.add(self.tag)

class Untag(object):
    """Unset a bullet tag."""

    def __init__(self, tag):
        self.tag = tag
        
    def __getstate__(self):
        return dict(tag=self.tag)

    def __setstate__(self, state):
        self.__init__(state["tag"])

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        return cls(element.text)

    def __call__(self, owner, action, params, rank, created):
        try:
            owner.tags.remove(self.tag)
        except KeyError:
            pass

class Appearance(object):
    """Set a bullet appearance."""

    def __init__(self, appearance):
        self.appearance = appearance

    def __getstate__(self):
        return dict(appearance=self.appearance)

    def __setstate__(self, state):
        self.__init__(state["appearance"])

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        return cls(element.text)

    def __call__(self, owner, action, params, rank, created):
        owner.apearance = self.appearance

class Vanish(object):
    """Make the owner disappear."""

    def __init__(self):
        pass

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        return cls()

    def __repr__(self):
        return "%s()" % (type(self).__name__)

    def __call__(self, owner, action, params, rank, created):
        owner.vanish()
        return True

class Repeat(object):
    """Repeat an action definition."""

    def __init__(self, times, action):
        self.times = times
        self.action = action

    def __getstate__(self):
        return [('times', self.times.expr), ('action', self.action)]

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(INumberDef(state["times"]), state["action"])
    
    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        for subelem in list(element):
            tag = realtag(subelem)
            if tag == "times":
                times = INumberDef(subelem.text)
            elif tag == "action":
                action = ActionDef.FromXML(doc, subelem)
            elif tag == "actionRef":
                action = ActionRef.FromXML(doc, subelem)
        try:
            return cls(times, action)
        except UnboundLocalError as exc:
            raise ParseError(str(exc))

    def __call__(self, owner, action, params, rank, created):
        repeat = self.times(params, rank)
        return self.action(owner, action, params, rank, created, repeat)

    def __repr__(self):
        return "%s(%r, %r)" % (type(self).__name__, self.times, self.action)

class If(object):
    """Conditional actions."""

    def __init__(self, cond, then, else_=None):
        self.cond = cond
        self.then = then
        self.else_ = else_

    def __getstate__(self):
        if self.else_:
            return [('cond', self.cond.expr),
                    ('then', self.then),
                    ('else', self.else_)]
        else:
            return [('cond', self.cond.expr), ('then', self.then)]

    def __setstate__(self, state):
        state = dict(state)
        state["else_"] = state.pop("else", None)
        state["cond"] = INumberDef(state["cond"])
        self.__init__(**state)

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        else_ = None
        for subelem in list(element):
            tag = realtag(subelem)
            if tag == "cond":
                cond = INumberDef(subelem.text)
            elif tag == "then":
                then = ActionDef.FromXML(doc, subelem)
            elif tag == "else":
                else_ = ActionDef.FromXML(doc, subelem)
        try:
            return cls(cond, then, else_)
        except UnboundLocalError as exc:
            raise ParseError(str(exc))

    def __call__(self, owner, action, params, rank, created):
        if self.cond(params, rank):
            branch = self.then
        else:
            branch = self.else_

        if branch:
            return branch(owner, action, params, rank, created)

    def __repr__(self):
        if self.else_:
            return "%s(%r, then=%r, else_=%r)" % (
                type(self).__name__, self.cond, self.then, self.else_)
        else:
            return "%s(%r, then=%r)" % (
                type(self).__name__, self.cond, self.then)
        
class Accel(object):
    """Accelerate over some time."""

    horizontal = None
    vertical = None

    def __init__(self, term, horizontal=None, vertical=None):
        self.term = term
        self.horizontal = horizontal
        self.vertical = vertical

    def __getstate__(self):
        state = [('frames', self.term.expr)]
        if self.horizontal:
            state.append(('horizontal', self.horizontal))
        if self.vertical:
            state.append(('vertical', self.vertical))
        return state

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(INumberDef(state["frames"]), state.get("horizontal"),
                      state.get("vertical"))

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        horizontal = None
        vertical = None

        for subelem in list(element):
            tag = realtag(subelem)
            if tag == "term":
                term = INumberDef(subelem.text)
            elif tag == "horizontal":
                horizontal = Speed.FromXML(doc, subelem)
            elif tag == "vertical":
                vertical = Speed.FromXML(doc, subelem)

        try:
            return cls(term, horizontal, vertical)
        except AttributeError:
            raise ParseError

    def __call__(self, owner, action, params, rank, created):
        frames = self.term(params, rank)
        horizontal = self.horizontal and self.horizontal(params, rank)
        vertical = self.vertical and self.vertical(params, rank)
        action.accel_frames = frames
        if horizontal:
            mx, type = horizontal
            if frames <= 0:
                if type == "absolute":
                    owner.mx = mx
                elif type == "relative":
                    owner.mx += mx
            elif type == "sequence":
                action.mx = mx
            elif type == "absolute":
                action.mx = (mx - owner.mx) / frames
            elif type == "relative":
                action.mx = mx / frames
        if vertical:
            my, type = vertical
            if frames <= 0:
                if type == "absolute":
                    owner.my = my
                elif type == "relative":
                    owner.my += my
            elif type == "sequence":
                action.my = my
            elif type == "absolute":
                action.my = (my - owner.my) / frames
            elif type == "relative":
                action.my = my / frames

    def __repr__(self):
        return "%s(%r, horizontal=%r, vertical=%r)" % (
            type(self).__name__, self.term, self.horizontal, self.vertical)

class BulletDef(object):
    """Bullet definition."""

    def __init__(self, actions=(), direction=None, speed=None, tags=(),
                 appearance=None):
        self.direction = direction
        self.speed = speed
        self.actions = list(actions)
        self.tags = set(tags)
        self.appearance = appearance

    def __getstate__(self):
        state = []
        if self.direction:
            state.append(("direction", self.direction))
        if self.speed:
            state.append(("speed", self.speed))
        if self.actions:
            state.append(("actions", self.actions))
        if self.tags:
            state.append(("tags", list(self.tags)))
        if self.appearance:
            state.append(("appearance", self.appearance))
        return state

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(**state)

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        actions = []
        speed = None
        direction = None
        tags = set()
        for subelem in list(element):
            tag = realtag(subelem)
            if tag == "direction":
                direction = Direction.FromXML(doc, subelem)
            elif tag == "speed":
                speed = Speed.FromXML(doc, subelem)
            elif tag == "action":
                actions.append(ActionDef.FromXML(doc, subelem))
            elif tag == "actionRef":
                actions.append(ActionRef.FromXML(doc, subelem))
            elif tag == "tag":
                tags.add(subelem.text)
        dfn = cls(actions, direction, speed, tags)
        doc._bullets[element.get("label")] = dfn
        return dfn

    def __call__(self, owner, action, params, rank, created):
        actions = [a(None, action, params, rank, created)
                   for a in self.actions]
        return (
            self.direction and self.direction(params, rank),
            self.speed and self.speed(params, rank),
            self.tags,
            self.appearance,
            actions)

    def __repr__(self):
        return "%s(direction=%r, speed=%r, actions=%r)" % (
            type(self).__name__, self.direction, self.speed, self.actions)

class BulletRef(object):
    """Create a bullet by name with parameters."""

    def __init__(self, bullet, params=None):
        self.bullet = bullet
        self.params = ParamList() if params is None else params

    def __getstate__(self):
        state = []
        if self.params.params:
            params = [param.expr for param in self.params.params]
            state.append(("params", params))
        state.append(('bullet', self.bullet))
        return state

    def __setstate__(self, state):
        state = dict(state)
        bullet = state["bullet"]
        params = [NumberDef(param) for param in state.get("params", [])]
        self.__init__(bullet, ParamList(params))

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        bullet = cls(element.get("label"), ParamList.FromXML(doc, element))
        doc._bullet_refs.append(bullet)
        return bullet

    def __call__(self, owner, action, params, rank, created):
        params = self.params(params, rank)
        return self.bullet(owner, action, params, rank, created)

    def __repr__(self):
        return "%s(params=%r, bullet=%r)" % (
            type(self).__name__, self.params, self.bullet)

class ActionDef(object):
    """Action definition.

    To support parsing new actions, add tags to
    ActionDef.CONSTRUCTORS. It maps tag names to classes with a
    FromXML classmethod, which take the BulletML instance and
    ElementTree element as arguments.
    """

    # This is self-referential, so it's filled in later.
    CONSTRUCTORS = dict()

    def __init__(self, actions):
        self.actions = list(actions)

    def __getstate__(self):
        return dict(actions=self.actions)

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(state["actions"])

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        actions = []
        for subelem in list(element):
            tag = realtag(subelem)
            try:
                ctr = cls.CONSTRUCTORS[tag]
            except KeyError:
                continue
            else:
                actions.append(ctr.FromXML(doc, subelem))
        dfn = cls(actions)
        doc._actions[element.get("label")] = dfn
        return dfn

    def __call__(self, owner, action, params, rank, created=(), repeat=1):
        Action = action if isinstance(action, type) else type(action) 
        parent = None if owner is None else action
        child = Action(parent, self.actions, params, rank, repeat)
        if owner is not None:
            owner.replace(parent, child)
            child.step(owner, created)
        return child

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.actions)

class ActionRef(object):
    """Run an action by name with parameters."""

    def __init__(self, action, params=None):
        self.action = action
        self.params = params or ParamList()

    def __getstate__(self):
        state = []
        if self.params.params:
            params = [param.expr for param in self.params.params]
            state.append(("params", params))
        state.append(('action', self.action))
        return state

    def __setstate__(self, state):
        state = dict(state)
        action = state["action"]
        params = [NumberDef(param) for param in state.get("params", [])]
        self.__init__(action, ParamList(params))

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        action = cls(element.get("label"), ParamList.FromXML(doc, element))
        doc._action_refs.append(action)
        return action

    def __call__(self, owner, action, params, rank, created=(), repeat=1):
        params = self.params(params, rank)
        return self.action(owner, action, params, rank, created, repeat)

    def __repr__(self):
        return "%s(params=%r, action=%r)" % (
            type(self).__name__, self.params, self.action)

class Offset(object):
    """Provide an offset to a bullet's initial position."""

    VALID_TYPES = ["relative", "absolute"]

    def __init__(self, type, x, y):
        if type not in self.VALID_TYPES:
            raise ValueError("invalid type %r" % type)
        self.type = intern(type)
        self.x = x
        self.y = y

    def __getstate__(self):
        state = [('type', self.type)]
        if self.x:
            state.append(('x', self.x.expr))
        if self.y:
            state.append(('y', self.y.expr))
        return state

    def __setstate__(self, state):
        state = dict(state)
        x = NumberDef(state["x"]) if "x" in state else None
        y = NumberDef(state["y"]) if "y" in state else None
        self.__init__(state["type"], x, y)

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        type = element.get("type", "relative")
        x = None
        y = None
        for subelem in element:
            tag = realtag(subelem)
            if tag == "x":
                x = NumberDef(subelem.text)
            elif tag == "y":
                y = NumberDef(subelem.text)
        return cls(type, x, y)

    def __call__(self, params, rank):
        return (self.x(params, rank) if self.x else 0,
                self.y(params, rank) if self.y else 0)

class FireDef(object):
    """Fire definition (creates a bullet)."""

    def __init__(self, bullet, direction=None, speed=None, offset=None,
                 tags=(), appearance=None):
        self.bullet = bullet
        self.direction = direction
        self.speed = speed
        self.offset = offset
        self.tags = set(tags)
        self.appearance = appearance

    def __getstate__(self):
        state = []
        if self.direction:
            state.append(("direction", self.direction))
        if self.speed:
            state.append(("speed", self.speed))
        if self.offset:
            state.append(("offset", self.offset))
        if self.tags:
            state.append(("tags", list(self.tags)))
        if self.appearance:
            state.append(("appearance", self.appearance))
        try:
            params = self.bullet.params
        except AttributeError:
            state.append(('bullet', self.bullet))
        else:
            if params.params:
                state.append(('bullet', self.bullet))
            else:
                # Strip out empty BulletRefs.
                state.append(('bullet', self.bullet.bullet))
        return state

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(**state)

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        direction = None
        speed = None
        offset = None
        tags = set()
        appearance = None

        for subelem in list(element):
            tag = realtag(subelem)
            if tag == "direction":
                direction = Direction.FromXML(doc, subelem, "aim")
            elif tag == "speed":
                speed = Speed.FromXML(doc, subelem)
            elif tag == "bullet":
                bullet = BulletDef.FromXML(doc, subelem)
            elif tag == "bulletRef":
                bullet = BulletRef.FromXML(doc, subelem)
            elif tag == "offset":
                offset = Offset.FromXML(doc, subelem)
            elif tag == "tag":
                tags.add(subelem.text)
            elif tag == "appearance":
                appearance = subelem.text
        try:
            fire = cls(bullet, direction, speed, offset, tags, appearance)
        except UnboundLocalError as exc:
            raise ParseError(str(exc))
        else:
            doc._fires[element.get("label")] = fire
            return fire

    def __call__(self, owner, action, params, rank, created):
        direction, speed, tags, appearance, actions = self.bullet(
            owner, action, params, rank, created)
        if self.direction is not None:
            direction = self.direction(params, rank)
        if self.speed is not None:
            speed = self.speed(params, rank)
        tags = tags.union(self.tags)
        if self.appearance is not None:
            appearance = self.appearance

        if direction is not None:
            direction, type = direction
            if type == "aim" or type is None:
                direction += owner.aim
            elif type == "sequence":
                direction += action.previous_fire_direction
            elif type == "relative":
                direction += owner.direction
        else:
            direction = owner.aim
        action.previous_fire_direction = direction

        if speed is not None:
            speed, type = speed
            if type == "sequence":
                speed += action.previous_fire_speed
            elif type == "relative":
                # The reference Noiz implementation uses
                # prvFireSpeed here, but the standard is
                # pretty clear -- "In case of the type is
                # "relative", ... the speed is relative to the
                # speed of this bullet."
                speed += owner.speed
        else:
            speed = 1
        action.previous_fire_speed = speed

        x = owner.x
        y = owner.y
        if self.offset is not None:
            off_x, off_y = self.offset(params, rank)
            if self.offset.type == "relative":
                s = sin(direction)
                c = cos(direction)
                x += c * off_x + s * off_y
                y += s * off_x - c * off_y
            else:
                x += off_x
                y += off_y

        if appearance is None:
            appearance = owner.appearance
        bullet = owner.__class__(
            x=x, y=y, direction=direction, speed=speed,
            target=owner.target, actions=actions, rank=rank,
            appearance=appearance, tags=tags)
        created.append(bullet)

    def __repr__(self):
        return "%s(direction=%r, speed=%r, bullet=%r)" % (
            type(self).__name__, self.direction, self.speed, self.bullet)

class FireRef(object):
    """Fire a bullet by name with parameters."""

    def __init__(self, fire, params=None):
        self.fire = fire
        self.params = params or ParamList()

    def __getstate__(self):
        state = []
        if self.params.params:
            params = [param.expr for param in self.params.params]
            state.append(("params", params))
        state.append(('fire', self.fire))
        return state

    def __setstate__(self, state):
        state = dict(state)
        fire = state["fire"]
        params = [NumberDef(param) for param in state.get("params", [])]
        self.__init__(fire, ParamList(params))

    @classmethod
    def FromXML(cls, doc, element):
        """Construct using an ElementTree-style element."""
        fired = cls(element.get("label"), ParamList.FromXML(doc, element))
        doc._fire_refs.append(fired)
        return fired

    def __call__(self, owner, action, params, rank, created):
        params = self.params(params, rank)
        return self.fire(owner, action, params, rank, created)

    def __repr__(self):
        return "%s(params=%r, fire=%r)" % (
            type(self).__name__, self.params, self.fire)

class BulletML(object):
    """BulletML document.

    A BulletML document is a collection of top-level actions and the
    base game type.

    You can add tags to the BulletML.CONSTRUCTORS dictionary to extend
    its parsing. It maps tag names to classes with a FromXML
    classmethod, which take the BulletML instance and ElementTree
    element as arguments.
    
    """

    CONSTRUCTORS = dict(
        bullet=BulletDef,
        action=ActionDef,
        fire=FireDef,
        )

    def __init__(self, type="none", actions=None):
        self.type = intern(type)
        self.actions = [] if actions is None else actions

    def __getstate__(self):
        return [('type', self.type), ('actions', self.actions)]

    def __setstate__(self, state):
        state = dict(state)
        self.__init__(state["type"], actions=state.get("actions"))

    @classmethod
    def FromXML(cls, source):
        """Return a BulletML instance based on XML."""
        if not hasattr(source, 'read'):
            source = StringIO(source)

        tree = ElementTree()
        root = tree.parse(source)

        doc = cls(type=root.get("type", "none"))

        doc._bullets = {}
        doc._actions = {}
        doc._fires = {}
        doc._bullet_refs = []
        doc._action_refs = []
        doc._fire_refs = []

        for element in list(root):
            tag = realtag(element)
            if tag in doc.CONSTRUCTORS:
                doc.CONSTRUCTORS[tag].FromXML(doc, element)

        try:
            for ref in doc._bullet_refs:
                ref.bullet = doc._bullets[ref.bullet]
            for ref in doc._fire_refs:
                ref.fire = doc._fires[ref.fire]
            for ref in doc._action_refs:
                ref.action = doc._actions[ref.action]
        except KeyError as exc:
            raise ParseError("unknown reference %s" % exc)

        doc.actions = [act for name, act in doc._actions.items()
                        if name and name.startswith("top")]

        del(doc._bullet_refs)
        del(doc._action_refs)
        del(doc._fire_refs)
        del(doc._bullets)
        del(doc._actions)
        del(doc._fires)
        
        return doc

    @classmethod
    def FromYAML(cls, source):
        """Create a BulletML instance based on YAML."""

        # Late import to avoid a circular dependency.
        try:
            import bulletml.bulletyaml
            import yaml
        except ImportError:
            raise ParseError("PyYAML is not available")
        else:
            try:
                return yaml.load(source)
            except Exception as exc:
                raise ParseError(str(exc))

    @classmethod
    def FromDocument(cls, source):
        """Create a BulletML instance based on a seekable file or string.

        This attempts to autodetect if the stream is XML or YAML.
        """
        if not hasattr(source, 'read'):
            source = StringIO(source)
        start = source.read(1)
        source.seek(0)
        if start == "<":
            return cls.FromXML(source)
        elif start == "!" or start == "#":
            return cls.FromYAML(source)
        else:
            raise ParseError("unknown initial character %r" % start)

    def __repr__(self):
        return "%s(type=%r, actions=%r)" % (
            type(self).__name__, self.type, self.actions)

ActionDef.CONSTRUCTORS = dict(
    repeat=Repeat,
    fire=FireDef,
    fireRef=FireRef,
    changeSpeed=ChangeSpeed,
    changeDirection=ChangeDirection,
    accel=Accel,
    wait=Wait,
    vanish=Vanish,
    tag=Tag,
    appearance=Appearance,
    untag=Untag,
    action=ActionDef,
    actionRef=ActionRef)
ActionDef.CONSTRUCTORS["if"] = If
