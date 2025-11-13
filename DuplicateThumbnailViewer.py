import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk


class DuplicateThumbnailViewer:
    """
    GUI class for viewing and managing duplicate photos in a thumbnail grid.
    """

    def __init__(self, duplicate_finder):
        self.duplicate_finder = duplicate_finder
        self.root = None
        self.thumbnail_images = []  # Keep references to prevent garbage collection

    def delete_photo_with_confirmation(self, photo_path, frame, root):
        """
        Deletes a photo file with confirmation dialog and removes it from the UI.

        Args:
            photo_path (str): Path to the photo file to delete
            frame (ttk.Frame): The frame containing the photo to remove
            root (tk.Tk): The main window to refresh
        """
        filename = os.path.basename(photo_path)

        # Show confirmation dialog
        result = messagebox.askyesno(
            "Confirm Deletion",
            f'Are you sure you want to delete "{filename}"?\n\n'
            f"This action cannot be undone.",
            icon="warning",
        )

        if result:
            try:
                # Delete the file from filesystem
                os.remove(photo_path)
                print(f"Successfully deleted: {filename}")

                # Update the duplicate finder's cache data
                self.update_cache_after_deletion(photo_path)

                # Remove the frame from the grid
                frame.destroy()

                # Update the scroll region and grid layout
                canvas = None
                scrollable_frame = None
                for child in root.winfo_children():
                    if isinstance(child, tk.Canvas):
                        canvas = child
                        # Find the scrollable frame inside the canvas
                        for canvas_child in canvas.winfo_children():
                            if isinstance(canvas_child, ttk.Frame):
                                scrollable_frame = canvas_child
                                break
                        break

                if canvas and scrollable_frame:
                    # Reconfigure the grid to close gaps
                    self.reconfigure_grid_layout(scrollable_frame)
                    # Update scroll region
                    canvas.configure(scrollregion=canvas.bbox("all"))

            except FileNotFoundError:
                messagebox.showerror("Error", f"File not found: {filename}")
            except OSError as e:
                messagebox.showerror("Error", f"Could not delete file: {e}")

    def update_cache_after_deletion(self, deleted_file_path):
        """Update the cache data after a file is deleted."""
        # Remove from files list
        if deleted_file_path in self.duplicate_finder.cache_data["files"]:
            self.duplicate_finder.cache_data["files"].remove(deleted_file_path)

        # Remove from hashes entries
        for file_hash, files in self.duplicate_finder.cache_data["hashes"].items():
            if deleted_file_path in files:
                files.remove(deleted_file_path)
                # If no files left for this hash, remove the hash entry
                if not files:
                    del self.duplicate_finder.cache_data["hashes"][file_hash]
                break

        # Write updated cache to file
        self.duplicate_finder.write_cache_file()

    def reconfigure_grid_layout(self, scrollable_frame):
        """
        Reorganizes the grid layout after a frame is destroyed to close gaps.

        Args:
            scrollable_frame (ttk.Frame): The frame containing the grid layout
        """
        # Get all children of the scrollable frame
        children = scrollable_frame.winfo_children()

        # Separate regular frames from separators
        frames = []
        separators = []

        for child in children:
            if isinstance(child, tk.Frame) and child.cget("bg") == "red":
                # This is a separator
                grid_info = child.grid_info()
                separators.append((child, grid_info.get("row", 0)))
            elif isinstance(child, ttk.Frame):
                # This is a thumbnail frame
                grid_info = child.grid_info()
                frames.append(
                    (child, grid_info.get("row", 0), grid_info.get("column", 0))
                )

        # Sort by row, then column
        frames.sort(key=lambda x: (x[1], x[2]))
        separators.sort(key=lambda x: x[1])

        # Clear all grid positions
        for child in children:
            child.grid_forget()

        # Reorganize frames in a 4-column grid
        row = 0
        col = 0

        for frame, old_row, old_col in frames:
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            col += 1
            if col >= 4:  # 4 columns
                col = 0
                row += 1

        # Re-add separators at appropriate positions
        for separator, old_row in separators:
            separator.grid(
                row=row, column=0, columnspan=4, sticky="ew", padx=10, pady=20
            )
            row += 1

    def show_duplicates_grid(self):
        """Show all duplicate groups in a thumbnail grid with separators."""
        # Get all duplicate groups
        duplicate_entries = [
            (hash_key, files)
            for hash_key, files in self.duplicate_finder.cache_data["hashes"].items()
            if len(files) > 1
        ]

        if not duplicate_entries:
            messagebox.showinfo("No Duplicates", "No duplicate groups found!")
            return

        # Flatten all duplicate files into a single list with group separators
        all_photos = []
        for i, (file_hash, photo_files) in enumerate(duplicate_entries):
            all_photos.extend(photo_files)
            # Add a separator marker between groups (except for the last group)
            if i < len(duplicate_entries) - 1:
                all_photos.append(None)  # None represents a separator

        self.open_photos_thumbnail_grid(all_photos)

    def open_photos_thumbnail_grid(self, photo_files):
        """
        Opens all photos in a thumbnail grid using a Tkinter window.
        This allows you to see all photos at once for easy comparison.
        Click on any thumbnail to open the full-size image.
        Click the X button to delete a photo (with confirmation).
        """
        if not photo_files:
            print("No photos to open.")
            return

        num_photos = len([f for f in photo_files if f is not None])
        print(f"Creating thumbnail grid for {num_photos} photos...")

        # Create the main window
        self.root = tk.Tk()
        self.root.title("Photo Duplicate Viewer - Manage Duplicates")
        # Increase width to better accommodate 4 columns with padding and scrollbar
        self.root.geometry("1600x900")

        # Create a scrollable frame
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Thumbnail size
        thumb_size = (200, 200)

        # Create thumbnails with memory optimization
        self.thumbnail_images = []  # Keep references to prevent garbage collection
        row = 0
        col = 0

        for i, photo_path in enumerate(photo_files):
            if photo_path is None:  # Separator
                # Create separator line
                separator = tk.Frame(scrollable_frame, height=2, bg="red")
                separator.grid(
                    row=row, column=0, columnspan=4, sticky="ew", padx=10, pady=20
                )
                row += 1
                col = 0
                continue

            if not os.path.exists(photo_path):
                print(f"Warning: File does not exist: {photo_path}")
                continue

            try:
                # Open and resize the image with optimized settings
                with Image.open(photo_path) as img:
                    # Convert to RGB if necessary to avoid mode issues
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")
                    # Create thumbnail while preserving aspect ratio
                    img.thumbnail(thumb_size, Image.Resampling.LANCZOS)

                    # Convert to PhotoImage for tkinter
                    photo = ImageTk.PhotoImage(img, master=self.root)
                    self.thumbnail_images.append(photo)  # Keep reference to prevent GC

                    # Create frame for this thumbnail
                    frame = ttk.Frame(scrollable_frame, relief="raised", borderwidth=1)
                    frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                    # Ensure frame can expand to fill available space
                    frame.grid_propagate(False)

                    # Create a container frame for positioning the delete button
                    container_frame = tk.Frame(frame, bg="white")
                    container_frame.pack(fill="both", expand=True)

                    # Create label with image
                    label = ttk.Label(container_frame, image=photo)
                    label.pack(padx=5, pady=5)

                    # Add filename below the image
                    filename = os.path.basename(photo_path)
                    filename_label = ttk.Label(
                        container_frame, text=filename, wraplength=180
                    )
                    filename_label.pack(padx=5, pady=(0, 5))

                    # Create delete button (X) in top-right corner
                    delete_button = tk.Button(
                        container_frame,
                        text="✕",
                        font=("Arial", 14, "bold"),
                        fg="white",
                        bg="red",
                        activebackground="darkred",
                        activeforeground="white",
                        relief="raised",
                        bd=1,
                        width=3,
                        height=1,
                        cursor="hand2",
                    )

                    # Position the delete button in top-right corner of container
                    delete_button.place(relx=1.0, rely=0.0, x=-5, y=5, anchor="ne")

                    # Add click handler to open full-size image
                    def open_full_size(path=photo_path):
                        subprocess.Popen(
                            ["xdg-open", path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )

                    # Add click handler for delete button
                    def delete_photo(path=photo_path):
                        self.delete_photo_with_confirmation(path, frame, self.root)

                    # Bind events
                    label.bind(
                        "<Button-1>", lambda e, path=photo_path: open_full_size(path)
                    )
                    filename_label.bind(
                        "<Button-1>", lambda e, path=photo_path: open_full_size(path)
                    )
                    delete_button.configure(command=delete_photo)

                    # Prevent delete button clicks from triggering image opening
                    delete_button.bind(
                        "<Button-1>", lambda e: e.widget.invoke(), add="+"
                    )

                    # Move to next position
                    col += 1
                    if col >= 4:  # 4 columns
                        col = 0
                        row += 1

            except Exception as e:
                print(f"Error processing {photo_path}: {e}")
                # Create error placeholder
                frame = ttk.Frame(scrollable_frame, relief="raised", borderwidth=1)
                frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
                # Ensure frame can expand to fill available space
                frame.grid_propagate(False)

                error_label = ttk.Label(
                    frame, text=f"Error loading:\n{os.path.basename(photo_path)}"
                )
                error_label.pack(padx=5, pady=5)

                col += 1
                if col >= 4:
                    col = 0
                    row += 1

        # Configure grid weights for responsive layout
        for i in range(4):  # 4 columns
            scrollable_frame.columnconfigure(i, weight=1)

        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Update the scroll region after all widgets are created
        self.root.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        # Add instructions
        instructions = ttk.Label(
            self.root,
            text="Click on any thumbnail to open the full-size image. "
            "Click the ✕ button to delete a photo.",
        )
        instructions.pack(side="bottom", pady=5)

        print(
            "Thumbnail grid created! Click on any image to open it full-size. "
            "Click the ✕ button to delete photos."
        )
        self.root.mainloop()
