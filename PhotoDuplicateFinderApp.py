import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from DuplicateThumbnailViewer import DuplicateThumbnailViewer
from PhotoDuplicateFinder import PhotoDuplicateFinder


class PhotoDuplicateFinderApp:
    """
    Main GUI application for finding and managing duplicate photos.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Photo Duplicate Finder")
        self.root.geometry("600x550")
        self.root.resizable(True, True)

        # Initialize the duplicate finder
        self.duplicate_finder = PhotoDuplicateFinder()

        # Create the main interface
        self.create_main_interface()

    def create_main_interface(self):
        """Create the main application interface."""
        # Title
        title_label = ttk.Label(
            self.root, text="Photo Duplicate Finder", font=("Arial", 20, "bold")
        )
        title_label.pack(pady=20)

        # Subtitle
        subtitle_label = ttk.Label(
            self.root,
            text="Find and remove duplicate photos in your collection",
            font=("Arial", 10),
        )
        subtitle_label.pack(pady=(0, 30))

        # Directory selection frame
        dir_frame = ttk.LabelFrame(self.root, text="Select Photo Directory", padding=20)
        dir_frame.pack(fill="x", padx=20, pady=10)

        # Current directory display
        self.dir_label = ttk.Label(
            dir_frame, text="No directory selected", foreground="gray"
        )
        self.dir_label.pack(pady=(0, 10))

        # Select directory button
        self.select_dir_btn = ttk.Button(
            dir_frame, text="Select Folder", command=self.select_directory
        )
        self.select_dir_btn.pack()

        # Scan button (initially disabled)
        self.scan_btn = ttk.Button(
            self.root,
            text="Scan for Duplicates",
            command=self.start_scanning,
            state="disabled",
        )
        self.scan_btn.pack(pady=20)

        # Progress frame
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.pack(fill="x", padx=20, pady=10)

        # Progress bar
        self.progress_var = tk.StringVar(value="Ready to scan...")
        self.progress_label = ttk.Label(
            self.progress_frame, textvariable=self.progress_var
        )
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=(5, 0))

        # Results frame
        self.results_frame = ttk.LabelFrame(self.root, text="Results", padding=20)
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Results label
        self.results_label = ttk.Label(
            self.results_frame, text="No scan performed yet", foreground="gray"
        )
        self.results_label.pack()

        # Manage duplicates button (initially hidden)
        self.manage_btn = ttk.Button(
            self.results_frame,
            text="Manage Duplicates",
            command=self.open_duplicate_viewer,
            state="disabled",
        )
        self.manage_btn.pack(pady=10)

    def select_directory(self):
        """Open folder selection dialog."""
        directory = filedialog.askdirectory(
            title="Select folder to scan for duplicate photos"
        )

        if directory:
            self.duplicate_finder.directory_to_scan = directory
            self.duplicate_finder.cache_file = os.path.join(
                directory, self.duplicate_finder.cache_filename
            )

            # Update UI
            self.dir_label.config(text=directory, foreground="black")
            self.scan_btn.config(state="normal")
            self.progress_var.set("Ready to scan...")

    def start_scanning(self):
        """Start the duplicate scanning process in a separate thread."""
        if not self.duplicate_finder.directory_to_scan:
            messagebox.showerror("Error", "Please select a directory first.")
            return

        # Disable buttons during scanning
        self.select_dir_btn.config(state="disabled")
        self.scan_btn.config(state="disabled")

        # Start progress bar
        self.progress_bar.start()
        self.progress_var.set("Scanning directory for images...")

        # Start scanning in a separate thread
        scan_thread = threading.Thread(target=self.scan_directory)
        scan_thread.daemon = True
        scan_thread.start()

    def scan_directory(self):
        """Perform the actual directory scanning."""
        try:
            # Load existing hash data if cache file exists
            if os.path.isfile(self.duplicate_finder.cache_file):
                self.root.after(
                    0, lambda: self.progress_var.set("Loading existing cache...")
                )
                self.duplicate_finder.read_cache_file()

            # Scan directory and compute hashes
            self.root.after(
                0, lambda: self.progress_var.set("Computing file hashes...")
            )
            self.duplicate_finder.extract_file_hashes()

            # Write the data to the cache file
            self.duplicate_finder.write_cache_file()

            # Update UI with results
            self.root.after(0, self.scan_complete)

        except Exception as error:
            self.root.after(0, lambda: self.scan_error(str(error)))

    def scan_complete(self):
        """Called when scanning is complete."""
        # Stop progress bar
        self.progress_bar.stop()

        # Count duplicates
        num_duplicates = self.duplicate_finder.calculate_num_duplicates()
        total_files = len(self.duplicate_finder.cache_data["files"])

        if num_duplicates == 0:
            self.results_label.config(
                text=f"Scan complete! No duplicates found in {total_files} files.",
                foreground="green",
            )
            # self.manage_btn.pack_forget()
            self.manage_btn.config(state="disabled")
        else:
            self.results_label.config(
                text=(
                    f"Found {num_duplicates} groups of duplicates "
                    f"in {total_files} files."
                ),
                foreground="orange",
            )
            self.manage_btn.config(state="normal")

        self.progress_var.set("Scan complete!")

        # Re-enable buttons
        self.select_dir_btn.config(state="normal")
        self.scan_btn.config(state="normal")

    def scan_error(self, error_message):
        """Called when scanning encounters an error."""
        self.progress_bar.stop()
        self.progress_var.set("Scan failed!")

        messagebox.showerror(
            "Scan Error", f"An error occurred during scanning:\n{error_message}"
        )

        # Re-enable buttons
        self.select_dir_btn.config(state="normal")
        self.scan_btn.config(state="normal")

    def open_duplicate_viewer(self):
        """Open the duplicate thumbnail viewer."""
        viewer = DuplicateThumbnailViewer(self.duplicate_finder)
        viewer.show_duplicates_grid()

    def run(self):
        """Start the application."""
        self.root.mainloop()
