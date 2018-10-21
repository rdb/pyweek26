from panda3d import core

from ..construct import Construct


class Generator(Construct):
    def __init__(self, world, pos, name):
        Construct.__init__(self, world, pos, name)
        self.capacity = 1

        model = loader.load_model("box")
        model.reparent_to(self.root)
        model.set_scale(2)
        model.set_pos(-1, -1, -1)
        model.set_color_off(1)
        model.set_texture_off(1)

        self._update_label()

    def _update_label(self):
        self.label.node().set_text("{}: {:.0f} MW".format(self.name, self.capacity))
