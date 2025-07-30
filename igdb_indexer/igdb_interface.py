"""Interface with IGDB"""

import os
import re
from typing import Any

import requests


def get_auth_token() -> str:
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


def query_igdb(game_id: str, access_token: str) -> dict[str, Any]:
    """queries IGDB.com, returns json struct with game info"""
    game_id = re.sub(r"\D", "", game_id)  # clean IDs from windows
    # query game info
    game_api_url = "https://api.igdb.com/v4/games"
    header = {
        "Client-ID": os.environ["CLIENT_ID"],
        "Authorization": "Bearer " + access_token,
    }
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
        img_file_path = os.path.join("user_data", str(game_id) + ".jpg")
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
