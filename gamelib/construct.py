from panda3d import core
from direct.interval.IntervalGlobal import LerpPosInterval, Sequence

from .wire import PowerWire
from . import constants


class Construct(object):

    allow_wire_sag = True
    selection_distance = 2

    def __init__(self, world, pos, name):
        self.world = world
        self.x, self.y = pos

        self.name = name

        # Starts out as a ghost.
        self.placed = False

        self.root = world.root.attach_new_node(name)
        self.root.set_pos(pos[0], pos[1], 0)
        self.attachments = []

        label_text = core.TextNode("label")
        label_text.set_align(core.TextNode.A_left)
        label_text.set_card_color(constants.normal_label_color)
        label_text.set_card_as_margin(0.5, 0.5, 0.5, 0.5)

        self.label = self.root.attach_new_node(label_text)
        self.label.set_pos(0.0, 0, 1.5)
        self.label.set_scale(0.2)
        self.label.set_light_off(1)
        self.label.set_color_scale_off(1)
        self.label.set_depth_write(False)
        self.label.set_billboard_point_eye()
        self.label.hide()

        # Set to show label even if not highlighted.
        self.__label_important = False
        self.highlighted = False

        cm = core.CardMaker("arrow")
        cm.set_frame(-1, 1, -1, 1)
        arrow = self.label.attach_new_node(cm.generate())
        arrow.set_r(45)
        arrow.set_x(0.7)
        arrow.set_z(-1.5)
        arrow.set_scale(0.8)
        arrow.set_color(label_text.card_color)
        self.arrow = arrow

        self.label_bob = Sequence(
            self.label.posInterval(constants.label_bob_time, (0.0, 0, 1.7), bakeInStart=True, blendType='easeInOut'),
            self.label.posInterval(constants.label_bob_time, (0.0, 0, 1.5), bakeInStart=True, blendType='easeInOut'),
        )

        self.connections = {}

        if constants.show_debug_labels:
            debug_label_text = core.TextNode("debug_label")
            debug_label_text.set_card_color((0, 0.5, 0, 1))
            debug_label_text.set_card_as_margin(0.5, 0.5, 0.5, 0.5)
            self.debug_label = self.root.attach_new_node(debug_label_text)
            self.debug_label.set_pos(-0.5, -1, 1.5)
            self.debug_label.set_scale(0.2)
            self.debug_label.set_light_off(1)
            self.debug_label.set_color_scale_off(1)
            self.debug_label.set_depth_write(False)
            self.debug_label.node().set_text("0V")

    def __repr__(self):
        return "<{} \"{}\">".format(type(self).__name__, self.name)

    @property
    def pos(self):
        return core.Point2(self.x, self.y)

    @property
    def neighbours(self):
        return [node for node, wire in self.connections.items() if wire.placed]

    def destroy(self):
        for wire in list(self.connections.values()):
            wire.destroy()

        assert not self.connections
        self.root.remove_node()

    def connect_to(self, other):
        if other in self.connections:
            return self.connections[other]

        wire = PowerWire(self.world, self, other)
        other.connections[self] = wire
        self.connections[other] = wire
        return wire

    def position(self, x, y):
        self.root.set_pos(x, y, 0)
        self.x = x
        self.y = y
        for wire in self.connections.values():
            wire.on_update()
            if wire.origin is self:
                wire.target.on_update()
            elif wire.target is self:
                wire.origin.on_update()
        self.on_update()

    @property
    def label_important(self):
        return self.__label_important

    @label_important.setter
    def label_important(self, setting):
        if setting != self.__label_important:
            self.__label_important = setting
            if setting or self.highlighted:
                self.label.show()
            else:
                self.label.hide()

            if setting:
                self.label_bob.loop()
                self.label.node().set_card_color(constants.important_label_color)
                self.arrow.set_color(constants.important_label_color)
            else:
                self.label_bob.finish()
                self.label.node().set_card_color(constants.normal_label_color)
                self.arrow.set_color(constants.normal_label_color)

    def highlight(self):
        self.highlighted = True
        self.label.show()
        self.root.set_color_scale((2, 2, 2, 1))

    def unhighlight(self):
        self.highlighted = False
        if not self.__label_important:
            self.label.hide()
        self.root.clear_color_scale()

    def on_voltage_change(self, voltage):
        """Called with the voltage of the node if it's connected."""

        if constants.show_debug_labels:
            self.debug_label.node().set_text("{:.1f} V".format(voltage))

    def on_disconnected(self):
        """Called instead of on_voltage_change if it's not connected."""

        if constants.show_debug_labels:
            self.debug_label.node().set_text("X")

    def on_update(self):
        """Updates state based on position information of neighbours."""
        pass
