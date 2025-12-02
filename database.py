"""Database management for storing and querying photo metadata.

This module provides the Database class for managing SQLite database operations
including storing photo file paths, hashes, and timestamps, as well as querying
for duplicate photos with pagination support.
"""

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
        try:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS photos (
                    filepath TEXT PRIMARY KEY,
                    hash TEXT NOT NULL,
                    lastseen DATETIME
                );
                """
            )
        except sqlite3.IntegrityError as e:
            print(f"Error creating database: {e}")
            raise

    def update_num_pages(self, directories_to_scan):
        """Update pagination information based on current duplicate groups.

        Args:
            directories_to_scan: List of directory paths to filter duplicates by.
                Only photos whose filepaths start with one of these directories
                will be considered.

        Queries the database for all duplicate photo groups (hashes that appear
        more than once), calculates the total number of pages based on
        hashes_per_page, and updates the page_number to ensure it doesn't exceed
        the total number of pages.
        """
        try:
            # Grab the duplicate photos, grouped by hash
            self.cursor.execute(
                """SELECT hash, GROUP_CONCAT(filepath)
                FROM photos
                WHERE """
                + " OR ".join(["filepath LIKE ?"] * len(directories_to_scan))
                + """
                GROUP BY hash
                HAVING COUNT(*) > 1
                ORDER BY hash
                """,
                tuple(str(directory) + "%" for directory in directories_to_scan),
            )

            # Get all the rows
            rows = self.cursor.fetchall()

            # Calculate the number of pages for pagination
            self.num_pages = math.ceil(len(rows) / self.hashes_per_page)
            self.page_number = min(1, self.num_pages)
        except sqlite3.IntegrityError as e:
            print(f"Error updating number of pages: {e}")
            raise

    def query_database(self, directories_to_scan):
        """Retrieve all duplicate photos grouped by their hash.

        Args:
            directories_to_scan: List of directory paths to filter duplicates by.
                Only photos whose filepaths start with one of these directories
                will be considered.

        Returns:
            List of tuples, where each tuple contains:
            - hash: The MD5 hash that appears multiple times
            - filepaths: Comma-separated string of file paths with that hash

        Only returns hashes that appear more than once in the database,
        effectively identifying duplicate photos. Results are paginated based
        on the current page_number and hashes_per_page settings.
        """
        try:
            # Grab the duplicate photos, grouped by hash
            self.cursor.execute(
                """SELECT hash, GROUP_CONCAT(filepath)
                FROM photos
                WHERE """
                + " OR ".join(["filepath LIKE ?"] * len(directories_to_scan))
                + """
                GROUP BY hash
                HAVING COUNT(*) > 1
                ORDER BY hash
                LIMIT ?
                OFFSET ?
                """,
                (
                    *(str(directory) + "%" for directory in directories_to_scan),
                    self.hashes_per_page,
                    (self.page_number - 1) * self.hashes_per_page,
                ),
            )

            # Get all the rows
            return self.cursor.fetchall()
        except sqlite3.IntegrityError as e:
            print(f"Error querying database: {e}")
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
                f"DELETE FROM photos WHERE filepath IN ({placeholders});",
                list(filepaths),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error deleting entries from database: {e}")
            raise

    def delete_stale_photos(self, directories_to_scan, timestamp):
        """
        Delete photo records from the database for the given directories whose
        'lastseen' timestamp is older than the provided value.

        Args:
            directories_to_scan: List of directory paths as strings or Path objects.
                Only photos whose filepaths start with one of these directories
                will be considered.
            timestamp (datetime): Any records with a 'lastseen' earlier than this
                datetime will be deleted from the database.

        Raises:
            sqlite3.IntegrityError: If the deletion operation fails.
        """
        placeholders = tuple(
            item
            for directory in directories_to_scan
            for item in (str(directory) + "%", timestamp)
        )
        filepaths_lastseen_condition = " OR ".join(
            ["(filepath LIKE ? AND lastseen < ?)"] * len(directories_to_scan)
        )
        try:
            self.cursor.execute(
                "DELETE FROM photos WHERE " + filepaths_lastseen_condition + ";",
                placeholders,
            )
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error deleting stale entries from database: {e}")
            raise

    def get_existing_filepaths(self, filepaths):
        """
        Get a set of filepaths that already exist in the database.

        Args:
            filepaths: List of file paths to check.

        Returns:
            set: Set of filepaths that exist in the database.
        """
        if not filepaths:
            return set()

        placeholders = ",".join("?" * len(filepaths))
        try:
            self.cursor.execute(
                f"SELECT filepath FROM photos WHERE filepath IN ({placeholders});",
                list(filepaths),
            )
            return {row[0] for row in self.cursor.fetchall()}
        except sqlite3.IntegrityError as e:
            print(f"Error getting existing rows from database: {e}")
            raise

    def batch_update_lastseen(self, filepaths, timestamp):
        """
        Batch update the 'lastseen' timestamp for multiple photos.

        Args:
            filepaths: List of file paths to update.
            timestamp: The new timestamp to set for 'lastseen'.
        """
        if not filepaths:
            return

        placeholders = ",".join("?" * len(filepaths))
        try:
            self.cursor.execute(
                f"UPDATE photos SET lastseen = ? WHERE filepath IN ({placeholders});",
                [timestamp] + list(filepaths),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error updating lastseen in database: {e}")
            raise

    def batch_insert_new_photos(self, photo_data):
        """
        Batch insert multiple new photos into the database.

        Args:
            photo_data: List of tuples, each containing (filepath, hash, timestamp).
        """
        if not photo_data:
            return

        try:
            self.cursor.executemany(
                "INSERT INTO photos VALUES (?, ?, ?);",
                photo_data,
            )
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error inserting new entries into database: {e}")
            raise
