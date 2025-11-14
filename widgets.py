from tkinter import ttk


class OutlinedFrame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, relief="ridge", borderwidth=2)
