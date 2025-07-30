"""The main file"""

import argparse
import json
import os
import sys

from igdb_indexer.game_details import GameDetails
from igdb_indexer.gui import make_gui
from igdb_indexer.networking import get_auth_token, query_igdb


def load_list_json(json_name: str) -> list[GameDetails]:
    """loads .json, returns sorted list of GameDetails"""
    games_list: list[GameDetails] = []
    with open(json_name, newline="") as json_file:
        games_json = json.load(json_file)
        for game in games_json["games"]:
            games_list.append(GameDetails(game["id"], game["name"], game["order_name"], game["year"]))
    games_list.sort()
    return games_list


def main():
    """adds/removes games with args, or shows GUI otherwise"""
    parser = argparse.ArgumentParser(description="Add or remove games from IGDB.")
    parser.add_argument(
        "--add",
        default="",
        dest="add",
        nargs="+",
        help="""ID of game from IGDB.com to add on given list""",
    )
    parser.add_argument(
        "--remove",
        default="",
        dest="remove",
        nargs="+",
        help="""ID of game from IGDB.com to remove on given list""",
    )
    parser.add_argument(
        "--update_all",
        default=False,
        action="store_true",
        help="""Whether to re-pull cover data from IGDB.com""",
    )
    args = parser.parse_args()

    if len(args.add) != 0:
        if len(args.add) != 2:
            print("Please specify an ID and a target list to add game to!")
            sys.exit(1)
        if os.path.exists(args.add[1] + ".json"):
            with open(args.add[1] + ".json", newline="") as json_file:
                games_json = json.load(json_file)
        else:
            games_json = {"games": []}
        access_token = get_auth_token()
        game_json = query_igdb(args.add[0], access_token)
        if game_json is None:
            sys.exit(1)
        games_json["games"] = [game for game in games_json["games"] if game["id"] != args.add[0]]
        games_json["games"].append(game_json)
        with open(args.add[1] + ".json", "w") as outfile:
            json.dump(games_json, outfile, indent=4)
        sys.exit(0)

    if len(args.remove) != 0:
        if len(args.remove) != 2:
            print("Please specify an ID and a target list to remove game from!")
            sys.exit(1)
        with open(args.remove[1] + ".json", newline="") as json_file:
            games_json = json.load(json_file)
        games_json["games"] = [game for game in games_json["games"] if game["id"] != args.remove[0]]
        with open(args.remove[1] + ".json", "w") as outfile:
            json.dump(games_json, outfile, indent=4)
        sys.exit(0)

    if not os.path.exists("user_data"):
        os.makedirs("user_data")

    list_of_jsons = []
    for file in os.listdir("user_data"):
        if not file.endswith(".json"):
            continue
        list_of_jsons.append(file)

    list_of_jsons.sort()
    for file in list_of_jsons:
        games_list = load_list_json(os.path.join("user_data", file))
        if args.update_all:
            access_token = get_auth_token()
            for game in games_list:
                query_igdb(game.id, access_token)
                # dont save anything, just download photo

    window = make_gui(list_of_jsons)
    window.mainloop()


if __name__ == "__main__":
    main()
