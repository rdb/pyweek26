from direct.showbase.ShowBase import ShowBase
from direct.showbase.Audio3DManager import Audio3DManager
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from panda3d import core

from .world import World
from .panel import Panel
from .dialog import Dialog
from . import constants

import math
import random
import sys


months = ["January", "February", "March", "April", "May", "June", "July",
         "August", "September", "October", "November", "December"]


class Game(ShowBase):
    def __init__(self):
        core.load_prc_file("config.prc")
        ShowBase.__init__(self)

        try:
            bold_font = loader.load_font("data/font/Roboto-Bold.ttf")
        except:
            print("Could not load Roboto-Bold.ttf")
            bold_font = None

        icon_font = loader.load_font("data/font/font-awesome5.otf")
        icon_font.pixels_per_unit = 128.0

        self.set_background_color((0.02, 0.01, 0.01, 1))

        # Disable control modifiers, etc.
        buttons = core.ModifierButtons()
        buttons.add_button("shift")
        self.mouseWatcherNode.set_modifier_buttons(buttons)

        audio3d = Audio3DManager(self.sfxManagerList[0], self.camera)
        #audio3d.set_distance_factor(1.0)
        audio3d.set_drop_off_factor(3.0)

        self.world = World(audio3d)
        self.world.root.reparent_to(self.render)

        self.music = loader.load_music("Contemplation.mp3")
        if self.music is not None:
            self.music.set_loop(1)
            self.music.set_play_rate(1.0)
        self.target_play_rate = 1.0

        #self.world.root.set_shader_auto(True)
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
        self.task_mgr.add(self.__game_task)
        self.task_mgr.add(self.__music_task)

        # Create UI
        self.panel = Panel(self.a2dBottomLeft, align='left', icon_font=icon_font)
        self.panel.add_button("1. Connect", icon=0xf5ee, callback=self.on_switch_mode, arg='connect', shortcut='1')
        self.panel.add_button("2. Upgrade", icon=0xf102, callback=self.on_switch_mode, arg='upgrade', shortcut='2')
        self.panel.add_button("3. Erase", icon=0xf12d, callback=self.on_switch_mode, arg='erase', shortcut='3')

        self.panel2 = Panel(self.a2dBottomRight, align='right', icon_font=icon_font)
        self.panel2.add_button("Pause", icon=0xf04c, callback=self.on_change_speed, arg=0)
        self.panel2.add_button("1x Speed", icon=0xf04b, callback=self.on_change_speed, arg=1)
        self.panel2.add_button("3x Speed", icon=0xf04e, callback=self.on_change_speed, arg=3)
        self.panel2.add_button("Quit", icon=0xf011, callback=self.on_quit, arg=None)
        self.game_speed = 0.0

        self.unpowered_button = DirectButton(parent=self.a2dTopLeft, pos=(0.13, 0, -0.15), text='\uf071', text_font=self.panel.icon_font, text_scale=0.1, text_fg=constants.important_label_color, relief=None, command=self.cycle_unpowered_town)
        self.unpowered_button.hide()
        self.unpowered_text = OnscreenText(parent=self.unpowered_button, pos=(0, -0.05), font=bold_font, text='Press tab', fg=constants.important_label_color, scale=0.04)
        self.next_unpowered_index = 0

        self.time_text = OnscreenText(parent=self.a2dBottomCenter, pos=(-0.1, 0.15), text='January, year 1', fg=(1, 1, 1, 1), scale=0.08)
        self.time_text.hide()
        self.month = 0.0
        self.year = 0

        self.power_text = OnscreenText(parent=self.a2dBottomCenter, pos=(-0.1, 0.24), text='', fg=(1, 1, 1, 1), scale=0.05)
        self.energy_text = OnscreenText(parent=self.a2dBottomCenter, pos=(-0.1, 0.07), text='', fg=(1, 1, 1, 1), scale=0.05)
        self.energy = 0.0
        self.total_energy = 0.0
        self.power = 0.0
        self.energy_target = 9000.0

        self.upgrade_text = OnscreenText(parent=self.a2dTopRight, align=core.TextNode.A_right, pos=(-0.21, -0.15), text='0', fg=(1, 1, 1, 1), scale=0.08)
        self.upgrade_icon = OnscreenText(parent=self.a2dTopRight, text='\uf35b', fg=constants.normal_label_color, pos=(-0.12, -0.16), font=icon_font, scale=0.1)
        self.upgrade_text.hide()
        self.upgrade_icon.hide()
        self.upgrade_counter = 0.0
        self.upgrades = 0

        self.dialog = Dialog(parent=self.aspect2d, icon_font=icon_font)

        self.mode = 'connect'

        self.accept('mouse1', self.on_click)
        self.accept('mouse3', self.cancel_placement)
        self.accept('shift-s', self.screenshot)
        self.accept('escape', self.cancel_placement)
        self.accept('shift-h', self.highlight_all)
        self.accept('shift-l', self.render.ls)
        self.accept('shift-p', self.create_stats)
        self.accept('shift-t', self.spawn_town)
        self.accept('shift-f', self.on_change_speed, [10.0])
        self.accept('tab', self.cycle_unpowered_town)
        self.accept('wheel_up', self.on_zoom, [-1.0])
        self.accept('wheel_down', self.on_zoom, [1.0])
        self.accept('space', self.on_toggle_pause)
        self.accept('shift-q', sys.exit)

        self.highlighted = None
        self.pylon = None
        self.placing_wire = None
        self.tutorial_done = False

        # Initial mode
        self.panel.select_button(0)
        self.panel2.select_button(1)

    def tutorial_end(self):
        self.dialog.show("""
Nice! You seem to get the gist of the game.

Keep growing your cities by providing them power. But be
careful! If you overload your power cables, they will break,
and the cities they are connected to will stop growing.

Try to reach {:.0f} MJ before the year's end!
""".format(self.energy_target / 10), button_text='Of course!', button_icon=0xf04b, callback=self.on_game_start)

    def on_game_start(self):
        for town in self.world.towns:
            town.placed = True
        self.tutorial_done = True
        self.game_speed = 1.0
        self.time_text.show()
        self.panel.show()
        self.panel2.show()
        self.cycle_unpowered_town()
        self.music.play()
        self.target_play_rate = 1.0
        self.task_mgr.add(self.__camera_task)

    def on_begin_month(self, month):
        print("Beginning month {}".format(month))
        if month == 6:
            # Sprout third town.
            spots = list(self.world.beginner_town_spots)
            random.shuffle(spots)

            # If all spots are already occupied, find some other spot.
            spots.append(None)

            index = len(self.world.towns)
            for spot in spots:
                if spot is None or self.world.grid[spot[0]][spot[1]] == 0:
                    self.world.sprout_town(grid_pos=spot)
                    break

            self.cycle_unpowered_town(index)

        elif month == 12:
            # We don't actually check energy target here... guess we don't
            # want to lose the player on the first year.
            self.pause()
            self.energy_target *= constants.energy_target_multiplier

            if self.upgrades == 0:
                # Aw, here's an upgrade point.
                self.on_get_upgrade()

            text = """
Great! You may notice in the top-right corner that you are
starting to obtain upgrade points. Use these to upgrade
your pylons to increase the capacity of its wires.

Can you supply {:.1f} more GJ by the end of the year?

Another town has sprung up. Press tab to focus it.
""".format(self.energy_target / 10000)
            self.dialog.show(text, button_text='Bring it on!', button_icon=0xf04b, callback=self.on_toggle_pause)

            self.world.sprout_town()

        elif month % 12 == 0 and month > 0:
            self.pause()

            if self.energy >= self.energy_target:
                self.next_unpowered_town = len(self.world.towns)
                self.world.sprout_town()

                self.energy_target *= constants.energy_target_multiplier
                callback = self.on_toggle_pause
                text = """
Well done!
You supplied {:.1f} GJ last year and made it to year {}!

Can you supply {:.1f} more GJ by the end of the year?

Another town has sprung up. Press tab to focus it.
""".format(self.energy / 10000, int(month // 12) + 1, self.energy_target / 10000)
                self.dialog.show(text, button_text='Bring it on!', button_icon=0xf04b, callback=self.on_toggle_pause)
            else:
                text = """
Unfortunately, you failed to satisfy the growing energy
demands. You needed to produce {:.1f} GJ, but you
produced only {:.1f} GJ.

You produced a grand total of {:.1f} GJ.

Better luck next time!
""".format(self.energy_target / 10000, self.energy / 10000, self.total_energy / 10000)
                self.dialog.show(text, button_text='Quit', button_icon=0xf011, callback=sys.exit)

            self.energy = 0.0

    def on_get_upgrade(self):
        self.upgrade_counter = 0.0
        self.upgrades += 1

        self.upgrade_text['text'] = str(self.upgrades)
        self.upgrade_text.show()
        self.upgrade_icon.show()

    def on_use_upgrade(self):
        self.upgrades -= 1

        self.upgrade_text['text'] = str(self.upgrades)

    def __music_task(self, task):
        play_rate = self.music.get_play_rate()
        if self.target_play_rate != play_rate:
            diff = self.target_play_rate - play_rate
            if abs(diff) < 0.01:
                new_play_rate = self.target_play_rate
            elif diff > 0:
                diff = min(diff, self.clock.dt * constants.music_rate_change_speed)
                new_play_rate = play_rate + diff
            else:
                diff = max(diff, -self.clock.dt * constants.music_rate_change_speed)
                new_play_rate = play_rate + diff
            self.music.set_play_rate(new_play_rate)
        return task.cont

    def __camera_task(self, task):
        mw = self.mouseWatcherNode

        # Keyboard controls
        hor = mw.is_button_down('arrow_right') - mw.is_button_down('arrow_left')
        ver = mw.is_button_down('arrow_up') - mw.is_button_down('arrow_down')

        # Check mouse on camera edge.
        p = base.win.get_pointer(0)
        if p.in_window and not self.panel.hovered and not self.panel2.hovered:
            size = base.win.size
            if p.x < constants.camera_window_border:
                hor -= 2
            if p.x > size.x - constants.camera_window_border:
                hor += 2
            if p.y < constants.camera_window_border:
                ver += 2
            if p.y > size.y - constants.camera_window_border:
                ver -= 2

        if hor != 0:
            speed = constants.camera_speed * self.camera.get_pos().length_squared() ** 0.2
            movement = hor * speed * self.clock.dt
            abs_pos = self.world.root.get_relative_point(self.camera_target, (movement, 0, 0))
            abs_pos.x = min(max(abs_pos.x, -20), 20)
            abs_pos.y = min(max(abs_pos.y, -20), 20)
            self.camera_target.set_pos(self.world.root, abs_pos)

        if ver != 0:
            speed = constants.camera_speed * self.camera.get_pos().length_squared() ** 0.2
            movement = ver * speed * self.clock.dt
            abs_pos = self.world.root.get_relative_point(self.camera_target, (0, movement, 0))
            abs_pos.x = min(max(abs_pos.x, -20), 20)
            abs_pos.y = min(max(abs_pos.y, -20), 20)
            self.camera_target.set_pos(self.world.root, abs_pos)

        return task.cont

    def __game_task(self, task):
        elapsed = self.clock.dt * self.game_speed * 0.5
        self.world.step(elapsed)

        if self.game_speed > 0.0:
            power = 0
            for town in self.world.towns:
                if town.powered:
                    power += town.power
            self.power = power
            energy = self.power * self.clock.dt * self.game_speed
            self.energy += energy
            self.total_energy += energy
            self.upgrade_counter += energy / constants.upgrade_point_rarity
            self.power_text['text'] = '{:.0f} MW'.format(self.power * 0.1)
            self.energy_text['text'] = '{:.0f} MJ'.format(self.energy * 0.1)

            if self.upgrade_counter > 1:
                self.on_get_upgrade()

        if self.game_speed != 0:
            new_month = self.month + elapsed * 0.4
            year = int(new_month // 12)
            self.time_text.text = months[int(new_month) % 12] + ', year ' + str(year + 1)

            if int(new_month) != int(self.month):
                self.on_begin_month(int(new_month))

            self.month = new_month

        if all(town.powered for town in self.world.towns):
            self.unpowered_button.hide()

        elif self.tutorial_done:
            # Show only if we are not looking straight at the town.
            cam_pos = self.camera_target.get_pos(self.world.root).xy
            if any((town.pos - cam_pos).length_squared() > 25 for town in self.world.towns if not town.powered):
                self.unpowered_button.show()
            else:
                self.unpowered_button.hide()

        elif any(town.powered for town in self.world.towns):
            self.tutorial_end()

        mw = self.mouseWatcherNode

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

            elif self.mode == 'upgrade':
                if construct.upgradable and self.upgrades == 0:
                    construct.highlight("upgrade-no-money")
                elif construct.highlight_mode != 'yay-upgraded':
                    construct.highlight("upgrade")
            elif not construct.highlighted:
                construct.highlight("normal")

        elif self.placing_wire:
            self.placing_wire.set_target(self.pylon)

        return task.cont

    def spawn_town(self):
        index = len(self.world.towns)
        self.world.sprout_town()
        self.cycle_unpowered_town(index)

    def pause(self):
        self.panel2.select_button(0)
        self.on_change_speed(0)

    def on_zoom(self, amount):
        if not self.tutorial_done:
            return

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

    def on_change_speed(self, speed):
        print("Changing game speed to {}".format(speed))
        self.game_speed = speed
        if speed != 0:
            self.dialog.hide()

        if speed > 1:
            self.target_play_rate = 2.0
        else:
            self.target_play_rate = speed

    def on_toggle_pause(self):
        if not self.tutorial_done:
            return
        if self.game_speed == 0:
            self.panel2.select_button(1)
            self.on_change_speed(1)
        else:
            self.pause()

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
                if self.highlighted.upgradable and not self.highlighted.upgraded:
                    if self.upgrades > 0:
                        self.highlighted.upgrade()
                        self.on_use_upgrade()
                        self.highlighted.highlight("yay-upgraded")
                    else:
                        self.highlighted.highlight("upgrade-no-money")
                else:
                    self.highlighted.highlight('upgrade')

    def on_quit(self, arg=None):
        self.pause()

        text = """
Are you sure you want to quit?

You produced a grand total of {:.1f} GJ.

Press shift + Q to really exit the game.
""".format(self.total_energy / 10000)
        self.dialog.show(text, button_text='Keep playing', button_icon=0xf04b, callback=self.on_toggle_pause)

    def cycle_unpowered_town(self, index=None):
        if all(town.powered for town in self.world.towns):
            return

        if index is not None:
            self.next_unpowered_index = index

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
