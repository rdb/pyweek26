from panda3d import core

from .wire import PowerWire
from . import constants


class Construct(object):
    def __init__(self, world, pos, name):
        self.world = world
        self.x, self.y = pos

        self.name = name

        # Starts out as a ghost.
        self.placed = False

        self.root = world.root.attach_new_node(name)
        self.root.set_pos(pos[0], pos[1], 0)

        label_text = core.TextNode("label")
        #label_text.set_card_color((1, 0.6, 0.05, 1))
        label_text.set_card_color((1, 0.32, 0.04, 1))
        label_text.set_card_as_margin(0.5, 0.5, 0.5, 0.5)

        self.label = self.root.attach_new_node(label_text)
        self.label.set_pos(0.5, -1, 1.5)
        self.label.set_scale(0.2)
        self.label.set_light_off(1)
        self.label.set_depth_write(False)

        cm = core.CardMaker("arrow")
        cm.set_frame(-1, 1, -1, 1)
        arrow = self.label.attach_new_node(cm.generate())
        arrow.set_r(45)
        arrow.set_x(0.7)
        arrow.set_scale(0.8)
        arrow.set_color(label_text.card_color)

        self.connections = {}

    def __repr__(self):
        return "<{} \"{}\">".format(type(self).__name__, self.name)

    @property
    def pos(self):
        return core.Point2(self.x, self.y)

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

    def highlight(self):
        self.label.show()

    def unhighlight(self):
        self.label.hide()

    def on_update(self):
        """Updates state based on position information of neighbours."""
        pass
