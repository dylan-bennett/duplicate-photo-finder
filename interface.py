from sqlite3 import IntegrityError
from tkinter import E, N, S, StringVar, Tk, W, ttk

from PIL import Image, ImageTk

from widgets import OutlinedFrame, VerticalScrollFrame


class Interface:
    def __init__(self, database, finder):
        """Initialize the Interface and start the GUI application.

        Args:
            database: Database instance for accessing photo data.
            finder: Finder instance for scanning and hashing photos.

        Creates the Tkinter root window, builds the GUI layout, populates
        initial thumbnails, and starts the main event loop.
        """
        self.finder = finder
        self.database = database

        # Reference to each hash's thumbnail objects, to prevent garbage collection
        self.hash_and_thumbnails = {}

        # List of selected thumbnails
        self.selected_thumbnails = []

        # Instantiate the Tk root window
        self.tk_root = Tk()

        # Create the GUI
        self.create_gui()

        # Fill the thumbnails frame with duplicate thumbnails
        self.populate_thumbnails()

        # Spin up the GUI
        self.tk_root.mainloop()

    def create_gui(self):
        """Create and configure the graphical user interface layout.

        Sets up the main window with a controls frame containing scan and
        delete buttons, a status label, and a scrollable thumbnails container
        for displaying duplicate photos.
        """
        # Set the window title
        self.tk_root.title("Duplicate Photo Finder")

        # Create the main frame within the window
        main_frame = ttk.Frame(self.tk_root, padding=(3, 3, 3, 3))
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
        self.thumbnails_container = VerticalScrollFrame(
            main_frame, width=1000, height=500, relief="ridge", borderwidth=2
        )
        self.thumbnails_container.grid(column=0, row=1, sticky=(N, S, E, W))
        self.thumbnails_container.columnconfigure(0, weight=1)
        self.thumbnails_container.rowconfigure(0, weight=1)

        # Fill the Tk root window with the main frame
        self.tk_root.columnconfigure(0, weight=1)
        self.tk_root.rowconfigure(0, weight=1)

        # Fill the main frame with the first column and the thumbnails row
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def scan_for_duplicates(self):
        """Scan for duplicate photos and update the display.

        Finds all photo files in the configured directory, computes their
        hashes, stores them in the database, and updates the thumbnail
        display to show newly found duplicates. Updates the status text
        throughout the scanning process.
        """
        # Update the scanning text
        self.scanning_text.set("Scanning for photo files...")

        # Hash the photo files and store in the database
        filepaths = self.finder.find_photo_filepaths()
        num_photos = len(filepaths)
        for i, filepath in enumerate(filepaths, 1):
            self.scanning_text.set(f"Analyzing photo {i}/{num_photos}...")
            file_hash = self.finder.compute_file_hash(filepath)

            # Insert the file path and its hash into the database
            if file_hash:
                try:
                    self.database.insert_filepath_and_hash(filepath, file_hash)
                except IntegrityError:
                    pass

        # Update the thumbnails
        self.scanning_text.set("Updating thumbnails...")
        self.populate_thumbnails()

        # Reset the scanning text
        self.scanning_text.set("Scan complete!")

    def display_thumbnails_in_frame(self, hash_frame, filepaths):
        """Display photo thumbnails in a grid layout within the given frame.

        Args:
            hash_frame: Tkinter Frame widget to display thumbnails in.
            filepaths: List of file paths to images to display as thumbnails.

        Returns:
            List of PhotoImage objects representing the thumbnails. These
            must be kept in scope to prevent garbage collection.

        Loads each image, creates a 200x200 thumbnail, and arranges them
        in a grid with 5 columns. Handles errors gracefully by skipping
        images that cannot be loaded.
        """
        thumbnails = []
        row, col = 0, 0

        # Run through all of the photograph files
        for filepath in filepaths:
            try:
                # Create the Image object
                img = Image.open(filepath)

                # Convert it into a thumbnail
                img.thumbnail((200, 200))

                # Create a Tkinter-compatible photo image object
                thumbnail = ImageTk.PhotoImage(img)

                # Add it to our list of thumbnails
                thumbnails.append(thumbnail)
            except Exception as e:
                print(f"Error loading image {filepath}: {e}")
                continue

            # Create a frame for the thumbnail. We'll change its border
            # to indicate selected/deselecated
            thumbnail_frame = ttk.Frame(hash_frame, relief="flat", borderwidth=3)
            thumbnail_frame.grid(row=row, column=col, padx=5, pady=5)

            # Display the thumbnail within the frame
            label = ttk.Label(thumbnail_frame, image=thumbnail)
            label.pack()

            # Add in filepath and frame attributes to the Label, for later reference
            label.filepath = filepath
            label.thumbnail_frame = thumbnail_frame

            # Bind a click event to the Label, to toggle selection
            label.bind(
                "<Button-1>", lambda e, lbl=label: self.toggle_thumbnail_selection(lbl)
            )

            # Increment the row and column
            col += 1
            if col >= self.thumbnails_cols:
                col = 0
                row += 1

        # Return the thumbnail objects to prevent garbage collection
        return thumbnails

    def toggle_thumbnail_selection(self, label):
        """Toggle the selection state of a thumbnail.

        Args:
            label: The ttk.Label widget representing the thumbnail.
        """
        if label in self.selected_thumbnails:
            # Deselect the thumbnail and remove the visual indicator
            self.selected_thumbnails.remove(label)
            label.thumbnail_frame.configure(relief="flat")
        else:
            # Select the thumbnail and add a visual indicator
            self.selected_thumbnails.append(label)
            label.thumbnail_frame.configure(relief="solid")

        print([t.filepath for t in self.selected_thumbnails])

    def populate_thumbnails(self):
        """Populate the thumbnails container with duplicate photos from the database.

        Retrieves all duplicate photos grouped by hash from the database,
        clears any existing thumbnails, and displays each group of duplicates
        in separate frames. Maintains references to thumbnail objects to
        prevent garbage collection.
        """
        # Grab the duplicate photos, grouped by hash
        db_rows = self.database.get_duplicate_photos()

        # Remove any previous thumbnail groups
        for child in self.thumbnails_container.frame.winfo_children():
            child.destroy()

        # Will need to save the thumbnail objects, to avoid garbage collection
        self.hash_and_thumbnails = {}

        frame_row = 0
        for hash, concat_filepaths in db_rows:
            # Get the list of filepaths
            filepaths = concat_filepaths.split(",")

            # Create a new Frame for the hash's thumbnails
            hash_frame = ttk.Frame(self.thumbnails_container.frame)
            hash_frame.grid(row=frame_row, column=0)
            frame_row += 1

            # Put the thumbnails into the frame
            thumbnails = self.display_thumbnails_in_frame(hash_frame, filepaths)

            # Save the thumbnail objects, to avoid garbage collection
            self.hash_and_thumbnails[hash] = thumbnails
