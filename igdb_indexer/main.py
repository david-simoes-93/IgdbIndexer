"""The main file"""

import os

from igdb_indexer.gui import MainWindow
from igdb_indexer.json_interface import get_all_json


def main():
    """loads all JSONs, shows GUI"""
    if not os.path.exists("user_data"):
        os.makedirs("user_data")

    # grab all JSON files
    list_of_jsons = get_all_json()

    # create TK window
    window = MainWindow(list_of_jsons)
    window.mainloop()


if __name__ == "__main__":
    main()
