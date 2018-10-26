from panda3d import core

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject

from . import constants


color1 = (0.9, 0.9, 0.9, 1)
color0 = constants.normal_label_color


class Panel(DirectObject):

    def __init__(self, parent):
        self.frame = DirectFrame(
            parent=parent,
            frameSize=(0, 0.02, 0, 0.3),
            frameColor=(0.9, 0.9, 0.9, 0.5),
        )

        self.icon_font = loader.load_font("data/font/font-awesome5.otf")
        self.icon_font.pixels_per_unit = 128.0

        self.frame.set_pos(0.05, 0, 0.05)

        self.buttons = []
        self.icons = []

        self.selected_button = None
        self.selected_icon = None

    def add_button(self, text, icon=None, callback=None, arg=None, shortcut=None):
        i = len(self.buttons)
        x = i * 0.27
        frame = DirectFrame(parent=self.frame, pos=(0.02 + x, 0, 0.02), frameColor=color0, frameSize=(0, 0.25, 0, 0.25))
        button = DirectButton(parent=frame, pos=(0.005, 0, 0.005), text=text, frameSize=(0, 0.24, 0, 0.24), text_scale=0.04, text_pos=(0.12, 0.025), frameColor=color0, text_fg=color1, relief=DGG.FLAT, command=self.on_click, extraArgs=[i, callback, arg])
        self.buttons.append(button)

        self.frame['frameSize'] = (0, 0.02 + 0.27 * len(self.buttons), 0, 0.3)

        if icon is not None:
            icon = OnscreenText(parent=button, pos=(0.12, 0.12), text=chr(icon), font=self.icon_font, scale=0.08, fg=color1)
            icon.name = "icon"
            self.icons.append(icon)
        else:
            self.icons.append(None)

        if shortcut:
            self.accept(shortcut, self.on_click, [i, callback, arg])

    def on_click(self, i, callback, arg):
        self.select_button(i)
        callback(arg)

    def select_button(self, i):
        if self.selected_button is not None:
            button = self.selected_button
            button['frameColor'] = color0
            button['text_fg'] = color1

            if self.selected_icon is not None:
                self.selected_icon['fg'] = color1

        button = self.buttons[i]
        self.selected_button = button

        button['frameColor'] = color1
        button['text_fg'] = color0

        icon = self.icons[i]
        self.selected_icon = icon

        if icon is not None:
            icon['fg'] = color0
