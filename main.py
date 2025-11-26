from pathlib import Path

from database import Database
from finder import Finder
from interface import Interface


class DuplicatePhotoFinder:
    def __init__(self):
        """Initialize the DuplicatePhotoFinder application.

        Sets up the configuration directory structure, database path, and
        directory to scan. Initializes component references (database, finder,
        interface) to None, which will be initialized later.
        """
        # Create the folder to store our info, if necessary
        home_folder = Path.home()
        config_folder = ".config"
        root_folder = "duplicate-photo-finder"
        full_path = home_folder / config_folder / root_folder
        full_path.mkdir(exist_ok=True)

        db_name = "photos.db"
        self.db_path = f"{full_path}/{db_name}"

        self.directory_to_scan = "/home/dylan/Pictures"

        self.database = None
        self.finder = None
        self.interface = None

    def init_database(self):
        """Initialize and create the database connection.

        Creates a Database instance using the configured database path and
        creates the necessary database tables if they don't already exist.
        """
        # Open / Create the database
        self.database = Database(self.db_path)
        self.database.create_db()

    def init_finder(self):
        """Initialize the Finder component.

        Creates a Finder instance with the database and directory to scan.
        The Finder is responsible for locating photo files and computing
        their hashes to identify duplicates.
        """
        # Instantiate the Finder
        self.finder = Finder(
            database=self.database, directory_to_scan=self.directory_to_scan
        )

    def init_interface(self):
        """Initialize the graphical user interface.

        Creates an Interface instance with the database and finder components.
        The interface provides the GUI for displaying duplicate photos and
        managing the scanning process.
        """
        # Instantiate the GUI
        self.interface = Interface(self.database, self.finder)

    def run(self):
        """Run the duplicate photo finder application.

        Initializes all components in the correct order (database, finder,
        interface) and starts the GUI main loop.
        """
        self.init_database()
        self.init_finder()
        self.init_interface()


if __name__ == "__main__":
    dpf = DuplicatePhotoFinder()
    dpf.run()
