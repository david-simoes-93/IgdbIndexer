"""The main file"""

import os

from igdb_indexer.gui import make_gui


def main():
    """loads all JSONs, shows GUI"""
    if not os.path.exists("user_data"):
        os.makedirs("user_data")

    # grab all JSON files
    list_of_jsons = []
    for file in os.listdir("user_data"):
        if not file.endswith(".json"):
            continue
        list_of_jsons.append(file)
    list_of_jsons.sort()

    # create TK window
    window = make_gui(list_of_jsons)
    window.mainloop()


if __name__ == "__main__":
    main()
