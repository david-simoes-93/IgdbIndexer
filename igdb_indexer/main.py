"""The main file"""

import argparse
import csv
import json
import os
import re
import sys

import requests

from igdb_indexer.game_details import GameInfo
from igdb_indexer.gui import make_gui


def build_games_list(json_name):
    """loads .json, returns list of GameInfo"""
    games_list = []
    with open(json_name, newline="") as json_file:
        games_json = json.load(json_file)
        for game in games_json["games"]:
            games_list.append(GameInfo(game["id"], game["name"], game["order_name"], game["year"]))
    games_list.sort()
    return games_list


def process_csv(csv_name):
    """loads .csv extracted from IGDB.com, queries IGDB.com for GameInfos, saves .json with same name"""
    games_json = []
    access_token = get_auth_token()

    with open(csv_name + ".csv", newline="") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",", quotechar='"')
        first_line_skipped = False
        for row in csv_reader:
            if not first_line_skipped:
                first_line_skipped = True
                continue
            game_json = call_api(row[0], access_token)
            if game_json is None:
                sys.exit(1)
            games_json.append(game_json)

    with open(csv_name + ".json", "w") as outfile:
        json.dump({"games": games_json}, outfile, indent=4)


def get_auth_token():
    """authenticates on Twitch with OAuth2"""
    auth_url = (
        "https://id.twitch.tv/oauth2/token?client_id="
        + os.environ["CLIENT_ID"]
        + "&client_secret="
        + os.environ["CLIENT_SECRET"]
        + "&grant_type=client_credentials"
    )

    # make post to auth_url, get token
    response_decoded_json = requests.post(auth_url)
    response_json = response_decoded_json.json()
    access_token = response_json["access_token"]
    return access_token


def call_api(game_id, access_token):
    """queries IGDB.com, returns json struct with game info"""
    game_id = re.sub(r"\D", "", game_id)
    # query game info
    game_api_url = "https://api.igdb.com/v4/games"
    header = {"Client-ID": os.environ["CLIENT_ID"], "Authorization": "Bearer " + access_token}
    response_decoded_json = requests.post(
        game_api_url,
        data="fields *,release_dates.*,cover.*; where id = " + str(game_id) + ";",
        headers=header,
    )
    if len(response_decoded_json.json()) == 0:
        print(f"\tGame {game_id} not found in IGDB")
        return None
    response_json = response_decoded_json.json()[0]

    name = response_json["name"]

    # get earliest release year
    year = 0
    if "release_dates" in response_json:
        for release_year in response_json["release_dates"]:
            if "y" not in release_year:  # happens with TBD dates
                continue
            if release_year["y"] < year or year == 0:
                year = release_year["y"]
    if year == 0:
        print("\tEmpty year!")

    # get proper name to order game with
    order_name = name.lower().split(": ")[0].split(" - ")[0].split(", ")[0] + " "
    if order_name.startswith("the "):
        order_name = order_name[4:]
    order_name = re.sub(r"[^a-zA-Z0-9 ]", "", order_name)
    order_name = re.sub(r" [0-9]+ ", "", order_name)
    order_name = order_name.replace("  ", " ")
    order_name = order_name.replace(" i ", "").replace(" ii ", "").replace(" iii ", "")
    order_name = order_name.strip() + " " + str(year)

    # download cover img
    if "cover" in response_json:
        img_url = "https:" + response_json["cover"]["url"].replace("/t_thumb/", "/t_cover_big/")
        img_file_path = "./" + str(game_id) + ".jpg"
        if not os.path.exists(img_file_path):
            img_data = requests.get(img_url).content
            with open(img_file_path, "wb") as handler:
                handler.write(img_data)
    else:
        print("\tNo image found!")

    game_json = {
        "id": game_id,
        "name": name.strip(),
        "order_name": order_name.strip(),
        "year": year,
    }
    print(game_json)
    return game_json


# adds/removes games with args, or shows GUI otherwise
def main():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "--add",
        default="",
        dest="add",
        nargs="+",
        help="""ID of game from IGDB.com to add on given list""",
    )
    parser.add_argument(
        "--csv",
        default="",
        dest="csv",
        help="""IGDB.com CSV file name to process and convert to JSON""",
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
        help="""Whether to re-pull data from IGDB.com""",
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
        game_json = call_api(args.add[0], access_token)
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

    if len(args.csv) != 0:
        process_csv("./" + args.csv)

    if not os.path.exists("user_data"):
        os.makedirs("user_data")

    list_of_jsons = []
    for file in os.listdir("user_data"):
        if not file.endswith(".json"):
            continue
        list_of_jsons.append(file)

    list_of_games_lists = []
    list_of_jsons.sort()
    for file in list_of_jsons:
        print(file)

        games_list = build_games_list(os.path.join("user_data", file))
        if args.update_all:
            access_token = get_auth_token()
            for game in games_list:
                call_api(game.id, access_token)
                # dont save anything, just download photo
        # append to list so images don't get garbage collected
        list_of_games_lists.append(games_list)

    window = make_gui(list_of_jsons, list_of_games_lists)
    window.mainloop()


if __name__ == "__main__":
    main()
