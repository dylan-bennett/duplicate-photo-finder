from tkinter import *
from tkinter import ttk


class OutlinedFrame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, relief="ridge", borderwidth=2)


class Interface:
    def __init__(self, root):
        # Set the window title
        root.title("Duplicate Photo Finder")

        # Create the main frame within the window
        main_frame = ttk.Frame(root, padding=(3, 3, 3, 3))
        main_frame.grid(column=0, row=0, sticky=(N, S, E, W))

        # Frame that holds the controls. Stretch it horizontally.
        controls_frame = OutlinedFrame(main_frame, height=100)
        controls_frame.grid(column=0, row=0, sticky=(E, W))

        # Scan button
        scan_button = ttk.Button(controls_frame, text="Scan")
        scan_button.grid(column=0, row=0, sticky=W)

        # Scanning text, stretched horizontally
        self.scanning_text = StringVar(value="Click to scan")
        scanning_label = ttk.Label(controls_frame, textvariable=self.scanning_text)
        scanning_label.grid(column=1, row=0, padx=5)
        controls_frame.columnconfigure(1, weight=1)

        # Delete button
        delete_button = ttk.Button(controls_frame, text="Delete")
        delete_button.grid(column=2, row=0, sticky=E)

        # Frame that holds the thumbnails. Stretch it in all directions.
        thumbnails_frame = OutlinedFrame(main_frame, height=500, width=1000)
        thumbnails_frame.grid(column=0, row=1, sticky=(N, S, E, W))

        # Fill the root window with the main frame
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Fill the main frame with the first column and the thumbnails row
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
