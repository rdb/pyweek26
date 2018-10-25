from direct.showbase.ShowBase import ShowBase
from panda3d import core

from .world import World
from . import constants


class Game(ShowBase):
    def __init__(self):
        core.load_prc_file("config.prc")
        ShowBase.__init__(self)

        self.set_background_color((0.02, 0.01, 0.01, 1))

        self.world = World()
        self.world.root.reparent_to(self.render)

        self.world.root.set_shader_auto(True)
        self.world.root.set_antialias(core.AntialiasAttrib.M_auto)

        # Set up camera
        self.disable_mouse()
        self.pivot = self.world.root.attach_new_node("pivot")
        self.camera.reparent_to(self.pivot)
        self.camera.set_pos(0, -15, 15)
        self.camera.look_at(0, 0, 0)

        self.lens = self.cam.node().get_lens(0)
        self.lens.focal_length = 0.4
        self.lens.set_fov(50)

        self.pivot.set_h(20)

        self.clock = core.ClockObject.get_global_clock()
        self.task_mgr.add(self.__task)


        self.mode = 'normal'

        self.accept('mouse1', self.on_click)
        self.accept('mouse3', self.cancel_placement)
        self.accept('shift-s', self.screenshot)
        self.accept('escape', self.cancel_placement)
        self.accept('shift-h', self.highlight_all)
        self.accept('shift-l', self.render.ls)
        self.accept('shift-p', self.create_stats)
        self.accept('wheel_up', self.on_zoom, [1.0])
        self.accept('wheel_down', self.on_zoom, [-1.0])

        self.highlighted = None
        self.pylon = None
        self.placing_wire = None

    def __task(self, task):
        self.world.step(self.clock.dt)

        mw = self.mouseWatcherNode

        # Keyboard controls
        hor = mw.is_button_down('arrow_right') - mw.is_button_down('arrow_left')
        if hor != 0:
            speed = constants.camera_speed * self.camera.get_pos().length_squared() ** 0.2
            self.camera.set_x(self.camera.get_x() + hor * speed * self.clock.dt)

        ver = mw.is_button_down('arrow_up') - mw.is_button_down('arrow_down')
        if ver != 0:
            speed = constants.camera_speed * self.camera.get_pos().length_squared() ** 0.2
            self.camera.set_y(self.camera.get_y() + ver * speed * self.clock.dt)

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

        if construct is not None and construct is not self.highlighted:
            construct.highlight()
            self.highlighted = construct

        if self.placing_wire:
            if not self.placing_wire.try_set_target(self.highlighted):
                self.placing_wire.set_target(self.pylon)

        return task.cont

    def on_zoom(self, amount):
        lens = self.lens
        #lens.set_fov(lens.get_fov() * (1.0 + amount * 0.1))
        self.camera.set_pos(self.camera.get_pos() * (1.0 + amount * 0.1))

    def on_click(self):
        if self.mode == 'normal':
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
                self.mode = 'normal'

    def highlight_all(self):
        for thing in [self.world.gen] + self.world.towns:
            thing.highlight()

    def cancel_placement(self):
        if self.mode == 'placing':
            self.placing_wire.set_target(self.pylon)
            self.placing_wire.cancel_placement()
            self.placing_wire = None
            self.pylon = None
            self.mode = 'normal'
