import hashlib
import json
import os


class PhotoDuplicateFinder:
    def __init__(self):
        self.directory_to_scan = None
        self.cache_filename = "_duplicate_photos_info"
        self.cache_file = None

        self.cache_data = {
            "files": [],
            "hashes": {},
        }
        self.valid_image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}

    def read_cache_file(self):
        print("Loading existing hash data...")
        try:
            with open(self.cache_file, "r") as f:
                self.cache_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load cache file: {e}")
            raise

    def write_cache_file(self):
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache_data, f, indent=2)
            print("Hash data saved to cache file")
        except IOError as e:
            print(f"Warning: Could not save cache file: {e}")

    def extract_file_hashes(self):
        # Convert to set for O(1) lookup performance
        cached_files = set(self.cache_data["files"])
        # First pass: count total files for progress tracking
        total_files = 0
        for root, _, files in os.walk(self.directory_to_scan):
            for filename in files:
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in self.valid_image_extensions:
                    total_files += 1
        processed_files = 0
        print(f"Processing {total_files} image files...")
        # Recursively walk through directory and subdirectories
        for root, _, files in os.walk(self.directory_to_scan):
            for filename in files:
                # Check if file has a supported image extension
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext not in self.valid_image_extensions:
                    continue

                # Get the full file path
                file_path = os.path.join(root, filename)

                # Skip if we've already processed this file
                if file_path in cached_files:
                    continue

                # Add to photo files list
                self.cache_data["files"].append(file_path)
                cached_files.add(file_path)  # Update the set for future lookups

                # Show progress
                processed_files += 1
                if processed_files % 10 == 0 or processed_files == total_files:
                    progress_pct = processed_files / total_files * 100
                    print(
                        f"Progress: {processed_files}/{total_files} files "
                        f"processed ({progress_pct:.1f}%)"
                    )

                try:
                    # Compute MD5 hash using chunked reading for memory efficiency
                    hash_md5 = hashlib.md5()
                    with open(file_path, "rb") as f:
                        # Read file in chunks to avoid loading large files
                        # entirely into memory
                        for chunk in iter(lambda: f.read(8192), b""):
                            hash_md5.update(chunk)
                    file_hash = hash_md5.hexdigest()

                    # Initialize hash entry if it doesn't exist
                    if file_hash not in self.cache_data["hashes"]:
                        self.cache_data["hashes"][file_hash] = []

                    # Add file path to hash entry (avoid duplicates)
                    if file_path not in self.cache_data["hashes"][file_hash]:
                        self.cache_data["hashes"][file_hash].append(file_path)

                except (IOError, OSError) as e:
                    print(f"Warning: Could not read file {file_path}: {e}")
                    continue

    def delete_all_but_first_photo(self, file_hash):
        """
        Deletes all but the first file in the hash entry and updates the cache.

        Args:
            file_hash (str): The hash key for the duplicate files to process
        """
        if file_hash not in self.cache_data["hashes"]:
            print(f"Hash {file_hash} not found in cache data")
            return

        photo_files = self.cache_data["hashes"][file_hash]

        if len(photo_files) <= 1:
            print("No duplicates to delete (only one file or less)")
            return

        # Keep the first file, delete the rest
        files_to_delete = photo_files[1:]  # All files except the first one
        first_file = photo_files[0]  # Keep this one

        print(
            f"Deleting {len(files_to_delete)} duplicate files, "
            f"keeping: {os.path.basename(first_file)}"
        )

        # Delete files from filesystem and remove from cache
        for file_path in files_to_delete:
            try:
                # Use try/except instead of os.path.exists check for better performance
                os.remove(file_path)
                print(f"Deleted: {os.path.basename(file_path)}")

                # Remove from files list
                if file_path in self.cache_data["files"]:
                    self.cache_data["files"].remove(file_path)

            except FileNotFoundError:
                print(f"Warning: File does not exist: {file_path}")
            except OSError as e:
                print(f"Error deleting {file_path}: {e}")

        # Update the hash entry to only contain the first file
        self.cache_data["hashes"][file_hash] = [first_file]

        # Write the updated cache to file
        self.write_cache_file()

        print(
            f"Successfully processed {len(files_to_delete)} "
            f"duplicates for hash {file_hash}"
        )

    def calculate_num_duplicates(self):
        """
        Calculate the number of groups of duplicate files.

        Returns:
            int: The number of hash entries in the cache that have more than one file,
                 indicating groups of duplicate photos.
        """
        # Use generator expression for memory efficiency with large datasets
        return sum(1 for entry in self.cache_data["hashes"].values() if len(entry) > 1)

    def get_duplicate_entries(self):
        """
        Retrieve all groups of duplicate files.

        Returns:
            list of tuples: Each tuple contains a hash key and a list of file paths
            that share that hash (i.e., are duplicates). Only groups with more than
            one file are included.
        """
        return [
            (hash_key, files)
            for hash_key, files in self.cache_data["hashes"].items()
            if len(files) > 1
        ]

    def delete_file_from_cache(self, deleted_file_path):
        """Update the cache data after a file is deleted."""
        # Remove from files list
        if deleted_file_path in self.cache_data["files"]:
            self.cache_data["files"].remove(deleted_file_path)

        # Remove from hashes entries
        for file_hash, files in self.cache_data["hashes"].items():
            if deleted_file_path in files:
                files.remove(deleted_file_path)
                # If no files left for this hash, remove the hash entry
                if not files:
                    del self.cache_data["hashes"][file_hash]
                break

        # Write updated cache to file
        self.write_cache_file()