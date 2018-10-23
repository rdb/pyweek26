from panda3d import core

from ..construct import Construct


class Town(Construct):
    def __init__(self, world, pos, name):
        Construct.__init__(self, world, pos, name)
        self.size = 1
        self.powered = False

        model = loader.load_model("jack")
        model.reparent_to(self.root)
        model.set_scale(1)
        model.set_color_off(1)

    @property
    def resistance(self):
        power = self.size * 10
        return (230 ** 2) / power

    @property
    def current(self):
        if not self.powered:
            return 0
        power = self.size * 10
        return 230 / self.resistance

    def on_power_on(self):
        self.powered = True

    def on_power_off(self):
        self.powered = False

    def _update_label(self):
        self.label.node().set_text("{}: {:.0f} MW".format(self.name, self.size))

    def grow(self, dt):
        if self.powered:
            self.size += dt
        self._update_label()
