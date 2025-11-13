import sqlite3
from pathlib import Path
from tkinter import Tk

from ui import Interface


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

    # Create the GUI
    root = Tk()
    root.ui = Interface(root, con)
    root.mainloop()


if __name__ == "__main__":
    main()
