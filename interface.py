"""Graphical user interface for the duplicate photo finder application.

This module provides the Interface class which creates and manages a Tkinter-based
GUI for displaying duplicate photos, scanning directories, and managing photo deletion.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from os import cpu_count
from sqlite3 import IntegrityError
from tkinter import E, N, S, StringVar, TclError, Tk, W, filedialog, messagebox, ttk

from PIL import Image, ImageTk
from tktooltip import ToolTip

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
        self._debounce_running = None

        # Number of columns the thumbnails should take up at max
        self.thumbnails_cols = 4

        # Reference to each hash's thumbnail objects, to prevent garbage collection
        self.hash_and_thumbnails = {}

        # List of selected thumbnails
        self.selected_filepaths = set()

        # Instantiate the Tk root window
        self.tk_root = Tk()

        # Update the database pagination info
        self.database.update_num_pages(self.finder.directory_to_scan)

        # Create the GUI
        self.create_gui()

        # Fill the thumbnails frame with duplicate thumbnails
        self.display_thumbnails()

        # Set the scanning text
        self.update_scanning_text("Click to scan")

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
        self.scan_button = ttk.Button(
            controls_frame, text="Scan", command=self.scan_for_duplicates
        )
        self.scan_button.grid(column=0, row=0, sticky=W)

        # Scanning text, stretched horizontally
        self.scanning_text = StringVar(value="Click to scan")
        scanning_label = ttk.Label(controls_frame, textvariable=self.scanning_text)
        scanning_label.grid(column=2, row=0, padx=5)
        controls_frame.columnconfigure(1, weight=1)

        # Delete button
        self.delete_button = ttk.Button(
            controls_frame,
            text="Delete",
            state="disabled",
            command=self.show_delete_confirm_modal,
        )
        self.delete_button.grid(column=3, row=0, sticky=E)

        # Frame that holds the thumbnails. Stretch it in all directions.
        self.thumbnails_container = VerticalScrollFrame(
            main_frame, width=1000, height=500, relief="ridge", borderwidth=2
        )
        self.thumbnails_container.grid(column=0, row=1, sticky=(N, S, E, W))
        self.thumbnails_container.columnconfigure(0, weight=1)
        self.thumbnails_container.rowconfigure(0, weight=1)

        # Frame that holds the navigation. Stretch it horizontally.
        navigation_frame = OutlinedFrame(main_frame, height=100)
        navigation_frame.grid(column=0, row=2, sticky=(E, W))

        # Previous page button
        self.prev_page_button = ttk.Button(
            navigation_frame,
            text="Prev Page",
            state="disabled",
            command=self.go_to_prev_page,
        )
        self.prev_page_button.grid(column=0, row=0, sticky=E)

        # Text displaying number of pages
        self.num_pages_text = StringVar(
            value=f"Page {self.database.page_number} of {self.database.num_pages}"
        )
        pages_label = ttk.Label(navigation_frame, textvariable=self.num_pages_text)
        pages_label.grid(column=1, row=0, padx=5, sticky=E)

        # Next page button
        self.next_page_button = ttk.Button(
            navigation_frame,
            text="Next Page",
            state="!disabled" if self.database.page_number else "disabled",
            command=self.go_to_next_page,
        )
        self.next_page_button.grid(column=2, row=0, sticky=E)

        # Label with the directory we're scanning
        self.directory_to_scan_text = StringVar(
            value=f"Selected folder: {self.finder.directory_to_scan}"
        )
        directory_to_scan_label = ttk.Label(
            navigation_frame, textvariable=self.directory_to_scan_text
        )
        directory_to_scan_label.grid(column=3, row=0, sticky=W)

        # Select directory button
        self.select_directory_button = ttk.Button(
            navigation_frame,
            text="Select Folder",
            command=self.open_select_directory_dialog,
        )
        self.select_directory_button.grid(column=4, row=0, sticky=W, padx=5)

        # Fill the Tk root window with the main frame
        self.tk_root.columnconfigure(0, weight=1)
        self.tk_root.rowconfigure(0, weight=1)

        # Fill the main frame with the first column and the thumbnails row
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def open_select_directory_dialog(self):
        new_dir = filedialog.askdirectory(initialdir=self.finder.directory_to_scan)
        if new_dir:
            self.finder.directory_to_scan = new_dir

            self.directory_to_scan_text.set(
                f"Selected folder: {self.finder.directory_to_scan}"
            )
            self.tk_root.update()

    def _debounce(self, delay, fn, args=None, kwargs=None):

        if self._debounce_running is not None:
            self.tk_root.after_cancel(self._debounce_running)

        self._debounce_running = self.tk_root.after(
            delay,
            lambda fn=fn, args=args, kwargs=kwargs: self._call_debounce_fn(
                fn, args, kwargs
            ),
        )

    def _call_debounce_fn(self, fn, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        fn(*args, **kwargs)
        self._debounce_running = None

    def go_to_prev_page(self):
        """Navigate to the previous page of duplicate photo groups.

        Decrements the current page number (minimum 1), updates button states,
        updates the page label, and refreshes the thumbnail display.
        """
        self.database.page_number = max(1, self.database.page_number - 1)
        self.update_prev_next_button_states()
        self.update_num_pages_label()
        self._debounce(500, self.display_thumbnails)

    def go_to_next_page(self):
        """Navigate to the next page of duplicate photo groups.

        Increments the current page number (maximum num_pages), updates button
        states, updates the page label, and refreshes the thumbnail display.
        """
        self.database.page_number = min(
            self.database.page_number + 1, self.database.num_pages
        )
        self.update_prev_next_button_states()
        self.update_num_pages_label()
        self._debounce(500, self.display_thumbnails)

    def update_prev_next_button_states(self):
        """Update the enabled/disabled state of pagination buttons.

        Disables the "Previous" button when on page 1, and disables the
        "Next" button when on the last page. Enables both buttons otherwise.
        """
        self.prev_page_button.state(
            ["disabled" if self.database.page_number <= 1 else "!disabled"]
        )
        self.next_page_button.state(
            [
                (
                    "disabled"
                    if self.database.page_number >= self.database.num_pages
                    else "!disabled"
                )
            ]
        )

    def update_num_pages_label(self):
        """Update the pagination label text with current page information.

        Sets the label text to show the current page number and total number
        of pages, then forces a GUI update to reflect the change.
        """
        # Update the pagination UI
        self.num_pages_text.set(
            f"Page {self.database.page_number} of {self.database.num_pages}"
        )
        self.tk_root.update()

    def show_delete_confirm_modal(self):
        """Display a confirmation dialog before deleting selected photos.

        Shows a yes/no dialog asking the user to confirm deletion of the
        currently selected photos. If the user confirms, calls
        delete_selected_photos() to perform the deletion.
        """
        # Show a confirmation modal to the user
        num_photos = len(self.selected_filepaths)
        response = messagebox.askyesno(
            title="Confirm Delete Photos",
            message=(
                "Are you sure you want to delete the selected "
                f"{num_photos} photo{'' if num_photos == 1 else 's'}?"
            ),
        )

        # If Yes is selected
        if response is True:
            self.delete_selected_photos()

    def delete_selected_photos(self):
        """Delete the selected photos from disk and database.

        Removes the selected photo files from the filesystem, deletes their
        database entries, updates the thumbnail display, and shows a success
        message. Clears the selection after deletion is complete.
        """
        # Delete the photos from the hard drive
        self.finder.delete_selected_photos(self.selected_filepaths)

        # Remove the entry from the database
        try:
            self.database.delete_photos(self.selected_filepaths)
        except IntegrityError:
            pass

        # Visually disable the delete button
        self.delete_button.state(["disabled"])

        # Update the thumbnails
        self.update_scanning_text("Updating thumbnails...")
        self.display_thumbnails()

        # Reset the scanning text
        self.update_scanning_text("Scan complete!")

        # Let the user know that the files have been deleted
        num_photos = len(self.selected_filepaths)
        messagebox.showinfo(
            title="Photos Deleted!",
            message=(
                f"Successfully deleted {num_photos} "
                f"photo{'' if num_photos == 1 else 's'}"
            ),
        )

        # Clear out the selected photos list
        self.selected_filepaths.clear()

    def scan_for_duplicates(self):
        """Scan for duplicate photos and update the display.

        Finds all photo files in the configured directory, computes their
        hashes, stores them in the database, and updates the thumbnail
        display to show newly found duplicates. Updates the status text
        throughout the scanning process.
        """
        # Update the scanning text
        self.update_scanning_text("Scanning for photo files...")

        # Get the filepaths of all photos on the hard drive
        filepaths = self.finder.find_photo_filepaths()
        if not filepaths:
            return

        # Check which filepaths already exist in the database
        self.update_scanning_text("Checking existing files...")
        filepaths_in_database = self.database.get_existing_filepaths(filepaths)

        # Separate files into existing and new
        new_filepaths = [fp for fp in filepaths if fp not in filepaths_in_database]

        # Batch update all existing database rows with the current timestamp
        now = datetime.now()
        if filepaths_in_database:
            try:
                self.database.batch_update_lastseen(filepaths_in_database, now)
            except IntegrityError:
                pass

        # Process new files: compute hashes and prepare for batch insert
        new_photos_data = []
        if new_filepaths:
            new_photos_data = self.compute_file_hashes(new_filepaths, now)

        # Batch insert all new photos
        if new_photos_data:
            try:
                self.database.batch_insert_new_photos(new_photos_data)
            except IntegrityError:
                pass

        # Any records in the database that didn't get their lastseen column updated
        # don't exist on the filesystem anymore. They can be purged.
        try:
            self.database.delete_stale_photos(self.finder.directory_to_scan, now)
        except IntegrityError:
            pass

        # Update the database pagination info
        self.database.update_num_pages(self.finder.directory_to_scan)

        # Update the thumbnails
        self.update_scanning_text("Updating thumbnails...")
        self.display_thumbnails()

        # Update the pagination UI
        self.update_prev_next_button_states()
        self.update_num_pages_label()

        # Reset the scanning text
        self.update_scanning_text("Scan complete!")

    def update_scanning_text(self, text):
        self.scanning_text.set(text)
        self.tk_root.update()  # Final GUI update

    def compute_file_hashes(self, new_filepaths, now):
        print("Computing file hashes...")
        new_photos_data = []
        for i, filepath in enumerate(new_filepaths, 1):
            # Update GUI every 50 files to reduce overhead
            if i % 50 == 0 or i == len(new_filepaths):
                self.update_scanning_text(
                    f"Analyzing new photos {i}/{len(new_filepaths)}..."
                )

            filepath, file_hash = self.finder.dhash_file(filepath)
            if file_hash:
                new_photos_data.append((filepath, file_hash, now))

        return new_photos_data

    def compute_file_hashes_multiprocessing(self, new_filepaths, now):
        new_photos_data = []

        # Use multiprocessing to hash files in parallel
        # Determine optimal number of workers
        # (use CPU count, but cap at reasonable limit)
        max_workers = min(cpu_count() or 4, len(new_filepaths), 8)

        completed_count = 0
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all hashing tasks
            future_to_filepath = {
                executor.submit(self.finder.dhash_file, filepath): filepath
                for filepath in new_filepaths
            }

            # Process results as they complete
            for future in as_completed(future_to_filepath):
                completed_count += 1

                # Update GUI every 50 files to reduce overhead
                should_update = completed_count % 50 == 0 or completed_count == len(
                    new_filepaths
                )
                if should_update:
                    self.update_scanning_text(
                        f"Analyzing new photos "
                        f"{completed_count}/{len(new_filepaths)}..."
                    )

                try:
                    filepath, file_hash = future.result()
                    if file_hash:
                        new_photos_data.append((filepath, file_hash, now))
                except Exception as e:
                    # Handle any errors from the worker process
                    print(f"Error processing {future_to_filepath[future]}: {e}")
                    continue

        return new_photos_data

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
            try:
                thumbnail_frame = ttk.Frame(
                    hash_frame,
                    borderwidth=3,
                    relief="solid" if filepath in self.selected_filepaths else "flat",
                )
                thumbnail_frame.grid(row=row, column=col, padx=5, pady=5)

                # Display the thumbnail within the frame
                thumbnail_label = ttk.Label(thumbnail_frame, image=thumbnail)
                thumbnail_label.pack()

                # Add in filepath and frame attributes to the Label, for later reference
                thumbnail_label.filepath = filepath
                thumbnail_label.thumbnail_frame = thumbnail_frame

                # Bind a click event to the Label, to toggle selection
                thumbnail_label.bind(
                    "<Button-1>",
                    lambda e, fp=filepath, t_f=thumbnail_frame: (
                        self.toggle_filepath_selection(fp, t_f)
                    ),
                )

                # Add a tooltip to the thumbnail
                ToolTip(thumbnail_label, msg=filepath)

                # Add the filepath underneath the thumbnail
                filename = filepath.split("/")[-1]
                filepath_label = ttk.Label(thumbnail_frame, text=filename)
                filepath_label.pack()

                self.tk_root.update()  # Force GUI update
            except TclError:
                pass

            # Increment the row and column
            col += 1
            if col >= self.thumbnails_cols:
                col = 0
                row += 1

        # Return the thumbnail objects to prevent garbage collection
        return thumbnails

    def toggle_filepath_selection(self, filepath, thumbnail_frame):
        """Toggle the selection state of a photo thumbnail.

        Args:
            filepath: Path to the photo file to toggle selection for.
            thumbnail_frame: Tkinter Frame widget containing the thumbnail.
                The frame's relief is updated to visually indicate selection
                state (solid for selected, flat for unselected).

        If the filepath is already selected, it is removed from the selection
        and the frame border is set to flat. If not selected, it is added to
        the selection and the frame border is set to solid. The delete button
        is enabled if any photos are selected, disabled otherwise.
        """
        if filepath in self.selected_filepaths:
            self.selected_filepaths.remove(filepath)
            thumbnail_frame.configure(relief="flat")
        else:
            self.selected_filepaths.add(filepath)
            thumbnail_frame.configure(relief="solid")

        # Enable or disable the Delete button
        self.delete_button.state(
            ["!disabled" if self.selected_filepaths else "disabled"]
        )

    def display_thumbnails(self):
        """Populate the thumbnails container with duplicate photos from the database.

        Retrieves all duplicate photos grouped by hash from the database,
        clears any existing thumbnails, and displays each group of duplicates
        in separate frames. Maintains references to thumbnail objects to
        prevent garbage collection.
        """

        # Grab the duplicate photos, grouped by hash
        db_rows = self.database.query_database(self.finder.directory_to_scan)

        # Remove any previous thumbnail groups
        for child in self.thumbnails_container.frame.winfo_children():
            child.destroy()

        # Will need to save the thumbnail objects, to avoid garbage collection
        self.hash_and_thumbnails = {}

        row_index = 0
        num_rows = len(db_rows)
        for i, (hash, concat_filepaths) in enumerate(db_rows, 1):
            # Update the scanning text at the top
            self.update_scanning_text(f"Displaying duplicate group {i}/{num_rows}...")

            # Get the list of filepaths
            filepaths = concat_filepaths.split(",")

            # Create a new Frame for the hash's thumbnails
            hash_frame = ttk.Frame(self.thumbnails_container.frame)
            hash_frame.grid(row=row_index, column=0, sticky=(W))
            row_index += 1

            # Put the thumbnails into the frame
            thumbnails = self.display_thumbnails_in_frame(hash_frame, filepaths)

            # Put in a visual separator spanning the full width of the frame
            separator = ttk.Separator(
                self.thumbnails_container.frame, orient="horizontal"
            )
            separator.grid(row=row_index, column=0, sticky=(E, W), padx=10, pady=5)
            row_index += 1

            # Save the thumbnail objects, to avoid garbage collection
            self.hash_and_thumbnails[hash] = thumbnails
