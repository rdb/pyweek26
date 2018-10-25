from panda3d import core

from ..construct import Construct
import random


class Generator(Construct):

    allow_wire_sag = False

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
        self.attachments = self.attachments[:4]

    def _update_label(self):
        self.label.node().set_text("{}\n{:.0f} MW".format(self.name, self.capacity))
