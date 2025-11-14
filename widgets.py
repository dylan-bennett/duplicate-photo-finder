from tkinter import VERTICAL, Canvas, E, N, S, W, ttk


class OutlinedFrame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs,
            relief=kwargs.get("relief", "ridge"),
            borderwidth=kwargs.get("borderwidth", 2)
        )


class VerticalScrollFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        # Create the outer Frame instance, bound to the parent
        super().__init__(parent, *args, **kwargs)

        # Canvas (a scrollable widget)
        self.canvas = Canvas(
            self,
            borderwidth=0,
            highlightthickness=0,
            width=kwargs.get("width"),
            height=kwargs.get("height"),
        )
        self.canvas.grid(column=0, row=0, sticky=(N, S, E, W))

        # Scrollbar bound to the canvas
        scrollbar = ttk.Scrollbar(
            self,
            orient=VERTICAL,
            command=self.canvas.yview,
        )
        scrollbar.grid(column=1, row=0, sticky=(N, S))
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Inner frame that will actually hold the content, embedded in the canvas
        self.frame = ttk.Frame(self.canvas)
        self.frame_window = self.canvas.create_window(
            (0, 0), window=self.frame, anchor="nw"
        )

        # Update the scrollable region whenever the inner frame changes size
        self.frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        # Keep the inner frame the same width as the canvas so it stretches horizontally
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(
                self.frame_window, width=event.width
            ),
        )

        # Enable scrolling with the mouse wheel when hovering the canvas
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, _event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        elif event.delta:
            direction = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(direction, "units")
