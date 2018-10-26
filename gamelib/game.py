from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from panda3d import core

from .world import World
from .panel import Panel
from . import constants

import math


class Game(ShowBase):
    def __init__(self):
        core.load_prc_file("config.prc")
        ShowBase.__init__(self)

        try:
            bold_font = loader.load_font("data/font/Roboto-Bold.ttf")
        except:
            print("Could not load Roboto-Bold.ttf")
            bold_font = None

        self.set_background_color((0.02, 0.01, 0.01, 1))

        self.world = World()
        self.world.root.reparent_to(self.render)

        self.world.root.set_shader_auto(True)
        self.world.root.set_antialias(core.AntialiasAttrib.M_auto)

        # Set up camera
        self.disable_mouse()
        self.pivot = self.world.root.attach_new_node("pivot")
        self.camera_target = self.pivot.attach_new_node("target")
        self.camera.reparent_to(self.camera_target)
        self.camera.set_pos(0, -15, 15)
        self.camera.look_at(0, 0, 0)

        self.lens = self.cam.node().get_lens(0)
        self.lens.focal_length = 0.4
        self.lens.set_fov(50)

        self.pivot.set_h(20)

        self.clock = core.ClockObject.get_global_clock()
        self.task_mgr.add(self.__task)

        # Create UI
        self.panel = Panel(self.a2dBottomLeft)
        self.panel.add_button("1. Connect", icon=0xf5ee, callback=self.on_switch_mode, arg='connect', shortcut='1')
        self.panel.add_button("2. Upgrade", icon=0xf102, callback=self.on_switch_mode, arg='upgrade', shortcut='2')
        self.panel.add_button("3. Erase", icon=0xf12d, callback=self.on_switch_mode, arg='erase', shortcut='3')

        self.unpowered_button = DirectButton(parent=base.a2dTopLeft, pos=(0.13, 0, -0.15), text='\uf071', text_font=self.panel.icon_font, text_scale=0.1, text_fg=constants.important_label_color, relief=None, command=self.cycle_unpowered_town)
        self.unpowered_button.hide()
        self.unpowered_text = OnscreenText(parent=self.unpowered_button, pos=(0, -0.05), font=bold_font, text='Press tab', fg=constants.important_label_color, scale=0.04)
        self.next_unpowered_index = 0

        self.mode = 'connect'

        self.accept('mouse1', self.on_click)
        self.accept('mouse3', self.cancel_placement)
        self.accept('shift-s', self.screenshot)
        self.accept('escape', self.cancel_placement)
        self.accept('shift-h', self.highlight_all)
        self.accept('shift-l', self.render.ls)
        self.accept('shift-p', self.create_stats)
        self.accept('shift-t', self.spawn_town)
        self.accept('tab', self.cycle_unpowered_town)
        self.accept('wheel_up', self.on_zoom, [1.0])
        self.accept('wheel_down', self.on_zoom, [-1.0])

        self.highlighted = None
        self.pylon = None
        self.placing_wire = None
        self.made_first_connection = False

        # Initial mode
        self.panel.select_button(0)

    def __task(self, task):
        self.world.step(self.clock.dt)

        if all(town.powered for town in self.world.towns):
            self.unpowered_button.hide()

        elif self.made_first_connection:
            # Show only if we are not looking straight at the town.
            cam_pos = self.camera_target.get_pos(self.world.root).xy
            if any((town.pos - cam_pos).length_squared() > 25 for town in self.world.towns if not town.powered):
                self.unpowered_button.show()
            else:
                self.unpowered_button.hide()

        elif any(town.powered for town in self.world.towns):
            self.made_first_connection = True

        mw = self.mouseWatcherNode

        # Keyboard controls
        hor = mw.is_button_down('arrow_right') - mw.is_button_down('arrow_left')
        if hor != 0:
            speed = constants.camera_speed * self.camera.get_pos().length_squared() ** 0.2
            movement = hor * speed * self.clock.dt
            abs_pos = self.world.root.get_relative_point(self.camera_target, (movement, 0, 0))
            abs_pos.x = min(max(abs_pos.x, -20), 20)
            abs_pos.y = min(max(abs_pos.y, -20), 20)
            self.camera_target.set_pos(self.world.root, abs_pos)

        ver = mw.is_button_down('arrow_up') - mw.is_button_down('arrow_down')
        if ver != 0:
            speed = constants.camera_speed * self.camera.get_pos().length_squared() ** 0.2
            movement = ver * speed * self.clock.dt
            abs_pos = self.world.root.get_relative_point(self.camera_target, (0, movement, 0))
            abs_pos.x = min(max(abs_pos.x, -20), 20)
            abs_pos.y = min(max(abs_pos.y, -20), 20)
            self.camera_target.set_pos(self.world.root, abs_pos)

        # Mouse controls
        construct = None
        if mw.has_mouse():
            mpos = mw.get_mouse()
            pos3d = core.Point3()
            near = core.Point3()
            far = core.Point3()
            self.lens.extrude(mpos, near, far)
            if self.world.plane.intersects_line(pos3d,
                self.world.root.get_relative_point(self.camera, near),
                self.world.root.get_relative_point(self.camera, far)):

                # Which construct are we hovering over?
                construct = self.world.pick_closest_construct(pos3d[0], pos3d[1])
                if construct is self.pylon:
                    construct = None

                if self.pylon is not None:
                    self.pylon.position_within_radius_of(pos3d[0], pos3d[1], self.placing_wire.origin, constants.max_pylon_distance)

        if self.highlighted is not None and construct is not self.highlighted:
            if self.pylon is not self.highlighted:
                self.highlighted.unhighlight()
            self.highlighted = None

        if construct is not None:
            self.highlighted = construct

            if self.placing_wire:
                if not self.placing_wire.try_set_target(construct):
                    self.placing_wire.set_target(self.pylon)

                    if construct is None:
                        construct.highlight("placing")
                    elif construct is self.placing_wire.origin:
                        construct.highlight("self-connect")
                    elif construct in self.placing_wire.origin.connections and self.placing_wire.origin.connections[construct].placed:
                        construct.highlight("already-connected")
                    else:
                        construct.highlight("too-far")
                else:
                    construct.highlight("connect")

            elif not construct.highlighted:
                construct.highlight("normal")

        elif self.placing_wire:
            self.placing_wire.set_target(self.pylon)

        return task.cont

    def spawn_town(self):
        self.world.sprout_town()

    def on_zoom(self, amount):
        lens = self.lens
        self.camera.set_pos(self.camera.get_pos() * (1.0 + amount * 0.1))

        dist_sq = self.camera.get_pos().length_squared()
        if dist_sq > constants.camera_max_zoom ** 2:
            self.camera.set_pos(self.camera.get_pos() * constants.camera_max_zoom / math.sqrt(dist_sq))

        elif dist_sq < constants.camera_min_zoom ** 2:
            self.camera.set_pos(self.camera.get_pos() * constants.camera_min_zoom / math.sqrt(dist_sq))

    def on_switch_mode(self, mode):
        self.cancel_placement()

        if self.highlighted:
            self.highlighted.unhighlight()
            self.highlighted = None

        self.mode = mode

    def on_click(self):
        if self.mode == 'connect':
            if self.highlighted:
                self.pylon = self.world.construct_pylon()
                self.placing_wire = self.highlighted.connect_to(self.pylon)
                self.highlighted.unhighlight()
                self.highlighted = None
                self.mode = 'placing'

        elif self.mode == 'placing':
            construct = self.world.pick_closest_construct(self.pylon.x, self.pylon.y)
            if construct and construct is not self.placing_wire.target:
                print("Cannot place here!")
                return

            if self.pylon and not self.world.is_buildable_terrain(self.pylon.x, self.pylon.y):
                print("Cannot place on bad terrain!")
                self.pylon.highlight('bad-terrain')
                return

            self.placing_wire.finish_placement()

            # Continue placing if we just placed a pylon.
            if self.pylon.placed:
                old_pylon = self.pylon
                self.pylon = self.world.construct_pylon()
                self.placing_wire = old_pylon.connect_to(self.pylon)
                self.highlighted = None
            else:
                self.placing_wire = None
                self.pylon = None
                self.mode = 'connect'

        elif self.mode == 'erase':
            if self.highlighted:
                if self.highlighted.erasable:
                    self.highlighted.destroy()
                    self.highlighted = None
                else:
                    self.highlighted.highlight('erase')

        elif self.mode == 'upgrade':
            if self.highlighted:
                if self.highlighted.upgradable:
                    self.highlighted.upgrade()
                else:
                    self.highlighted.highlight('upgrade')

    def cycle_unpowered_town(self):
        if all(town.powered for town in self.world.towns):
            return

        while True:
            self.next_unpowered_index = self.next_unpowered_index % len(self.world.towns)

            town = self.world.towns[self.next_unpowered_index]
            self.next_unpowered_index += 1
            if not town.powered:
                self.camera_target.posInterval(constants.cycle_unpowered_town_time, town.root.get_pos(self.pivot), blendType='easeInOut', bakeInStart=True).start()
                return

    def highlight_all(self):
        for thing in [self.world.gen] + self.world.towns:
            thing.highlight(mode=self.mode)

    def cancel_placement(self):
        if self.mode == 'placing':
            self.placing_wire.set_target(self.pylon)
            self.placing_wire.cancel_placement()
            self.placing_wire = None
            self.pylon = None
            self.mode = 'connect'
