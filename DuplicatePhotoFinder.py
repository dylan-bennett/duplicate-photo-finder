import hashlib
import os

class DuplicatePhotoFinder:
    def __init__(self, database):
        self.directory_to_scan = "/home/dylan/Documents/Development/duplicate-photo-finder/test/test_images/"
        self.valid_image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
        self.database_connection = database
        self.database_cursor = self.database_connection.cursor()

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

    def compute_file_hashes(self):
        # Recursively walk through directory and subdirectories
        for root, _, files in os.walk(self.directory_to_scan):
            for filename in files:
                print(filename)
                # Check if file has a supported image extension
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in self.valid_image_extensions:
                    print("Not a valid image")
                    continue

                # Get the full file path
                filepath = os.path.join(root, filename)
                print(filepath)

                # Check if the file path exists in the database. If it does, skip it
                self.database_cursor.execute(f"SELECT filepath FROM photos WHERE filepath = '{filepath}';")
                if self.database_cursor.fetchone() is not None:
                    print("Already exists in database")
                    continue

                # Hash the photo file
                print("Hashing the photo")
                try:
                    file_hash = self.hash_file(filepath)
                except (IOError, OSError):
                    continue

                # Insert the file path and its hash into the database
                print("Inserting into database")
                self.database_cursor.execute(f"INSERT INTO photos VALUES ('{filepath}', '{file_hash}');")
                self.database_connection.commit()

