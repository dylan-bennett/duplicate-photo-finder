from pathlib import Path
import sqlite3

from DuplicatePhotoFinder import DuplicatePhotoFinder

def main():
    # Create the folder to store our info, if necessary
    print("Creating config folder")
    home_folder = Path.home()
    config_folder = ".config"
    root_folder = "duplicate-photo-finder"
    full_path = home_folder / config_folder / root_folder
    full_path.mkdir(exist_ok=True)

    # Open / Create the database
    print("Creating the database (if necessary)")
    db_name = "photos.db"
    con = sqlite3.connect(f"{full_path}/{db_name}")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            filepath TEXT PRIMARY KEY,
            hash TEXT NOT NULL
        );
    """)

    # Recursively go through folders and find photo files
    print("Initializing DuplicatePhotoFinder")
    duplicate_photo_finder = DuplicatePhotoFinder(database=con)

    print("Hashing files")
    duplicate_photo_finder.compute_file_hashes()

    # Hash the files, store their entry in the database if necessary




    pass

if __name__ == "__main__":
    main()