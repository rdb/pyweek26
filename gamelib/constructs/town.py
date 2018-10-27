from panda3d import core

from ..construct import Construct
from .. import constants

import math
import numpy


category_names = [
    "dwelling",
    "hamlet",
    "village",
    "village",
    "village",
    # 50 MW
    "town", "town", "town", "town", "town",
    # 100 MW
    "city", "city", "city", "city", "city",
    "city", "city", "city", "city", "city",
    "city", "city", "city", "city", "city",
    # 250 MW
    "metropolis",
]

dist_matrix = numpy.zeros((5, 5))
for x in range(5):
    for y in range(5):
        dist = math.sqrt((x - 2) ** 2 + (y - 2) ** 2)
        dist /= 2.8284271247461903
        dist = 1 - dist
        dist **= 2
        dist *= 4
        dist_matrix[x, y] = dist


class Town(Construct):

    # We make the last connection point to a town inherently stronger.
    wire_conductance = 3

    def __init__(self, world, pos, name, placed=False):
        Construct.__init__(self, world, pos, name)
        self.size = 1
        self.powered = False
        self.name = "dwelling"
        self.placed = placed

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

        # Make this city unique.
        self.random_offsets = numpy.random.random_sample((5, 5)) - 0.5
        self.random_choices = numpy.random.randint(2, size=(5, 5))
        self.random_orients = numpy.random.randint(4, size=(5, 5))

        self.city = self.root.attach_new_node("city")
        self._rebuild_city()

        attach = self.root.attach_new_node("attach")
        attach.set_z(0.2)
        self.attachments.append(attach)

        self.power_off()

    @property
    def power(self):
        return 10 * (self.size ** 0.85)

    @property
    def resistance(self):
        return (230 ** 2) / self.power

    @property
    def current(self):
        if not self.powered:
            return 0
        return 230 / self.resistance

    def power_on(self):
        # Turn on lights
        self.powered = True
        self.window_mat.emission = self.window_emit
        self.city.set_color_scale((1.5, 1.5, 1.5, 1))

        self._update_label()

    def power_off(self):
        # Turn off lights
        self.powered = False
        self.window_mat.emission = (0, 0, 0, 1)
        self.city.set_color_scale((1, 1, 1, 1))

        self._update_label()

    def on_voltage_change(self, voltage):
        if not self.powered:
            self.power_on()

        Construct.on_voltage_change(self, voltage)

    def on_disconnected(self):
        if self.powered:
            self.power_off()

        Construct.on_disconnected(self)

    def _update_label(self):
        if not self.placed:
            return
        if self.powered:
            name = self.name[0].upper() + self.name[1:]
            self.set_label(text="{}\n{:.0f} MW".format(name, self.power * 0.1))
        else:
            self.set_label(text="This {} is not\ngetting power!".format(self.name), important=True)

    def _rebuild_city(self):
        self.city.children.detach()

        for x in range(5):
            for y in range(5):
                which = self.grid[x][y]
                if which > 0:
                    tiles = self.tiles_by_size[which - 1]
                    tile = tiles[self.random_choices[x, y]].copy_to(self.city)
                    tile.set_pos(x - 2, y - 2, 0)
                    tile.set_h(90 * self.random_orients[x, y])
                    tile.set_scale(0.5)

    def grow(self, dt):
        if not self.placed:
            return

        if self.powered:
            self.size += dt
        else:
            self.size = max(1, self.size - dt * constants.town_shrink_rate)

        #growth = 4.5 - (500 / (self.size + (500 / 4.5)))
        growth = 8 - (1000 / (self.size * 0.4 + (1000 / 8)))

        # Compute new tiles.
        new_grid = numpy.zeros((5, 5), dtype=int)
        new_grid = numpy.rint((dist_matrix + self.random_offsets) * growth, out=new_grid, casting='unsafe')
        new_grid = numpy.clip(new_grid, 0, 4)

        # Always a house in the center.
        if new_grid[2][2] < 1:
            new_grid[2][2] = 1

        if (new_grid != self.grid).any():
            self.grid = new_grid
            self._rebuild_city()

        # Make up a nice name for it... calling a single building a "city"
        # seems so silly.
        category = min(int(self.size // 10), len(category_names) - 1)
        self.name = category_names[category]

        self._update_label()
