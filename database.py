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

    def create_db(self):
        """Create the photos table if it doesn't already exist.

        Creates a table named 'photos' with two columns:
        - filepath: TEXT PRIMARY KEY (unique file path)
        - hash: TEXT NOT NULL (MD5 hash of the file)

        This method is safe to call multiple times as it uses
        CREATE TABLE IF NOT EXISTS.
        """
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photos (
                filepath TEXT PRIMARY KEY,
                hash TEXT NOT NULL
            );
            """
        )

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
            """
        )
        return self.cursor.fetchall()

    def check_filepath_exists(self, filepath):
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

    def insert_filepath_and_hash(self, filepath, file_hash):
        """Insert a file path and its hash into the database.

        Args:
            filepath: The file path to store.
            file_hash: The MD5 hash of the file to store.

        Commits the transaction after inserting the record. If the filepath
        already exists (as a PRIMARY KEY), this will raise an IntegrityError.
        """
        try:
            self.cursor.execute(
                "INSERT INTO photos VALUES (?, ?);", (filepath, file_hash)
            )
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Could not insert {filepath} into database: {e}")
            raise

    def delete_photos(self, filepaths):
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
