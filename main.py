import sqlite3
from pathlib import Path

from DuplicatePhotoFinder import DuplicatePhotoFinder


def main():
    # Create the folder to store our info, if necessary
    home_folder = Path.home()
    config_folder = ".config"
    root_folder = "duplicate-photo-finder"
    full_path = home_folder / config_folder / root_folder
    full_path.mkdir(exist_ok=True)

    # Open / Create the database
    db_name = "photos.db"
    con = sqlite3.connect(f"{full_path}/{db_name}")
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS photos (
            filepath TEXT PRIMARY KEY,
            hash TEXT NOT NULL
        );
    """
    )

    # Hash the photo files and store in the database
    duplicate_photo_finder = DuplicatePhotoFinder(database=con)
    duplicate_photo_finder.compute_file_hashes()


if __name__ == "__main__":
    main()
