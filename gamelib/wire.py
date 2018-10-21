from panda3d import core
from copy import copy

from . import constants


class PowerWire(object):
    drawer = core.LineSegs()
    drawer.set_color((0.05, 0.05, 0.05, 1))
    drawer.set_thickness(2)

    drawer.move_to((0, 0, 1))
    drawer.draw_to((0, 1, 1))

    drawer.move_to((-0.1, 0, 0.9))
    drawer.draw_to((-0.1, 1, 0.9))
    drawer.move_to((0.1, 0, 0.9))
    drawer.draw_to((0.1, 1, 0.9))

    drawer.move_to((-0.15, 0, 0.8))
    drawer.draw_to((-0.15, 1, 0.8))
    drawer.move_to((0.15, 0, 0.8))
    drawer.draw_to((0.15, 1, 0.8))

    drawer.move_to((-0.1, 0, 0.7))
    drawer.draw_to((-0.1, 1, 0.7))
    drawer.move_to((0.1, 0, 0.7))
    drawer.draw_to((0.1, 1, 0.7))

    wires = drawer.create(False)
    del drawer

    def __init__(self, world, origin, target):
        self.world = world
        self.origin = origin
        self.target = target

        # If placed is false, then self.target does not know about self yet.
        self.placed = False

        self.path = self.world.root.attach_new_node(copy(self.wires))
        self.path.set_light_off(1)

    def __repr__(self):
        return "{!r}--{!r}".format(self.origin, self.target)

    @property
    def vector(self):
        return self.target.pos - self.origin.pos

    def try_set_target(self, to):
        """Try changing the target of the wire, for use during placement."""
        assert not self.placed

        if to is None:
            return False

        if to is self.origin:
            return False

        # Already a placed connection here?
        if to in self.origin.connections and self.origin.connections[to].placed:
            return False

        if (self.origin.pos - to.pos).length_squared() > constants.max_pylon_distance_sq:
            return False

        self.set_target(to)
        return True

    def set_target(self, to):
        """During placement, force connecting to this node."""
        assert to is not self.origin

        if self.target is not to:
            del self.target.connections[self.origin]
            del self.origin.connections[self.target]
            self.target = to
            self.target.connections[self.origin] = self
            self.origin.connections[self.target] = self
            self.on_update()

            self.target.on_update()
            self.origin.on_update()

    def cancel_placement(self):
        del self.target.connections[self.origin]
        del self.origin.connections[self.target]

        self.on_update()

        self.target.on_update()
        self.origin.on_update()

        self.path.remove_node()

    def finish_placement(self):
        assert not self.placed
        self.placed = True

        print("Finishing placement of {}".format(self))
        self.target.placed = True

    def destroy(self):
        self.path.remove_node()

        if self.origin.connections.get(self.target) is self:
            del self.origin.connections[self.target]

        if self.target.connections.get(self.origin) is self:
            del self.target.connections[self.origin]

    def on_update(self):
        """Called when position information of neighbours changes."""

        self.path.set_pos(self.origin.x, self.origin.y, 0)
        self.path.look_at(self.target.x, self.target.y, 0)
        self.path.set_sy((self.target.root.get_pos() - self.origin.root.get_pos()).length())
