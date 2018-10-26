from panda3d import core

from ..construct import Construct
import random


class Generator(Construct):

    allow_wire_sag = False

    # Behaves like an upgraded pylon.
    wire_conductance = 3

    def __init__(self, world, pos, name):
        Construct.__init__(self, world, pos, name)
        self.capacity = 1

        model = loader.load_model("plant")
        model.reparent_to(self.root)
        #model.set_scale(2)
        #model.set_pos(-1, -1, -1)
        model.set_color_off(1)
        model.set_texture_off(1)

        self._update_label()

        self.attachments = list(model.find_all_matches("**/attachment.*"))
        random.shuffle(self.attachments)
        self.attachments = self.attachments[:6]

    def _update_label(self):
        if len(self.connections) > 0:
            self.set_label("{}\n{:.0f} MW".format(self.name, self.capacity))
        else:
            self.set_label("Click here to\nbegin a power line", important=True)

    def on_update(self):
        self._update_label()
