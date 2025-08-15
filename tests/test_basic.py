import os
import shutil

import pytest
import requests

from igdb_indexer.game_details import GameDetails
from igdb_indexer.igdb_interface import get_auth_token, query_igdb
from igdb_indexer.json_interface import (
    get_all_json,
    load_json_as_games_list,
    remove_json,
    save_json,
)


@pytest.fixture
def empty_dir():
    data_dir: str = "test_data"
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
    os.makedirs(data_dir)
    yield None
    shutil.rmtree(data_dir)


@pytest.fixture
def sample_games(empty_dir):
    data_dir: str = "test_data"

    # 100 games
    games = [
        GameDetails(
            game_id=f"{index:04d}", name="name" + str(index), order_name="order_name" + str(index), year=2000 + index
        )
        for index in range(100)
    ]

    # only 90 have cover
    for index in range(90):
        shutil.copyfile(os.path.join("igdb_indexer", "default.jpg"), os.path.join(data_dir, f"{index:04d}.jpg"))
    yield games


@pytest.fixture
def sample_dir(sample_games):
    # make a dir with 2 game lists, each has 55~60 games
    data_dir: str = "test_data"
    save_json("file0.json", {"games": [game.to_json() for game in sample_games[0:60]]}, data_dir=data_dir)
    save_json("file1.json", {"games": [game.to_json() for game in sample_games[45:100]]}, data_dir=data_dir)
    yield None


def test_json_interface(sample_dir):
    data_dir: str = "test_data"

    # finds JSON files
    list_of_json = get_all_json("test_data")
    list_of_json.sort()
    assert len(list_of_json) == 2
    assert list_of_json[0] == "file0.json"
    assert list_of_json[1] == "file1.json"

    # can load JSON files
    games0 = load_json_as_games_list(list_of_json[0], data_dir=data_dir)
    games0.sort(key=lambda game: game.game_id)
    games1 = load_json_as_games_list(list_of_json[1], data_dir=data_dir)
    games_empty = load_json_as_games_list("random_file.json", data_dir=data_dir)
    assert len(games0) == 60
    assert len(games1) == 55
    assert len(games_empty) == 0  # doesn't exist, doesn't crash

    # loaded games are valid
    for index, game in enumerate(games0):
        assert game.game_id == f"{index:04d}"
        assert game.name == "name" + str(index)
        assert game.order_name == "order_name" + str(index)
        assert game.year == 2000 + index

    # can remove JSON
    remove_json(list_of_json[0], data_dir=data_dir)

    # cover images for games 0:45 were removed
    # games 45:60 exist in games1.json, so 15 cover images not removed
    # then there are cover images for 60:90, a total of 45
    list_of_covers = []
    for file in os.listdir(data_dir):
        if not file.endswith(".jpg"):
            continue
        list_of_covers.append(file)
    assert len(list_of_covers) == 45
    for index in range(45, 90):
        assert f"{index:04d}.jpg" in list_of_covers

    # can remove other JSON, no files left in folder
    remove_json(list_of_json[1], data_dir=data_dir)
    assert len(os.listdir(data_dir)) == 0


def test_igdb_access_token(monkeypatch):
    # mock the requests.post response
    post_url: str = None

    class MockPostResponse:
        @staticmethod
        def json():
            return {"access_token": "ccc"}

    def mock_post(url: str):
        nonlocal post_url
        post_url = url
        return MockPostResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    # make the token fetch
    monkeypatch.setenv("CLIENT_ID", "aaa")
    monkeypatch.setenv("CLIENT_SECRET", "bbb")
    response = get_auth_token()

    # check the token was fetched correctly
    assert post_url == "https://id.twitch.tv/oauth2/token?client_id=aaa&client_secret=bbb&grant_type=client_credentials"
    assert response == "ccc"


def test_igdb_query(monkeypatch, empty_dir):
    # mock the requests.post response for the game data
    post_url: str = None
    post_kwargs = None

    class MockPostResponse:
        @staticmethod
        def json():
            return [
                {
                    "name": "the name",
                    "release_dates": [{"y": 0}, {"y": 3020}, {"y": 2025}],
                    "cover": {"url": "//some.url"},
                }
            ]

    def mock_post(url: str, **kwargs):
        nonlocal post_url, post_kwargs
        post_url = url
        post_kwargs = kwargs
        return MockPostResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    # mock the requests.get response for the cover image
    get_url: str = None

    class MockGetResponse:
        content = b"\xff\xff\xff\xff"  # random bytes

    def mock_get(url: str):
        nonlocal get_url
        get_url = url
        return MockGetResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    # make the query
    monkeypatch.setenv("CLIENT_ID", "aaa")
    response = query_igdb("123", "some_access_token", "test_data")

    # check game data correct and cover image created
    assert post_url == "https://api.igdb.com/v4/games"
    assert post_kwargs["data"] == "fields *,release_dates.*,cover.*; where id = 123;"
    assert post_kwargs["headers"] == {
        "Client-ID": "aaa",
        "Authorization": "Bearer some_access_token",
    }
    assert get_url == "https://some.url"
    assert response == {
        "game_id": "123",
        "name": "the name",
        "order_name": "name 2025",
        "year": 2025,
    }
    assert os.path.isfile("test_data/123.jpg")
