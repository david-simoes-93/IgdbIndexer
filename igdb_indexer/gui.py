"""The GUI"""

import json
import os
import re
import tkinter as tk
from tkinter import ttk
from typing import Any

import requests

from igdb_indexer.game_details import GameDetails


class GameFrame(tk.Frame):
    def __init__(self, root: ttk.Frame, game_info: GameDetails, game_width_px: int):
        """makes a single game frame"""
        tk.Frame.__init__(self, master=root, borderwidth=1, background="white")
        self.game_info = game_info
        self.label_title = tk.Label(
            master=self,
            text=game_info.name,
            background="white",
            wraplength=game_width_px,
            font="Helvetica 15 bold",
        )
        self.label_year = tk.Label(
            master=self,
            text=str(game_info.year) + " - #" + game_info.game_id,
            background="white",
            wraplength=game_width_px,
        )
        game_info.generate_cover_image(game_width_px, int(game_width_px * 1.9))
        self.label_img = tk.Label(
            master=self,
            image=game_info.img,
        )
        self.label_pad = tk.Label(master=self, background="white", font="Helvetica 5")
        self.label_title.pack()
        self.label_year.pack()
        self.label_img.pack()
        self.label_pad.pack()


class GamesListPage(tk.Frame):
    """A TK Frame that will group and show the actual game frames in a grid-like fashion"""

    def __init__(self, root: ttk.Frame, tab_name: str, games_list: list[GameDetails], cols: int, game_width_px: int):
        tk.Frame.__init__(self, root)
        self.root: ttk.Frame = root
        self.cols: int = cols
        self.game_widgets: list[GameDetails] = []
        self.tab_name = tab_name

        # canvas with a scrollbar and a frame inside it
        self.canvas = tk.Canvas(
            self,
            width=root.winfo_screenwidth(),
            height=root.winfo_screenheight(),
            background="white",
        )
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left")

        # frame inside canvas has the actual game frames
        self.frame = tk.Frame(self.canvas, background="white")
        self.canvas.create_window(0, 0, window=self.frame, anchor="nw", tags="self.frame")
        self.frame.bind("<Configure>", self._on_frame_configure)
        self.frame.bind("<Enter>", self._bound_to_mousewheel)
        self.frame.bind("<Leave>", self._unbound_to_mousewheel)

        # keep game frames in memory
        self.make_game_frames(games_list, game_width_px)

    def make_game_frames(self, games_list: list[GameDetails], game_width_px: int) -> None:
        """makes a game frame for each game in games_list, places it in proper grid position"""
        self.game_widgets = []
        for index in range(len(games_list)):
            row = int(index / self.cols)
            col = index % self.cols
            game_frame = GameFrame(self.frame, games_list[index], game_width_px)
            game_frame.grid(row=row, column=col, sticky="s")
            self.game_widgets.append(game_frame)

    def _on_frame_configure(self, _event) -> None:
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bound_to_mousewheel(self, _event) -> None:
        """when frame is focused, bind mousewheel"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux_up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux_down)

    def _unbound_to_mousewheel(self, _event) -> None:
        """when frame is unfocused, unbind mousewheel"""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel_windows(self, event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux_down(self, _event) -> None:
        self.canvas.yview_scroll(1, "units")

    def _on_mousewheel_linux_up(self, _event) -> None:
        self.canvas.yview_scroll(-1, "units")


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


class GameSearchBar(tk.Frame):
    """A TK Frame that will filter/add/remove games on the given page"""

    def __init__(self, root: ttk.Frame, games_list_page: GamesListPage):
        tk.Frame.__init__(self, root)
        self.games_list_page = games_list_page

        self.grid_columnconfigure(0, weight=1)

        # Create text widget and specify size.
        self.text_box = tk.Entry(self, width=1000)
        filter_button = tk.Button(self, text="Filter", command=self.filter_button_cb)
        add_button = tk.Button(self, text="Add", command=self.add_button_cb)
        remove_button = tk.Button(self, text="Remove", command=self.remove_button_cb)

        self.text_box.grid(column=0, row=0)
        filter_button.grid(column=1, row=0)
        add_button.grid(column=2, row=0)
        remove_button.grid(column=3, row=0)

    def filter_button_cb(self):
        search_filter = self.text_box.get()
        for game_frame in self.games_list_page.game_widgets:
            if search_filter not in game_frame.game_info.name and search_filter not in game_frame.game_info.order_name:
                game_frame.label_img.configure(image=game_frame.game_info.img_hidden)
            else:
                game_frame.label_img.configure(image=game_frame.game_info.img)

    def add_button_cb(self):
        game_id = self.text_box.get()
        if not game_id.isdigit():
            print("Invalid game id")
            return

        # fetch game from IGDB
        access_token = get_auth_token()
        game_json = query_igdb(game_id, access_token)
        if game_json is None:
            print("Game not found")
            return

        # load JSON file
        json_path = os.path.join("user_data", self.games_list_page.tab_name + ".json")
        if os.path.exists(json_path):
            with open(json_path, newline="") as json_file:
                games_json = json.load(json_file)
        else:
            games_json = {"games": []}

        # update JSON file
        games_json["games"] = [game for game in games_json["games"] if game["id"] != game_id]
        games_json["games"].append(game_json)
        with open(json_path, "w") as outfile:
            json.dump(games_json, outfile, indent=4)

        print("Game added")
        # update tab

    def remove_button_cb(self):
        game_id = self.text_box.get()
        if not game_id.isdigit():
            print("Invalid game id")
            return

        # load JSON file
        json_path = os.path.join("user_data", self.games_list_page.tab_name + ".json")
        with open(json_path, newline="") as json_file:
            games_json = json.load(json_file)

        # remove game from list
        games_json["games"] = [game for game in games_json["games"] if game["id"] != game_id]

        # update JSON file
        with open(json_path, "w") as outfile:
            json.dump(games_json, outfile, indent=4)
        print("Game removed")

        # update tab


def make_gui(list_of_jsons: list[str], list_of_games_lists: list[GameDetails]) -> tk.Tk:
    """Creates the main GUI"""
    window = tk.Tk()
    width, height = window.winfo_screenwidth(), window.winfo_screenheight()
    window.geometry(f"{width}x{height}+0+0")
    window.title("Games Indexer")
    window.iconphoto(False, tk.PhotoImage(file="igdb_indexer/igdb.png"))
    window.update()

    cols = 5
    game_width_px = (window.winfo_width() - 40) / 5

    tab_control = ttk.Notebook(window)
    tab_control.pack(expand=1, fill="both")

    for file, games_list in zip(list_of_jsons, list_of_games_lists):
        tab = ttk.Frame(tab_control)
        tab_name = file[:-5]
        tab_control.add(tab, text=tab_name)
        tab.update()

        games_list_page = GamesListPage(tab, tab_name, games_list, cols, game_width_px)
        bottom_search_bar = GameSearchBar(tab, games_list_page)

        bottom_search_bar.pack(side="bottom", fill="x")
        games_list_page.pack(side="top", fill="both", expand=True)

    return window
