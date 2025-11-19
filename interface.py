from tkinter import E, N, S, StringVar, Tk, W, ttk

from PIL import Image, ImageTk

from widgets import OutlinedFrame, VerticalScrollFrame


class Interface:
    def __init__(self, database, finder):
        self.finder = finder
        self.database = database

        # Reference to each hash's thumbnail objects, to prevent garbage collection
        self.hash_and_thumbnails = {}

        # Instantiate the Tk root window
        self.tk_root = Tk()

        # Create the GUI
        self.create_gui()

        # Fill the thumbnails frame with duplicate thumbnails
        self.populate_thumbnails()

        # Spin up the GUI
        self.tk_root.mainloop()

    def create_gui(self):
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
        self.scanning_text.set("Scanning for photo files...")

        # Hash the photo files and store in the database
        filepaths = self.finder.find_photo_filepaths()
        num_photos = len(filepaths)
        for i, filepath in enumerate(filepaths, 1):
            self.scanning_text.set(f"Analyzing photo {i}/{num_photos}...")
            self.finder.compute_file_hash(filepath)

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
