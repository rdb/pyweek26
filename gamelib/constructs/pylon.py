from panda3d import core

from ..construct import Construct


class Pylon(Construct):

    selection_distance = 1

    def __init__(self, world, pos, name):
        Construct.__init__(self, world, pos, name)

        self.placed = False
        self.stashed = False

        self.model = loader.load_model("pylon")
        self.model.reparent_to(self.root)
        self.model.flatten_strong()
        #self.model.set_scale(0.5, 0.1, 1)
        self.model.set_color_off(1)

        self.attachments = []
        #for x, z in (-0.1, 0.9), (-0.1, 0.7), (-0.15, 0.8), (0, 1), (0.15, 0.9), (0.1, 0.7), (0.1, 0.9):
        for x, z in (-0.25, 0.85), (-0.15, 1.05), (0.15, 1.05), (0.25, 0.85):
        #for x, z in (-0.25, 0.65), (-0.13, 1), (0.13, 1), (0.25, 0.65):
            attach = self.model.attach_new_node("attach")
            attach.set_pos(x, 0, z)
            self.attachments.append(attach)

    def __del__(self):
        print("Destroying pylon {}".format(self))

    def stash(self):
        self.world.pylons.discard(self)
        self.root.detach_node()
        self.stashed = True

    def unstash(self):
        self.stashed = False
        self.world.pylons.add(self)
        self.root.reparent_to(self.world.root)

    def _update_label(self):
        self.label.node().set_text("{}: {:.0f} MW".format(self.name, self.size))

    def on_update(self):
        """Updates state based on position information of neighbours."""

        if len(self.connections) == 0:
            # It's orphaned, so we let it go.
            if not self.stashed:
                print("Orphaned pylon {}".format(self))
                self.stash()
            return
        else:
            self.unstash()

        #TODO: different algo: grab closest two angle, between two connections,
        # then reduce

        heading = 0
        for wire in self.connections.values():
            #print(wire.path.get_h())
            heading += wire.angle % 360.0

        h = heading / len(self.connections)

        if len(self.connections) == 2:
            wire1, wire2 = self.connections.values()
            if abs(wire1.vector.signed_angle_deg(wire2.vector)) > 90:
                h += 90

        prev_h = self.model.get_h()
        if h != prev_h:
            self.model.set_h(h)

            # Update wires
            for wire in self.connections.values():
                wire.on_update()

    def position_within_radius_of(self, x, y, other, max_distance):
        """Called while it has still one connection."""

        # Limit to max wire length
        if max_distance is not None:
            dir = core.Point2(x, y) - other.pos
            if dir.length_squared() > max_distance ** 2:
                x, y = other.pos + dir.normalized() * max_distance

        #TODO: limit angle?

        # This also calls on_update.
        Construct.position(self, x, y)
