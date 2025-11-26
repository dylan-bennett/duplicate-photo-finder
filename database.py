import math
import sqlite3


class Database:
    def __init__(self, db_path):
        """Initialize the Database connection.

        Args:
            db_path: Path to the SQLite database file. If the file doesn't
                exist, it will be created when the connection is established.

        Creates a connection to the SQLite database and initializes a cursor
        for executing SQL queries.
        """
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        # Pagination
        self.page_number = 1
        self.num_pages = 1
        self.hashes_per_page = 10

    def create_db(self):
        """Create the photos table if it doesn't already exist.

        Creates a table named 'photos' with three columns:
        - filepath: TEXT PRIMARY KEY (unique file path)
        - hash: TEXT NOT NULL (MD5 hash of the file)
        - lastseen: DATETIME (datetime of when a file was last indexed)

        This method is safe to call multiple times as it uses
        CREATE TABLE IF NOT EXISTS.
        """
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photos (
                filepath TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                lastseen DATETIME
            );
            """
        )

    def update_num_pages(self):
        # Grab the duplicate photos, grouped by hash
        self.cursor.execute(
            """SELECT hash, GROUP_CONCAT(filepath)
            FROM photos
            GROUP BY hash
            HAVING COUNT(*) > 1
            ORDER BY hash
            """,
        )

        # Get all the rows
        rows = self.cursor.fetchall()

        # Calculate the number of pages for pagination
        self.num_pages = math.ceil(len(rows) / self.hashes_per_page)

    def get_duplicate_photos(self):
        """Retrieve all duplicate photos grouped by their hash.

        Returns:
            List of tuples, where each tuple contains:
            - hash: The MD5 hash that appears multiple times
            - filepaths: Comma-separated string of file paths with that hash

        Only returns hashes that appear more than once in the database,
        effectively identifying duplicate photos.
        """
        # Grab the duplicate photos, grouped by hash
        self.cursor.execute(
            """SELECT hash, GROUP_CONCAT(filepath)
            FROM photos
            GROUP BY hash
            HAVING COUNT(*) > 1
            ORDER BY hash
            LIMIT ?
            OFFSET ?
            """,
            (self.hashes_per_page, (self.page_number - 1) * self.hashes_per_page),
        )

        # Get all the rows
        return self.cursor.fetchall()

    def check_photo_exists(self, filepath):
        """Check if a file path already exists in the database.

        Args:
            filepath: The file path to check for existence.

        Returns:
            bool: True if the filepath exists in the database, False otherwise.
        """
        self.cursor.execute(
            "SELECT filepath FROM photos WHERE filepath = ?;", (filepath,)
        )
        return self.cursor.fetchone() is not None

    def insert_new_photo(self, filepath, file_hash, timestamp):
        """Insert a file path and its hash into the database.

        Args:
            filepath: The file path to store.
            file_hash: The MD5 hash of the file to store.
            timestamp: The datetime object for a timestamp.

        Commits the transaction after inserting the record. If the filepath
        already exists (as a PRIMARY KEY), this will raise an IntegrityError.
        """
        try:
            self.cursor.execute(
                "INSERT INTO photos VALUES (?, ?, ?);", (filepath, file_hash, timestamp)
            )
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Could not insert {filepath} into database: {e}")
            raise

    def update_lastseen(self, filepath, timestamp):
        """
        Update the 'lastseen' timestamp for a given photo.

        Args:
            filepath (str): The file path of the photo to update.
            timestamp (datetime): The new timestamp to set for 'lastseen'.

        Raises:
            sqlite3.IntegrityError: If the update operation fails.
        """
        try:
            self.cursor.execute(
                "UPDATE photos SET lastseen = ? WHERE filepath = ?;",
                (timestamp, filepath),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Could not update lastseen entry: {e}")
            raise

    def delete_photos(self, filepaths):
        """
        Delete photos from the database for a list of file paths.

        Args:
            filepaths (list[str]): List of file paths to delete from the database.

        Raises:
            sqlite3.IntegrityError: If the deletion operation fails.
        """
        if not filepaths:
            return

        try:
            placeholders = ",".join("?" * len(filepaths))
            self.cursor.execute(
                f"DELETE FROM photos WHERE filepath IN ({placeholders});", filepaths
            )
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error deleting entries from database: {e}")
            raise

    def delete_stale_photos(self, timestamp):
        """
        Remove photo records from the database where the 'lastseen'
        timestamp is older than the provided value.

        Args:
            timestamp (datetime): Reference datetime. Any records with a 'lastseen'
                value less than this timestamp will be deleted.

        Raises:
            sqlite3.IntegrityError: If the deletion operation fails.
        """
        try:
            self.cursor.execute("DELETE FROM photos WHERE lastseen < ?;", (timestamp,))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error deleting stale entries from database: {e}")
            raise
