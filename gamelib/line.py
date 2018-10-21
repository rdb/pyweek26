from panda3d import core
from copy import copy


class PowerWire(object):
    drawer = core.WireSegs()
    drawer.set_color((0.2, 0.2, 0.2, 1))
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

    lines = drawer.create(False)
    del drawer

    def __init__(self, world, origin, target):
        self.world = world
        self.origin = origin
        self.target = target

        # If final is false, then self.target does not know about self yet.
        self.final = False

        self.path = self.world.root.attach_new_node(copy(self.lines))
        self.path.set_light_off(True)

    @property
    def vector(self):
        return self.target.pos - self.origin.pos

    def set_target(self, to):
        assert not self.final
        self.target = to
        self.on_update()

    def finish(self):
        assert not self.final
        self.final = True

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
