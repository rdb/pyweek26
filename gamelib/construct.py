from panda3d import core
from direct.interval.IntervalGlobal import LerpPosInterval, Sequence

from .wire import PowerWire
from . import constants


class Construct(object):

    allow_wire_sag = True
    selection_distance = 2
    upgradable = False
    erasable = False
    wire_conductance = 1

    def __init__(self, world, pos, name):
        self.world = world
        self.x, self.y = pos

        self.name = name

        # Starts out as a ghost.
        self.placed = False
        self.upgraded = False

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
        self.label.set_depth_test(False)
        self.label.set_bin('fixed', 10)
        self.label.set_billboard_point_eye()
        self.label.hide()

        # Set to show label even if not highlighted.
        self.__label_text = ''
        self.__label_important = False
        self.__label_effective_important = False
        self.highlight_mode = None

        cm = core.CardMaker("arrow")
        cm.set_frame(-1, 1, -1, 1)
        arrow = self.label.attach_new_node(cm.generate())
        arrow.set_r(45)
        arrow.set_x(0.7)
        arrow.set_z(-1.5)
        arrow.set_scale(0.8)
        arrow.set_color(label_text.card_color)
        arrow.set_depth_write(False)
        arrow.set_depth_test(False)
        arrow.set_bin('fixed', 0)
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
            self.debug_label.set_depth_test(False)
            self.debug_label.set_bin('fixed', 0)
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

    def finish_placement(self):
        self.placed = True

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

    def set_label(self, text, important=False):
        self.__label_text = text
        self.__label_important = important

        if self.highlight_mode not in ('connect', 'erase', 'placing', 'upgrade', 'upgrade-no-money', 'too-far', 'already-connected', 'bad-terrain'):
            self._do_set_label(text, important)

    def _do_set_label(self, text, important):
        self.label.node().set_text(text)

        if important is not self.__label_effective_important:
            self.__label_effective_important = important
            if important or self.highlight_mode is not None:
                self.label.show()
            else:
                self.label.hide()

            if important:
                self.label_bob.loop()
                self.label.node().set_card_color(constants.important_label_color)
                self.arrow.set_color(constants.important_label_color)
            else:
                self.label_bob.finish()
                self.label.node().set_card_color(constants.normal_label_color)
                self.arrow.set_color(constants.normal_label_color)

    @property
    def highlighted(self):
        return self.highlight_mode is not None

    def highlight(self, mode):
        if self.highlight_mode == mode:
            return

        self.label.show()
        self.highlight_mode = mode
        self.root.set_color_scale((2, 2, 2, 1))

        if mode == 'connect':
            effective_text = 'Click to connect\nthis {}'.format(self.name)
            effective_important = False
        elif mode == 'erase':
            if self.erasable:
                effective_text = 'Click to erase\nthis {}'.format(self.name)
                effective_important = False
            else:
                effective_text = "Only pylons can\nbe erased!"
                effective_important = True
        elif mode == 'placing':
            effective_text = 'Click to place a\npylon here'
            effective_important = False
        elif mode == 'upgrade' or mode == 'upgrade-no-money':
            if not self.upgradable:
                effective_text = "Only pylons can\nbe upgraded!"
                effective_important = True
            elif self.upgraded:
                effective_text = "Already\nupgraded!"
                effective_important = True
            elif mode == 'upgrade-no-money':
                effective_text = "You need more\nupgrade points!"
                effective_important = True
            else:
                effective_text = "Click to upgrade\nthis {}".format(self.name)
                effective_important = False
        elif mode == 'yay-upgraded':
            effective_text = "Upgraded\nsuccessfully!"
            effective_important = False
        elif mode == 'too-far':
            effective_text = "Too far! Build\npylons closer."
            effective_important = True
        elif mode == 'already-connected':
            effective_text = "Already\nconnected!"
            effective_important = True
        elif mode == 'bad-terrain':
            effective_text = "Cannot build\non bad terrain!"
            effective_important = True
        #elif mode == 'self-connect':
        #    effective_text = "Cannot connect\nto itself!"
        #    effective_important = True
        else:
            effective_text = self.__label_text
            effective_important = self.__label_important

        self._do_set_label(effective_text, important=effective_important)

    def unhighlight(self):
        self.highlight_mode = None
        if not self.__label_important:
            self.label.hide()
        else:
            self._do_set_label(self.__label_text, self.__label_important)
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
