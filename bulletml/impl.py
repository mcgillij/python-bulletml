"""BulletML implementation."""

from __future__ import division

from math import atan2, sin, cos

__all__ = ["Action", "Bullet"]

class Action(object):
    """Running action implementation.

    To implement new actions, add a new element/class pair to
    parser.ActionDef.CONSTRUCTORS.  It should support FromXML,
    __getstate__, and __setstate__, and 5-ary __call__:

        def __call__(self, owner, action, params, rank, created)

    Which will be called to execute it. This function should modify
    owner, action, and created in-place, and return true if action
    execution should stop for this bullet this frame.

    """

    def __init__(self, parent, actions, params, rank, repeat=1):
        self.actions = actions
        self.parent = parent
        self.repeat = repeat
        self.wait_frames = 0
        self.speed = 0
        self.speed_frames = 0
        self.direction = 0
        self.direction_frames = 0
        self.aiming = False
        self.mx = 0
        self.my = 0
        self.accel_frames = 0
        self.previous_fire_direction = 0
        self.previous_fire_speed = 0
        self.params = params
        self.pc = -1
        self.finished = False
        if parent:
            self.copy_state(parent)

    def __repr__(self):
        return "%s(pc=%r, actions=%r)" % (
            type(self).__name__, self.pc, self.actions)

    def vanish(self):
        """End this action and its parents."""
        if self.parent:
            self.parent.vanish()
        self.pc = None
        self.finished = True

    def copy_state(self, other):
        """Copy fire/movement state from other to self."""
        self.direction_frames = other.direction_frames
        self.direction = other.direction
        self.aiming = other.aiming
        self.speed_frames = other.speed_frames
        self.speed = other.speed
        self.accel_frames = other.accel_frames
        self.mx = other.mx
        self.my = other.my
        self.previous_fire_direction = other.previous_fire_direction
        self.previous_fire_speed = other.previous_fire_speed

    def step(self, owner, created):
        """Advance by one frame."""

        if self.speed_frames > 0:
            self.speed_frames -= 1
            owner.speed += self.speed

        if self.direction_frames > 0:
            self.direction_frames -= 1
            # I'm still not sure what the aim check is supposed to do.
            if self.aiming and self.direction_frames <= 0:
                owner.direction += owner.aim
            else:
                owner.direction += self.direction

        if self.accel_frames > 0:
            self.accel_frames -= 1
            owner.mx += self.mx
            owner.my += self.my

        if self.pc is None:
            return

        if self.wait_frames > 0:
            self.wait_frames -= 1
            return

        s_params = self.params
        rank = owner.rank

        while True:
            self.pc += 1

            try:
                action = self.actions[self.pc]
            except IndexError:
                self.repeat -= 1
                if self.repeat <= 0:
                    self.pc = None
                    self.finished = True
                    if self.parent is not None:
                        self.parent.copy_state(self)
                        owner.replace(self, self.parent)
                    break
                else:
                    self.pc = 0
                    action = self.actions[self.pc]

            if action(owner, self, s_params, rank, created):
                break

class Bullet(object):
    """Simple bullet implementation.

    Attributes:
    x, y - current X/Y position
    px, py - X/Y position prior to the last step
    mx, my - X/Y axis-oriented speed modifier ("acceleration")
    direction - direction of movement, in radians
    speed - speed of movement, in units per frame
    target - object with .x and .y fields for "aim" directions
    vanished - set to true by a <vanish> action
    rank - game difficulty, 0 to 1, default 0.5
    tags - string tags set by the running actions
    appearance - string used to set bullet appearance
    radius - radius for collision
    finished - true if all actions are finished and the bullet vanished

    Contructor Arguments:
    x, y, direction, speed, target, rank, tags, appearance, radius
        - same as the above attributes
    actions - internal action list
    Action - custom Action constructor

    """

    def __init__(self, x=0, y=0, direction=0, speed=0, target=None,
                 actions=(), rank=0.5, tags=(), appearance=None,
                 radius=0.5):
        self.x = self.px = x
        self.y = self.py = y
        self.radius = radius
        self.mx = 0
        self.my = 0
        self.direction = direction
        self.speed = speed
        self.vanished = False
        self.finished = False
        self.target = target
        self.rank = rank
        self.tags = set(tags)
        self.appearance = appearance
        self.actions = list(actions)

    @classmethod
    def FromDocument(cls, doc, x=0, y=0, direction=0, speed=0, target=None,
                     params=(), rank=0.5, Action=Action):
        """Construct a new Bullet from a loaded BulletML document."""
        actions = [action(None, Action, params, rank)
                   for action in doc.actions]
        return cls(x=x, y=y, direction=direction, speed=speed,
                   target=target, actions=actions, rank=rank)

    def __repr__(self):
        return ("%s(%r, %r, accel=%r, direction=%r, speed=%r, "
                "actions=%r, target=%r, appearance=%r, vanished=%r)") % (
            type(self).__name__, self.x, self.y, (self.mx, self.my),
            self.direction, self.speed, self.actions, self.target,
            self.appearance, self.vanished)

    @property
    def aim(self):
        """Angle to the target, in radians.

        If the target does not exist or cannot be found, return 0.
        """
        try:
            target_x = self.target.x
            target_y = self.target.y
        except AttributeError:
            return 0
        else:
            return atan2(target_x - self.x, target_y - self.y)

    def vanish(self):
        """Vanish this bullet and stop all actions."""
        self.vanished = True
        for action in self.actions:
            action.vanish()
        self.actions = []

    def replace(self, old, new):
        """Replace an active action with another.

        This is mostly used by actions internally to queue children.
        """
        try:
            idx = self.actions.index(old)
        except ValueError:
            pass
        else:
            self.actions[idx] = new

    def step(self):
        """Advance by one frame.

        This updates the position and velocity, and may also set the
        vanished flag.

        It returns any new bullets this bullet spawned during this step.
        """
        created = []

        finished = self.vanished
        for action in self.actions:
            action.step(self, created)
            finished = finished and action.finished
        if finished:
            for action in self.actions:
                finished = finished and action.finished
        self.finished = finished

        speed = self.speed
        direction = self.direction
        self.px = self.x
        self.py = self.y
        self.x += self.mx + sin(direction) * speed
        self.y += -self.my + cos(direction) * speed

        return created
