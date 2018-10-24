from panda3d import core

from ..construct import Construct

import random
import math
import numpy


class Town(Construct):
    def __init__(self, world, pos, name):
        Construct.__init__(self, world, pos, name)
        self.size = 1
        self.powered = False

        # Right now, we force a copy so we get a unique windowed material.
        city = loader.load_model("city.egg", noCache=True)
        self.tiles_by_size = [
            tuple(city.find_all_matches("**/tiny.*")),
            tuple(city.find_all_matches("**/small.*")),
            tuple(city.find_all_matches("**/medium.*")),
            tuple(city.find_all_matches("**/large.*")),
        ]
        for tiles in self.tiles_by_size:
            for tile in tiles:
                tile.set_pos(0, 0, 0)
                #tile.set_scale(0.5)
                #tile.flatten_strong()

        self.grid = numpy.zeros((5, 5), dtype=int)
        self.grid[2][2] = 1

        # We'll change the emit color when the lights go off.
        self.window_mat = city.find_material("window")
        self.window_mat.diffuse = (0.1, 0.1, 0.1, 1)
        self.window_emit = core.LVecBase4(self.window_mat.emission)

        # Create a random seed so this city will be unique.
        self.seed = random.random()

        self.city = self.root.attach_new_node("city")
        self._rebuild_city()

        self.on_power_off()

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
        self.window_mat.emission = self.window_emit

    def on_power_off(self):
        self.powered = False
        self.window_mat.emission = (0, 0, 0, 1)

    def _update_label(self):
        self.label.node().set_text("{}: {:.0f} MW".format(self.name, self.size))

    def _rebuild_city(self):
        self.city.children.detach()

        r = random.Random()
        r.seed(self.seed)

        for x in range(5):
            for y in range(5):
                wh = r.choice((0, 1))
                rot = r.choice((0, 1, 2, 3))
                which = self.grid[x][y]
                if which > 0:
                    tiles = self.tiles_by_size[which - 1]
                    tile = tiles[wh].copy_to(self.city)
                    tile.set_pos(x - 2, y - 2, 0)
                    tile.set_h(90 * rot)
                    tile.set_scale(0.5)

    def grow(self, dt):
        if self.powered:
            self.size += dt

        coeff = 400
        growth = 4 - (coeff / (self.size + (coeff / 4)))

        # Compute new tiles.
        new_grid = numpy.zeros((5, 5), dtype=int)
        for x in range(5):
            for y in range(5):
                r = random.Random()
                r.seed(x + y * 5 - self.seed)
                dist = math.sqrt((x - 2) ** 2 + (y - 2) ** 2)
                dist /= 2.8284271247461903
                dist = 1 - dist
                dist **= 2
                dist *= 4
                dist += (r.random() - 0.5)
                dist *= growth
                new_grid[x][y] = max(min(round(dist), 4), 0)

        # Always a house in the center.
        if new_grid[2][2] < 1:
            new_grid[2][2] = 1

        if (new_grid != self.grid).any():
            self.grid = new_grid
            self._rebuild_city()

        self._update_label()
