"""The main file"""

import os
import sys

from igdb_indexer.gui import MainWindow
from igdb_indexer.json_interface import get_all_json


def main():
    """loads all JSONs, shows GUI"""
    if "CLIENT_ID" not in os.environ or "CLIENT_SECRET" not in os.environ:
        print("Error: please export CLIENT_ID and CLIENT_SECRET variables. Check the README for more details.")
        sys.exit(1)

    if not os.path.exists("user_data"):
        os.makedirs("user_data")

    # grab all JSON files
    list_of_jsons = get_all_json()

    # create TK window
    window = MainWindow(list_of_jsons)
    window.mainloop()


if __name__ == "__main__":
    main()
