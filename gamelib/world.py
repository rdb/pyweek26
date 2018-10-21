from panda3d import core

from . import constructs

import math


class World(object):
    def __init__(self):
        self.root = core.NodePath("world")

        cm = core.CardMaker("card")
        cm.set_frame(-50, 50, -50, 50)
        self.plane_model = self.root.attachNewNode(cm.generate())
        self.plane_model.look_at(0, 0, -1)

        mat = core.Material()
        mat.diffuse = (1, 1, 1, 1)
        mat.ambient = (1, 1, 1, 1)
        self.plane_model.set_material(mat)

        self.plane = core.Plane(0, 0, 1, 0)

        self.sun = core.PointLight("sun")
        self.sun.color = (0.5, 1, 1, 1)
        self.sun.color = self.sun.color * 300
        self.sun.attenuation = (1, 0, 1)
        self.sun_path = self.root.attach_new_node(self.sun)
        self.sun_path.set_pos(20, -10, 3)
        self.sun_path.reparent_to(self.root)
        self.root.set_light(self.sun_path)

        self.moon = core.PointLight("sun")
        self.moon.color = (1, 0.5, 0.5, 1)
        self.moon.color = self.moon.color * 300
        self.moon.attenuation = (1, 0, 1)
        self.moon_path = self.root.attach_new_node(self.moon)
        self.moon_path.set_pos(-20, 10, 3)
        self.moon_path.reparent_to(self.root)
        self.root.set_light(self.moon_path)

        self.towns = []
        self.pylons = set()

        self.add_town((0, -2), "Oldtown")
        self.add_town((2, 3), "Newville")

        self.gen = constructs.Generator(self, (-4, 3), "Nuclear")
        self.gen.placed = True

    def construct_pylon(self):
        """Call this to construct additional pylons."""

        pylon = constructs.Pylon(self, (0, 0), "Pylon")
        self.pylons.add(pylon)
        return pylon

    def add_town(self, pos, name):
        town = constructs.Town(self, pos, name)
        town.placed = True
        self.towns.append(town)

    def pick_closest_construct(self, x, y, max_radius=None):
        """Returns the Construct that falls within the given radius of the given position."""

        closest = None
        closest_dist_sq = float("inf")
        if max_radius is not None:
            closest_dist_sq = max_radius ** 2

        for construct in self.towns + [self.gen] + list(self.pylons):
            if not construct.placed:
                continue

            dist_sq = math.sqrt((construct.x - x) ** 2 + (construct.y - y) ** 2)
            if dist_sq < closest_dist_sq:
                closest = construct
                closest_dist_sq = dist_sq

        return closest

    def step(self, dt):
        """Runs one iteration of the game logic."""

        for town in self.towns:
            town.grow(dt)
