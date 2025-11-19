from tkinter import VERTICAL, Canvas, E, N, S, W, ttk


class OutlinedFrame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        """Initialize an OutlinedFrame with default border styling.

        Args:
            *args: Variable positional arguments passed to ttk.Frame.
            **kwargs: Variable keyword arguments passed to ttk.Frame.
                If 'relief' is not provided, defaults to 'ridge'.
                If 'borderwidth' is not provided, defaults to 2.

        Creates a ttk.Frame with visible borders by default, making it
        useful for creating outlined sections in the GUI.
        """
        super().__init__(
            *args,
            **kwargs,
            relief=kwargs.get("relief", "ridge"),
            borderwidth=kwargs.get("borderwidth", 2)
        )


class VerticalScrollFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        """Initialize a vertically scrollable frame widget.

        Args:
            parent: Parent widget for this frame.
            *args: Variable positional arguments passed to ttk.Frame.
            **kwargs: Variable keyword arguments passed to ttk.Frame.
                'width' and 'height' are used to size the canvas.

        Creates a scrollable container with a canvas, vertical scrollbar,
        and an inner frame for content. The inner frame automatically
        adjusts its scrollable region and width. Mouse wheel scrolling
        is enabled when the mouse enters the canvas area.
        """
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
        """Bind mouse wheel events for scrolling.

        Args:
            _event: Tkinter event object (unused).

        Binds mouse wheel events (<MouseWheel> for Windows/Mac,
        <Button-4> and <Button-5> for Linux) to enable scrolling
        when the mouse enters the canvas area.
        """
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        """Unbind mouse wheel events when mouse leaves the canvas.

        Args:
            _event: Tkinter event object (unused).

        Removes all mouse wheel event bindings when the mouse leaves
        the canvas area to prevent scrolling when not hovering over
        the scrollable frame.
        """
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling events.

        Args:
            event: Tkinter event object containing mouse wheel information.

        Scrolls the canvas vertically based on mouse wheel input.
        Handles both Linux-style button events (Button-4 for scroll up,
        Button-5 for scroll down) and Windows/Mac-style delta events.
        """
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        elif event.delta:
            direction = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(direction, "units")
