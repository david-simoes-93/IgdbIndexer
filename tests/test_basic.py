import os
import shutil

import pytest

from igdb_indexer.game_details import GameDetails
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
