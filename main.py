from pathlib import Path
from tkinter import Tk

from database import Database
from finder import Finder
from ui import Interface


class DuplicatePhotoFinder:
    def __init__(self):
        # Create the folder to store our info, if necessary
        home_folder = Path.home()
        config_folder = ".config"
        root_folder = "duplicate-photo-finder"
        full_path = home_folder / config_folder / root_folder
        full_path.mkdir(exist_ok=True)

        db_name = "photos.db"
        self.db_path = f"{full_path}/{db_name}"

        self.directory_to_scan = (
            "/home/dylan/Documents/Development/duplicate-photo-finder/test/"
        )

        self.database = None
        self.finder = None
        self.interface = None

    def init_database(self):
        # Open / Create the database
        self.database = Database(self.db_path)
        self.database.create_db()

    def init_finder(self):
        # Instantiate the Finder
        self.finder = Finder(
            database=self.database, directory_to_scan=self.directory_to_scan
        )

    def init_interface(self):
        # Create and run the GUI
        self.interface = Tk()
        self.interface.ui = Interface(self.interface, self.database, self.finder)

    def run(self):
        self.init_database()
        self.init_finder()
        self.init_interface()
        self.interface.mainloop()


if __name__ == "__main__":
    dpf = DuplicatePhotoFinder()
    dpf.run()
