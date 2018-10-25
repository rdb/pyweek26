from panda3d import core

from . import constructs, constants

import math
import numpy
import random


class World(object):
    def __init__(self):
        self.root = core.NodePath("world")

        cm = core.CardMaker("card")
        cm.set_frame(-50, 50, -50, 50)
        self.plane_model = self.root.attachNewNode(cm.generate())
        self.plane_model.look_at(0, 0, -1)

        mat = core.Material()
        #mat.diffuse = (218.0/255.0, 234.0/255.0, 182.0/255.0, 1)
        mat.diffuse = (181.0/255.0, 214.0/255.0, 111.0/255.0, 1)
        #mat.diffuse = (192.0/255.0, 239.0/255.0, 91.0/255.0, 1)
        mat.diffuse = (2, 2, 2, 1)
        mat.ambient = (1, 1, 1, 1)
        self.plane_model.set_material(mat)

        self.plane = core.Plane(0, 0, 1, 0)

        self.sun = core.PointLight("sun")
        self.sun.color = (0.9, 1, 0.8, 1)
        self.sun.color = self.sun.color * 10000
        self.sun.attenuation = (1, 0, 1)
        self.sun_path = self.root.attach_new_node(self.sun)
        self.sun_path.set_pos(15, -8, 5)
        self.sun_path.set_pos(self.sun_path.get_pos() * 8)
        self.sun_path.reparent_to(self.root)
        self.root.set_light(self.sun_path)

        self.moon = core.PointLight("sun")
        self.moon.color = (243.0/255.0, 247.0/255.0, 173.0/255.0, 1)
        #self.moon.color = (1, 0.5, 0.5, 1)
        self.moon.color = self.moon.color * 10000
        self.moon.attenuation = (1, 0, 1)
        self.moon_path = self.root.attach_new_node(self.moon)
        self.moon_path.set_pos(-20, 10, 6)
        self.moon_path.set_pos(self.moon_path.get_pos() * 8)
        self.moon_path.reparent_to(self.root)
        self.root.set_light(self.moon_path)

        #self.sun = core.DirectionalLight("sun")
        #self.sun.direction = (1, -1, -0.5)
        #self.sun.color = (0.5, 1, 1, 1)
        ##self.sun.color = self.sun.color * 300
        #self.sun_path = self.root.attach_new_node(self.sun)
        #self.sun_path.set_pos(20, -10, 3)
        #self.sun_path.reparent_to(self.root)
        #self.root.set_light(self.sun_path)

        #self.moon = core.DirectionalLight("sun")
        #self.moon.direction = (-0.5, 1.5, -0.4)
        #self.moon.color = (1, 0.5, 0.5, 1)
        ##self.moon.color = self.moon.color * 300
        #self.moon_path = self.root.attach_new_node(self.moon)
        #self.moon_path.set_pos(-20, 10, 3)
        #self.moon_path.reparent_to(self.root)
        #self.root.set_light(self.moon_path)

        self.towns = []
        self.pylons = set()

        # Grid prevents building towns at already occupied places.
        self.grid = numpy.zeros((8, 8), dtype=int)

        # Build generator.  Block off everything in the immediate vicinity.
        x = 3
        y = 4
        self.grid[x][y] = 1
        self.grid[x+1][y] = 1
        self.grid[x-1][y] = 1
        self.grid[x][y-1] = 1
        self.grid[x+1][y-1] = 1
        self.grid[x-1][y-1] = 1
        self.grid[x][y+1] = 1
        self.grid[x+1][y+1] = 1
        self.grid[x-1][y+1] = 1
        x -= self.grid.shape[0] / 2
        y -= self.grid.shape[1] / 2
        self.gen = constructs.Generator(self, (x * constants.town_spacing, y * constants.town_spacing), "Power Plant")
        self.gen.placed = True

        # Build one town at a fixed location.
        self.sprout_town(grid_pos=(5, 4), seed=5)

        # And one at an arbitrary, but close spot.
        second_town_spots = [(2, 3), (4, 5), (2, 5), (5, 3), (3, 2)]
        self.sprout_town(grid_pos=random.choice(second_town_spots))

        # Draw grid?
        drawer = core.LineSegs()
        #drawer.set_color((0.05, 0.05, 0.05, 1))
        drawer.set_thickness(1)

        min_x = self.grid.shape[0] * -3
        max_x = self.grid.shape[0] * 3
        min_y = self.grid.shape[1] * -3
        max_y = self.grid.shape[1] * 3

        for x in range(min_x, max_x):
            drawer.move_to((x, min_y, 0.001))
            drawer.draw_to((x, max_y, 0.001))

        for y in range(min_y, max_y):
            drawer.move_to((min_x, y, 0.001))
            drawer.draw_to((max_x, y, 0.001))

        debug_grid = self.root.attach_new_node(drawer.create(False))
        debug_grid.set_light_off(1)
        debug_grid.set_color_scale((0.35, 0.35, 0.35, 1))
        debug_grid.show()

    def construct_pylon(self):
        """Call this to construct additional pylons."""

        pylon = constructs.Pylon(self, (0, 0), "Pylon")
        self.pylons.add(pylon)
        return pylon

    def sprout_town(self, grid_pos=None, seed=None):
        if grid_pos is not None:
            x, y = grid_pos
        else:
            x = random.randint(0, self.grid.shape[0] - 1)
            y = random.randint(0, self.grid.shape[1] - 1)
            while self.grid[x][y] != 0:
                x = random.randint(0, self.grid.shape[0] - 1)
                y = random.randint(0, self.grid.shape[1] - 1)

        self.grid[x][y] = 1

        x -= self.grid.shape[0] / 2
        y -= self.grid.shape[1] / 2

        town = constructs.Town(self, (x * constants.town_spacing, y * constants.town_spacing), "City", seed=seed)
        town.placed = True
        self.towns.append(town)

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

            dist_sq = (construct.x - x) ** 2 + (construct.y - y) ** 2
            if dist_sq < closest_dist_sq and dist_sq < (construct.selection_distance ** 2):
                closest = construct
                closest_dist_sq = dist_sq

        return closest

    def calc_power(self, start):
        """Calculates the voltages at each node."""

        # Gather all nodes connected
        nodes = self.find_nodes(start)

        # Other pylons are disconnected.
        for node in self.pylons - nodes:
            node.on_disconnected()

        # So are towns that can't be reached by the generator.
        for town in self.towns:
            if town not in nodes:
                town.on_disconnected()

        # Prune nodes with only one connection, unless they provide or consume
        # power.
        discarded = -1
        while discarded != 0:
            discarded = 0
            for node in tuple(nodes):
                if isinstance(node, constructs.Pylon):
                    if len(set(node.neighbours) & nodes) < 2:
                        nodes.discard(node)
                        node.on_disconnected()
                        discarded += 1

        if len(nodes) <= 1:
            for node in nodes:
                node.on_disconnected()
            return

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

        # Determine the current through each wire based on the voltages.
        hot_wires = []
        for node, result in zip(nodes, results):
            for other, wire in list(node.connections.items()):
                if wire.placed and other in nodes:
                    # Calc current from voltage differential and resistance.
                    current = abs(result - results[nodes.index(other)]) / wire.resistance
                else:
                    current = 0

                wire.on_current_change(current)
                if wire.overheated:
                    hot_wires.append(wire)

            node.on_voltage_change(result)

        # Remove the hottest wire.
        if hot_wires:
            hot_wires.sort(key=lambda wire:-wire.heat)
            print("Removing overheated wire {}".format(hot_wires[0]))
            hot_wires[0].destroy()

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
