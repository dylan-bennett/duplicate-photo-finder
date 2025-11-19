import hashlib
import os


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

    def compute_and_store_file_hash(self, filepath):
        """Compute and store the hash of a file if not already in the database.

        Args:
            filepath: Path to the file to hash and store.

        Checks if the file path already exists in the database. If it does,
        the method returns early. Otherwise, it computes the file's MD5 hash
        and stores both the filepath and hash in the database. Silently
        handles file read errors by returning without storing anything.
        """
        # Check if the file path exists in the database. If it does, skip it
        if self.database.check_filepath_exists(filepath):
            return

        # Hash the photo file
        try:
            file_hash = self.hash_file(filepath)
        except (IOError, OSError):
            return

        # Insert the file path and its hash into the database
        self.database.insert_filepath_and_hash(filepath, file_hash)
