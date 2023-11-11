import tkinter as tk
from src.constants import *
from src.tools.defaults import DefaultFrame, DefaultLabel


class NavFrame(DefaultFrame):
    """
    Frame acts as a navbar
    """

    def __init__(
        self,
        parent: DefaultFrame,
        controller: tk.Tk,
        links: list[callable],
        active_link: callable,
    ):
        super().__init__(parent, bg=NAVBAR_BACKGROUND_COLOR)
        self.controller = controller
        self.links = links
        self.active_link = active_link
        self.render()

    def render(self):
        for i, frame in enumerate(self.links):
            bg = (
                NAVBAR_ACTIVE_BACKGROUND_COLOR
                if frame == self.active_link
                else NAVBAR_BACKGROUND_COLOR
            )
            fg = (
                NAVBAR_ACTIVE_TEXT_COLOR
                if frame == self.active_link
                else NAVBAR_TEXT_COLOR
            )
            link_label = DefaultLabel(
                self,
                text=frame.__name__,
                fg=fg,  # Text color
                bg=bg,  # Background color
                cursor="hand",  # Hand cursor on hover
            )
            link_label.bind(
                "<Button-1>",
                lambda event, frame=frame: self.change_page(frame),
            )
            link_label.grid(row=0, column=i, pady=10, padx=10)

    def change_page(self, frame):
        self.active_link = frame
        self.render()
        self.controller.show_frame(frame)
