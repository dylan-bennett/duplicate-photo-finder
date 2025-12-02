"""Photo file discovery and hashing functionality.

This module provides the Finder class for locating photo files in a directory,
computing MD5 hashes to identify duplicates, and managing file deletion operations.
"""

import os
from pathlib import Path


class Finder:
    def __init__(self, database, directories_to_scan=None):
        """Initialize the Finder with a database and directory to scan.

        Args:
            database: Database instance for storing and checking photo hashes.
            directory_to_scan: Path to the directory to scan for photo files.
            directories_to_scan: List of paths to the directories to scan.

        Sets up the finder with supported image extensions (.png, .jpg, .jpeg,
        .gif, .bmp) and stores references to the database and scan directory.
        """
        # self.directory_to_scan = directory_to_scan or Path.home()
        self.directories_to_scan = directories_to_scan or [Path.home()]
        self.valid_image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
        self.database = database

    def find_photo_filepaths(self):
        """Find all photo file paths in the configured directory.

        Returns:
            List of file paths to image files found in the directory and
            all subdirectories. Only files with supported image extensions
            (.png, .jpg, .jpeg, .gif, .bmp) are included.

        Recursively walks through the directory tree and collects paths
        to all files matching the valid image extensions.
        """
        filepaths = []

        # Recursively walk through directories and subdirectories
        for directory in self.directories_to_scan:
            for root, _, files in os.walk(directory):
                for filename in files:
                    # Check if file has a supported image extension
                    file_ext = os.path.splitext(filename)[1].lower()
                    if file_ext not in self.valid_image_extensions:
                        continue

                    # Get the full file path
                    filepath = os.path.join(root, filename)

                    filepaths.append(filepath)

        return filepaths

    def delete_selected_photos(self, filepaths):
        """Delete photo files from the filesystem.

        Args:
            filepaths: Iterable of file paths to delete.

        Attempts to delete each file path from the filesystem. If a file
        doesn't exist, it is skipped with a warning message. If deletion
        fails due to an OSError, the error is printed and the next file
        is processed.
        """
        for filepath in filepaths:
            if os.path.exists(filepath):
                # Delete the photo from the system
                try:
                    os.remove(filepath)
                except OSError as e:
                    print(f"Error deleting {filepath}: {e}")
                    continue

            else:
                print(f"File not found, skipping: {filepath}")
