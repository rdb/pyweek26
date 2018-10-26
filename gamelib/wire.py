from panda3d import core
from copy import copy
import math

from . import constants

acosh_scale = math.acosh(2) * 2


class PowerWire(object):
    resistance = 1.0

    def __init__(self, world, origin, target):
        self.world = world
        self.origin = origin
        self.target = target

        self.heat = 0

        # If placed is false, then self.target does not know about self yet.
        self.placed = False

        self.path = self.world.root.attach_new_node(core.GeomNode("wires"))
        self.path.set_light_off(1)
        self.path.set_color_scale((0.05, 0.05, 0.05, 1))

        if constants.show_debug_labels:
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
        r = "{!r}--{!r}".format(self.origin, self.target)
        if self.heat > 0.0:
            r += " (HOT:{:.1f})".format(self.heat)
        return r

    def _draw_lines(self):
        self.path.node().remove_all_geoms()

        drawer = core.LineSegs()
        #drawer.set_color((0.05, 0.05, 0.05, 1))
        drawer.set_thickness(constants.wire_thickness)

        origin_attachments = self.origin.attachments
        target_attachments = self.target.attachments

        # Don't cross the lines.
        if origin_attachments[0].get_quat(self.path).get_forward().dot(target_attachments[0].get_quat(self.path).get_forward()) < 0:
            target_attachments = tuple(reversed(target_attachments))

        sag = self.origin.allow_wire_sag and self.target.allow_wire_sag

        for i in range(max(len(origin_attachments), len(target_attachments))):
            from_point = origin_attachments[i % len(origin_attachments)].get_pos(self.path)
            to_point = target_attachments[i % len(target_attachments)].get_pos(self.path)

            # Interpolate.
            drawer.move_to(from_point)
            for t in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
                point = from_point * (1 - t) + to_point * t
                if sag:
                    point.z += constants.wire_sag * (math.cosh((t - 0.5) * acosh_scale) - 2)
                drawer.draw_to(point)
            drawer.draw_to(to_point)

        wires = drawer.create(self.path.node())

    @property
    def vector(self):
        return self.target.pos - self.origin.pos

    @property
    def angle(self):
        return -self.vector.signed_angle_deg((0, 1))

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

        if (self.origin.pos - to.pos).length_squared() > (constants.max_pylon_distance + to.selection_distance) ** 2:
            return False

        self.set_target(to)
        return True

    def set_target(self, to):
        """During placement, force connecting to this node."""
        assert to is not self.origin

        if self.target is not to:
            del self.target.connections[self.origin]
            del self.origin.connections[self.target]
            self.target.on_update()

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
        if constants.show_debug_labels:
            self.debug_label.remove_node()

    @property
    def overheated(self):
        return self.heat >= constants.max_wire_heat

    def on_current_change(self, current):
        """Called to process an update in current flowing through."""

        power = current ** 2 * self.resistance

        if constants.show_debug_labels:
            self.debug_label.node().set_text("{:.1f} W".format(power))

        if power > 2:
            # Start overheating.
            self.heat += min((power - 2), 1) * globalClock.dt
            self.path.set_color_scale((1, 0, 0, 1))
            #self.path.set_color_scale((1, 3 - power, 0, 1))
        elif power > 1:
            # Cool down.
            self.heat = max(self.heat - globalClock.dt, 0)
            self.path.set_color_scale((1, 2 - power, 2 - power, 1))
            #self.path.set_color_scale((power - 1, 1, 0, 1))
        elif power > 0:
            # Cool down faster.
            self.heat = max(self.heat - 2 * globalClock.dt, 0)
            self.path.set_color_scale((1, 1, 1, 1))
            #self.path.set_color_scale((0, power, 0, 1))
        else:
            self.heat = 0
            self.path.set_color_scale((0.05, 0.05, 0.05, 1))

    def on_update(self):
        """Called when position information of neighbours changes."""

        #self.path.set_pos(self.origin.x, self.origin.y, 0)
        #self.path.look_at(self.target.x, self.target.y, 0)
        #self.path.set_sy((self.target.root.get_pos() - self.origin.root.get_pos()).length())

        if constants.show_debug_labels:
            pos = (self.origin.pos + self.target.pos) * 0.5
            self.debug_label.set_pos(pos[0] + -0.5, pos[1] + -1, 1.5)

        self._draw_lines()
