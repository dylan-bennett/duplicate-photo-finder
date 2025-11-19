from pathlib import Path
from tkinter import Tk

from database import Database
from finder import DuplicatePhotoFinder
from ui import Interface


def main():
    # Create the folder to store our info, if necessary
    home_folder = Path.home()
    config_folder = ".config"
    root_folder = "duplicate-photo-finder"
    db_name = "photos.db"
    full_path = home_folder / config_folder / root_folder
    full_path.mkdir(exist_ok=True)

    # Open / Create the database
    database = Database(f"{full_path}/{db_name}")
    database.create_db()

    # Instantiate the Finder
    finder = DuplicatePhotoFinder(database=database)

    # Create and run the GUI
    root = Tk()
    root.ui = Interface(root, database, finder)
    root.mainloop()


if __name__ == "__main__":
    main()
