"""Photo file discovery and hashing functionality.

This module provides the Finder class for locating photo files in a directory,
computing MD5 hashes to identify duplicates, and managing file deletion operations.
"""

import hashlib
import os

import imagehash
from PIL import Image


class Finder:
    def __init__(self, database, directory_to_scan):
        """Initialize the Finder with a database and directory to scan.

        Args:
            database: Database instance for storing and checking photo hashes.
            directory_to_scan: Path to the directory to scan for photo files.

        Sets up the finder with supported image extensions (.png, .jpg, .jpeg,
        .gif, .bmp) and stores references to the database and scan directory.
        """
        self.directory_to_scan = directory_to_scan
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

        # Recursively walk through directory and subdirectories
        for root, _, files in os.walk(self.directory_to_scan):
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

    def hash_file(self, filepath):
        """Compute the MD5 hash of a file.

        Args:
            filepath: Path to the file to hash.

        Returns:
            str: Hexadecimal MD5 hash digest of the file.

        Raises:
            IOError: If the file cannot be read.
            OSError: If there is an operating system error accessing the file.

        Reads the file in 8KB chunks to efficiently compute the hash
        without loading the entire file into memory.
        """
        try:
            # Compute MD5 hash using chunked reading for memory efficiency
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                # Read file in chunks to avoid loading large files
                # entirely into memory
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()

        except (IOError, OSError) as e:
            print(f"Warning: Could not read file {filepath}: {e}")
            raise

    def dhash_file(self, filepath):
        try:
            return str(imagehash.dhash(Image.open(filepath)))
        except Exception as e:
            print(f"Problem {e} with {filepath}")
            raise

    def compute_file_hash(self, filepath):
        """Compute the MD5 hash of a file if not already present in the database.

        Args:
            filepath: Path to the file whose hash should be computed.

        Returns:
            str or None: The hexadecimal MD5 hash string if computed, or None if the
            file is already in the database or if an error occurs during hashing.

        This method first checks if the file path is already present in the database.
        If it exists, the function returns None and does not recompute the hash.
        If not, it attempts to read the file and compute its MD5 hash.
        If any file read errors occur (IOError or OSError), None is returned.
        """
        # Hash the photo file
        try:
            # file_hash = self.hash_file(filepath)
            file_hash = self.dhash_file(filepath)
        except (IOError, OSError):
            return None

        return file_hash
