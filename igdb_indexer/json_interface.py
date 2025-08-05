"""Interface with JSON files"""

import json
import os
from typing import Any, Dict, List

from igdb_indexer.game_details import GameDetails


def load_json(json_file_name: str) -> Dict[str, Any]:
    """load JSON file as a dict {games: [Dict[str, str]]}"""
    json_path = os.path.join("user_data", json_file_name)
    if os.path.exists(json_path):
        with open(json_path, newline="") as json_file:
            games_json = json.load(json_file)
    else:
        games_json = {"games": []}
    return games_json


def save_json(json_file_name: str, games_json: Dict[str, Any]) -> None:
    """save JSON file"""
    json_path = os.path.join("user_data", json_file_name)
    with open(json_path, "w") as outfile:
        json.dump(games_json, outfile, indent=4)
    print(f"Saved {json_path}")


def remove_json(json_file_name: str) -> None:
    """remove JSON file and all game covers it uniquely references"""
    other_jsons = get_all_json()
    other_jsons.remove(json_file_name)

    # find all games referenced by other lists
    other_games = set()
    for other_json in other_jsons:
        for game in load_json(other_json)["games"]:
            other_games.add(game["game_id"])

    # remove all game_covers of games in the list-to-be-deleted that aren't referenced elsewhere
    for game in load_json(json_file_name)["games"]:
        if game["game_id"] in other_games:
            continue
        try:
            os.remove(os.path.join("user_data", game["game_id"] + ".jpg"))
        except Exception:
            print(f"Failed to remove cover img for {game['game_id']}")

    # remove list
    json_path = os.path.join("user_data", json_file_name)
    os.remove(json_path)
    print(f"Removed {json_path}")


def get_all_json() -> List[str]:
    """grab all JSON files"""
    list_of_jsons = []
    for file in os.listdir("user_data"):
        if not file.endswith(".json"):
            continue
        list_of_jsons.append(file)
    list_of_jsons.sort()
    return list_of_jsons


def load_json_as_games_list(json_file_name: str) -> List[GameDetails]:
    """loads JSON file, returns sorted List of GameDetails"""
    games_json = load_json(json_file_name)
    games_list: List[GameDetails] = []
    for game in games_json["games"]:
        games_list.append(GameDetails(**game))
    games_list.sort()
    return games_list
