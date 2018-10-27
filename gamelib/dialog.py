from panda3d import core

from direct.gui import DirectGuiGlobals as DGG
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectButton import DirectButton
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.DirectObject import DirectObject

from . import constants


color1 = (0.9, 0.9, 0.9, 1)
color0 = constants.normal_label_color


class Dialog(DirectObject):

    def __init__(self, parent, text="", font=None, icon_font=None):
        self.outer = DirectFrame(
            parent=parent,
            frameSize=(-0.7, 0.7, -0.4, 0.4),
            frameColor=color0,
        )

        self.inner = DirectFrame(
            parent=self.outer,
            frameSize=(-0.695, 0.695, -0.395, 0.395),
            frameColor=color1,
            text_scale=0.05,
            text_fg=(0.1, 0.1, 0.1, 1),
            text_font=font,
            text_pos=(-0.65, 0.35),
            text_align=core.TextNode.A_left,
            text=text,
        )
        self.outer.hide()

        frame = DirectFrame(parent=self.inner, pos=(-0.125, 0, -0.355), frameColor=color0, frameSize=(0, 0.25, 0, 0.25))
        button = DirectButton(parent=frame, pos=(0.005, 0, 0.005), text='', frameSize=(0, 0.24, 0, 0.24), text_scale=0.04, text_pos=(0.12, 0.025), frameColor=color0, text_fg=color1, relief=DGG.FLAT, command=self.on_click)
        self.button = button

        icon = OnscreenText(parent=button, pos=(0.12, 0.12), text='', font=icon_font, scale=0.08, fg=color1)
        icon.name = "icon"
        self.icon = icon

    def on_click(self):
        if self.callback is not None:
            self.callback()
        self.hide()

    def show(self, text, button_text='', button_icon=None, callback=None):
        self.inner['text'] = text
        self.outer.show()
        self.callback = callback

        self.button['text'] = button_text
        if button_icon is not None:
            self.icon['text'] = chr(button_icon)
        else:
            self.icon['text'] = ''

    def hide(self):
        self.outer.hide()
        self.callback = None
