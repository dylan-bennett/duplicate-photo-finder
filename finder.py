import hashlib
import os


class DuplicatePhotoFinder:
    def __init__(self, database, directory_to_scan):
        self.directory_to_scan = directory_to_scan
        self.valid_image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
        self.database = database

    def find_photo_filepaths(self):
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

    def compute_file_hash(self, filepath):
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
