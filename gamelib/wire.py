from panda3d import core
from copy import copy
import math

from . import constants


class PowerWire(object):
    drawer = core.LineSegs()
    #drawer.set_color((0.05, 0.05, 0.05, 1))
    drawer.set_thickness(4)

    sag = 0.25
    for x, z in (0, 1), (-0.1, 0.9), (0.1, 0.9), (-0.15, 0.8), (0.15, 0.9), (-0.1, 0.7), (0.1, 0.7):
        drawer.move_to((x, 0, z))
        for y in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            drawer.draw_to((x, y, z - math.sin(y * math.pi) * sag))
        drawer.draw_to((x, 1, z))

    wires = drawer.create(False)
    del drawer

    resistance = 1.0

    def __init__(self, world, origin, target):
        self.world = world
        self.origin = origin
        self.target = target

        # If placed is false, then self.target does not know about self yet.
        self.placed = False

        self.path = self.world.root.attach_new_node(copy(self.wires))
        self.path.set_light_off(1)
        self.path.set_color_scale((0.05, 0.05, 0.05, 1))

        debug_label_text = core.TextNode("debug_label")
        debug_label_text.set_card_color((1, 0, 0, 1))
        debug_label_text.set_card_as_margin(0.5, 0.5, 0.5, 0.5)
        debug_label_text.set_align(core.TextNode.A_center)
        self.debug_label = self.world.root.attach_new_node(debug_label_text)
        pos = (self.origin.pos + self.target.pos) * 0.5
        self.debug_label.set_pos(pos[0], pos[1], 1)
        self.debug_label.set_scale(0.2)
        self.debug_label.set_light_off(1)
        self.debug_label.set_depth_write(False)
        self.debug_label.node().set_text("0 A")

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
        self.destroy()

    def finish_placement(self):
        assert not self.placed
        self.placed = True

        print("Finishing placement of {}".format(self))
        self.target.placed = True

    def destroy(self):
        if self.origin.connections.get(self.target) is self:
            del self.origin.connections[self.target]

        if self.target.connections.get(self.origin) is self:
            del self.target.connections[self.origin]

        self.origin.on_update()
        self.target.on_update()

        self.path.remove_node()
        self.debug_label.remove_node()

    def on_current_change(self, current):
        """Called to process an update in current flowing through."""

        power = current ** 2 * self.resistance
        self.debug_label.node().set_text("{:.1f} W".format(power))

        if power > 3:
            print("{} power exceeds {}, destroying".format(self, power))
            self.destroy()
        elif power > 2:
            self.path.set_color_scale((1, 3 - power, 0, 1))
        elif power > 1:
            self.path.set_color_scale((power - 1, 1, 0, 1))
        elif power > 0:
            self.path.set_color_scale((0, power, 0, 1))
        else:
            self.path.set_color_scale((0.05, 0.05, 0.05, 1))


    def on_update(self):
        """Called when position information of neighbours changes."""

        self.path.set_pos(self.origin.x, self.origin.y, 0)
        self.path.look_at(self.target.x, self.target.y, 0)
        self.path.set_sy((self.target.root.get_pos() - self.origin.root.get_pos()).length())

        pos = (self.origin.pos + self.target.pos) * 0.5
        self.debug_label.set_pos(pos[0] + -0.5, pos[1] + -1, 1.5)
