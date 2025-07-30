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


def save_json(json_file_name: str, games_json: Dict[str, List[GameDetails]]) -> None:
    """save JSON file"""
    json_path = os.path.join("user_data", json_file_name)
    with open(json_path, "w") as outfile:
        json.dump(games_json, outfile, indent=4)


def load_json_as_games_list(json_file_name: str) -> List[GameDetails]:
    """loads JSON file, returns sorted List of GameDetails"""
    games_json = load_json(json_file_name)
    games_list: List[GameDetails] = []
    for game in games_json["games"]:
        games_list.append(GameDetails(game["id"], game["name"], game["order_name"], int(game["year"])))
    games_list.sort()
    return games_list
