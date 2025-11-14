from tkinter import VERTICAL, Canvas, E, N, S, StringVar, W, ttk

from PIL import Image, ImageTk

from finder import DuplicatePhotoFinder
from widgets import OutlinedFrame


class Interface:
    def __init__(self, root, database):
        self.database_connection = database
        self.database_cursor = self.database_connection.cursor()

        # Set the window title
        root.title("Duplicate Photo Finder")

        # Create the main frame within the window
        main_frame = ttk.Frame(root, padding=(3, 3, 3, 3))
        main_frame.grid(column=0, row=0, sticky=(N, S, E, W))

        # Frame that holds the controls. Stretch it horizontally.
        controls_frame = OutlinedFrame(main_frame, height=100)
        controls_frame.grid(column=0, row=0, sticky=(E, W))

        # Scan button
        scan_button = ttk.Button(
            controls_frame, text="Scan", command=self.scan_for_duplicates
        )
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
        self.thumbnails_cols = 5
        thumbnails_container = OutlinedFrame(main_frame)
        thumbnails_container.grid(column=0, row=1, sticky=(N, S, E, W))
        thumbnails_container.columnconfigure(0, weight=1)
        thumbnails_container.rowconfigure(0, weight=1)

        # Canvas that will scroll the thumbnails frame
        self.thumbnails_canvas = Canvas(
            thumbnails_container,
            borderwidth=0,
            highlightthickness=0,
            height=500,
            width=1000,
        )
        self.thumbnails_canvas.grid(column=0, row=0, sticky=(N, S, E, W))

        # Scrollbar wired to the canvas
        thumbnails_scrollbar = ttk.Scrollbar(
            thumbnails_container, orient=VERTICAL, command=self.thumbnails_canvas.yview
        )
        thumbnails_scrollbar.grid(column=1, row=0, sticky=(N, S))
        self.thumbnails_canvas.configure(yscrollcommand=thumbnails_scrollbar.set)

        # Frame that will actually hold the thumbnails, embedded in the canvas
        self.thumbnails_frame = ttk.Frame(self.thumbnails_canvas)
        self._thumbnails_window = self.thumbnails_canvas.create_window(
            (0, 0), window=self.thumbnails_frame, anchor="nw"
        )

        # Update the scrollable region whenever the inner frame changes size
        self.thumbnails_frame.bind(
            "<Configure>",
            lambda event: self.thumbnails_canvas.configure(
                scrollregion=self.thumbnails_canvas.bbox("all")
            ),
        )

        # Keep the inner frame the same width as the canvas so it stretches horizontally
        self.thumbnails_canvas.bind(
            "<Configure>",
            lambda event: self.thumbnails_canvas.itemconfigure(
                self._thumbnails_window, width=event.width
            ),
        )

        # Enable scrolling with the mouse wheel when hovering the canvas
        self.thumbnails_canvas.bind("<Enter>", self._bind_mousewheel)
        self.thumbnails_canvas.bind("<Leave>", self._unbind_mousewheel)

        # Fill the root window with the main frame
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Fill the main frame with the first column and the thumbnails row
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Reference to each hash's thumbnail objects, to prevent garbage collection
        self.hash_and_thumbnails = {}

        # Fill the thumbnails frame with duplicate thumbnails
        self.populate_thumbnails()

    def scan_for_duplicates(self):
        self.scanning_text.set("Scanning for photo files...")

        # Hash the photo files and store in the database
        finder = DuplicatePhotoFinder(database=self.database_connection)
        # duplicate_photo_finder.compute_file_hashes()

        filepaths = finder.find_photo_filepaths()
        num_photos = len(filepaths)
        for i, filepath in enumerate(filepaths, 1):
            self.scanning_text.set(f"Analyzing photo {i}/{num_photos}...")
            finder.compute_file_hash(filepath)

        self.scanning_text.set("Updating thumbnails...")

        # Update the thumbnails
        self.populate_thumbnails()

        self.scanning_text.set("Scan complete!")

    def display_thumbnails_in_frame(self, hash_frame, filepaths):
        # Display the photos as thumbnails
        thumbnails = []

        for filepath in filepaths:
            try:
                # Create the Image object
                img = Image.open(filepath)

                # Convert it into a thumbnail
                img.thumbnail((200, 200))

                # Create a Tkinter-compatible photo image object
                tk_img = ImageTk.PhotoImage(img)

                # Add it to our list of thumbnails
                thumbnails.append(tk_img)
            except Exception as e:
                print(f"Error loading image {filepath}: {e}")

        # Display the thumbnails within the thumbnails frame
        row, col = 0, 0
        for thumbnail in thumbnails:
            # Display the thumbnail
            label = ttk.Label(hash_frame, image=thumbnail)
            label.grid(row=row, column=col, padx=5, pady=5)

            # Increment the row and column
            col += 1
            if col >= self.thumbnails_cols:
                col = 0
                row += 1

        # Return the thumbnail objects to prevent garbage collection
        return thumbnails

    def populate_thumbnails(self):
        # Create a cursor to navigate through the database
        database_cursor = self.database_connection.cursor()

        # Grab the duplicate photos, grouped by hash
        database_cursor.execute(
            """SELECT hash, GROUP_CONCAT(filepath)
            FROM photos
            GROUP BY hash
            HAVING COUNT(*) > 1
            """
        )
        db_rows = database_cursor.fetchall()

        # Remove any previous thumbnail groups
        for child in self.thumbnails_frame.winfo_children():
            child.destroy()

        self.hash_and_thumbnails = {}

        frame_row = 0
        for hash, concat_filepaths in db_rows:
            # Get the list of filepaths
            filepaths = concat_filepaths.split(",")

            # Create a new Frame for the hash's thumbnails
            hash_frame = ttk.Frame(self.thumbnails_frame)
            hash_frame.grid(row=frame_row, column=0)
            frame_row += 1

            # Put the thumbnails into the frame
            thumbnails = self.display_thumbnails_in_frame(hash_frame, filepaths)

            # Save the thumbnail objects, to avoid garbage collection
            self.hash_and_thumbnails[hash] = thumbnails

    def _bind_mousewheel(self, _event):
        self.thumbnails_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.thumbnails_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.thumbnails_canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        self.thumbnails_canvas.unbind_all("<MouseWheel>")
        self.thumbnails_canvas.unbind_all("<Button-4>")
        self.thumbnails_canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.thumbnails_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.thumbnails_canvas.yview_scroll(1, "units")
        elif event.delta:
            direction = -1 if event.delta > 0 else 1
            self.thumbnails_canvas.yview_scroll(direction, "units")
