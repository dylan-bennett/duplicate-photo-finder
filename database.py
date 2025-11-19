import sqlite3


class Database:
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def create_db(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS photos (
                filepath TEXT PRIMARY KEY,
                hash TEXT NOT NULL
            );
            """
        )

    def get_duplicate_photos(self):
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
        self.cursor.execute(
            f"SELECT filepath FROM photos WHERE filepath = '{filepath}';"
        )
        return self.cursor.fetchone() is not None

    def insert_filepath_and_hash(self, filepath, file_hash):
        self.cursor.execute(f"INSERT INTO photos VALUES ('{filepath}', '{file_hash}');")
        self.connection.commit()
