import tkinter as tk


class NavFrame(tk.Frame):
    """
    Frame acts as a navbar
    """

    def __init__(
        self,
        parent: tk.Frame,
        controller: tk.Tk,
        links: list[callable],
        active_link: callable,
    ):
        super().__init__(parent, bg="purple")
        self.controller = controller
        self.links = links
        self.active_link = active_link
        self.render()

    def render(self):
        for i, frame in enumerate(self.links):
            bg = "white" if frame == self.active_link else "purple"
            fg = "black" if frame == self.active_link else "white"
            link_label = tk.Label(
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
