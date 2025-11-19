import hashlib
import os


class DuplicatePhotoFinder:
    def __init__(self, database):
        self.directory_to_scan = (
            "/home/dylan/Documents/Development/duplicate-photo-finder/test/"
        )
        self.valid_image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
        self.database_connection = database
        self.database_cursor = self.database_connection.cursor()

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
        # print(f"Analyzing photo {i}/{num_photos}...")

        # Check if the file path exists in the database. If it does, skip it
        self.database_cursor.execute(
            f"SELECT filepath FROM photos WHERE filepath = '{filepath}';"
        )
        if self.database_cursor.fetchone() is not None:
            return

        # Hash the photo file
        try:
            file_hash = self.hash_file(filepath)
        except (IOError, OSError):
            return

        # Insert the file path and its hash into the database
        self.database_cursor.execute(
            f"INSERT INTO photos VALUES ('{filepath}', '{file_hash}');"
        )
        self.database_connection.commit()

    def compute_file_hashes(self):
        print("Finding photo files...")

        # Get all the filepaths of the photos
        filepaths = self.find_photo_filepaths()
        num_photos = len(filepaths)

        print(f"Found {num_photos} photo file(s)!")

        # Create a cursor to navigate through the database

        # Run through each photo file
        for i, filepath in enumerate(filepaths, 1):
            self.compute_file_hash(filepath)
