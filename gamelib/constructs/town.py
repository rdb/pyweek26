from panda3d import core

from ..construct import Construct


class Town(Construct):
    def __init__(self, world, pos, name):
        Construct.__init__(self, world, pos, name)
        self.size = 1

        model = loader.load_model("jack")
        model.reparent_to(self.root)
        model.set_scale(1)
        model.set_color_off(1)

    def _update_label(self):
        self.label.node().set_text("{}: {:.0f} MW".format(self.name, self.size))

    def grow(self, dt):
        self.size += dt
        self._update_label()
