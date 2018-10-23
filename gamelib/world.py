from panda3d import core

from . import constructs

import math
import numpy


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
        self.towns[0].powered = True

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

    def calc_power(self, a):
        # Gather all nodes connected
        nodes = self.find_nodes(a)

        # Prune nodes with only one connection, unless they provide or consume
        # power.
        discarded = -1
        while discarded != 0:
            discarded = 0
            for node in tuple(nodes):
                if isinstance(node, constructs.Pylon):
                    if len(set(node.neighbours) & nodes) < 2:
                        nodes.discard(node)
                        discarded += 1

        # Now create a linear system for Modified Nodal Analysis.
        nodes = tuple(nodes)
        matrix = []
        ords = []

        for i, node in enumerate(nodes):
            row = [0] * (len(nodes) + 1)

            for node2 in node.neighbours:
                if node2 in nodes:
                    j = nodes.index(node2)
                    row[i] += 1
                    row[j] += -1

            if isinstance(node, constructs.Generator):
                # Generator current is an unknown.
                row[-1] = 1

            matrix.append(row)

            if isinstance(node, constructs.Town):
                # Town: consumes 3A.
                ords.append(-node.current)
            else:
                ords.append(0)

        # Finally, one more equation: all the generators combined produce
        # enough current to satisfy all the towns.
        row = [0] * (len(nodes) + 1)
        row[-1] = 1
        ords.append(0)
        for i, node in enumerate(nodes):
            if isinstance(node, constructs.Town):
                if node.powered:
                    row[i] = 1.0 / node.resistance
                else:
                    row[i] = 0

        matrix.append(row)

        try:
            results = numpy.linalg.solve(matrix, ords)
        except:
            # Shouldn't happen, but better than nothing?
            results = numpy.linalg.lstsq(matrix, ords)[0]

        for node, result in zip(nodes, results):
            for other, wire in list(node.connections.items()):
                if other in nodes:
                    current = abs(result - results[nodes.index(other)])
                else:
                    current = 0

                wire.on_current_change(current)

            node.on_voltage_change(result)

    def find_nodes(self, start, visited=frozenset()):
        nodes = set(visited)
        nodes.add(start)

        for node in start.neighbours:
            if node not in visited:
                nodes |= self.find_nodes(node, nodes)

        return nodes

    def step(self, dt):
        """Runs one iteration of the game logic."""

        self.calc_power(self.gen)

        for town in self.towns:
            town.grow(dt)
