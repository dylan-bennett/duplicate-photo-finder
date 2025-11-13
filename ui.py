from tkinter import *
from tkinter import ttk

from PIL import Image, ImageTk


class OutlinedFrame(ttk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, relief="ridge", borderwidth=2)


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
        self.thumbnails_cols = 5
        self.thumbnails_frame = OutlinedFrame(main_frame, height=500, width=1000)
        self.thumbnails_frame.grid(column=0, row=1, sticky=(N, S, E, W))

        # Fill the root window with the main frame
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Fill the main frame with the first column and the thumbnails row
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Fill the thumbnails frame with duplicate thumbnails
        # NOTE: We need to save a reference to the thumbnails, otherwise they will be garbage-collected
        self.thumbnails = self.populate_thumbnails()

    def scan_for_duplicates(self):
        # Hash the photo files and store in the database
        duplicate_photo_finder = DuplicatePhotoFinder(database=self.database_connection)
        duplicate_photo_finder.compute_file_hashes()

        # Update the thumbnails
        self.populate_thumbnails()

    def populate_thumbnails(self):
        # Create a cursor to navigate through the database
        database_cursor = self.database_connection.cursor()

        # Grab the photos (TEMP FOR TESTING -- NEED TO UPDATE QUERY TO GROUP BY HASH)
        database_cursor.execute("SELECT filepath FROM photos;")
        db_rows = database_cursor.fetchall()

        # Display the photos as thumbnails
        thumbnails = []
        for db_row in db_rows:
            filepath = db_row[0]

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
            label = ttk.Label(self.thumbnails_frame, image=thumbnail)
            label.grid(row=row, column=col, padx=5, pady=5)

            # Increment the row and column
            col += 1
            if col >= self.thumbnails_cols:
                col = 0
                row += 1

        # Return the thumbnail objects to prevent garbage collection
        return thumbnails
