"""The GUI"""

import os
import tkinter as tk
from tkinter import ttk
from typing import List

from igdb_indexer.game_details import GameDetails
from igdb_indexer.igdb_interface import get_auth_token, query_igdb
from igdb_indexer.json_interface import (
    load_json,
    load_json_as_games_list,
    remove_json,
    save_json,
)


class GamesListPage(tk.Frame):
    """A TK Frame that will group and show the actual game frames in a grid-like fashion"""

    def __init__(self, root: ttk.Frame, tab_name: str, games_list: List[GameDetails], cols: int, game_width_px: int):
        tk.Frame.__init__(self, root)
        self.root: ttk.Frame = root
        self.cols: int = cols
        self.game_widgets: List[GameFrame] = []
        self.tab_name: str = tab_name
        self.game_width_px: int = game_width_px

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
        self.make_game_frames(games_list)

    def make_game_frames(self, games_list: List[GameDetails]) -> None:
        """makes a game frame for each game in games_list, places it in proper grid position"""
        self.game_widgets = []
        for index in range(len(games_list)):
            row = int(index / self.cols)
            col = index % self.cols
            game_frame = GameFrame(self, games_list[index], self.game_width_px)
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

    def remove_game(self, game_id: str) -> None:
        """removes a game given its ID"""

        # load JSON file
        games_json = load_json(self.tab_name + ".json")

        # remove game from list
        prev_size: int = len(games_json["games"])
        games_json["games"] = [game for game in games_json["games"] if game["game_id"] != game_id]
        if len(games_json["games"]) == prev_size:
            print(f"Game {game_id} not found")
            return

        # update JSON file
        save_json(self.tab_name + ".json", games_json)
        print(f"Game {game_id} removed")

        # update tab
        self.update_games_list_tab()

    def update_all_games(self) -> None:
        processing_window = ProcessingWindow(len(self.game_widgets))
        self.update()

        games_json = {"games": []}

        # fetch all games from current tab
        access_token = get_auth_token()
        for index, game_details in enumerate(self.game_widgets):
            game_json = query_igdb(game_details.game_info.game_id, access_token)
            if game_json is None:
                print(f"Game {game_details.game_info.game_id} no longer found")
                continue
            games_json["games"].append(game_json)
            processing_window.update_progress(index)

        # update JSON file
        save_json(self.tab_name + ".json", games_json)

        # update tab
        self.update_games_list_tab()

        processing_window.destroy()

    def update_games_list_tab(self) -> None:
        """re-creates the tab from scratch"""
        for game_frame in self.game_widgets:
            game_frame.destroy()
        self.game_widgets = []
        json_name: str = self.tab_name + ".json"
        self.make_game_frames(load_json_as_games_list(json_name))


class GameFrame(tk.Frame):
    """a single game frame, with title, date, id, and cover image"""

    def __init__(self, tab: GamesListPage, game_info: GameDetails, game_width_px: int):
        tk.Frame.__init__(self, master=tab.frame, borderwidth=1, background="white")
        self.tab = tab
        self.game_info: GameDetails = game_info
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
        self.label_img = tk.Label(
            master=self,
            image=game_info.generate_cover_image(game_width_px, int(game_width_px * 1.9)),
        )
        self.label_pad = tk.Label(master=self, background="white", font="Helvetica 5")
        self.label_title.pack()
        self.label_year.pack()
        self.label_img.pack()
        self.label_pad.pack()

        # Create a context menu
        self.context_menu = tk.Menu(self, tearoff=False)
        self.context_menu.add_command(label="Remove", command=self.remove_game)
        self.context_menu.bind("<Leave>", lambda _event: self.context_menu.unpost())
        self.bind("<Button-3>", self.open_right_click_menu)
        self.label_img.bind("<Button-3>", self.open_right_click_menu)

    def open_right_click_menu(self, event):
        self.context_menu.post(event.x_root - 1, event.y_root - 1)

    def remove_game(self) -> None:
        self.tab.remove_game(self.game_info.game_id)


class GameSearchBar(tk.Frame):
    """A frame with a search bar that will filter/add/remove/update games on the given page"""

    def __init__(self, root: ttk.Frame, games_list_page: GamesListPage):
        tk.Frame.__init__(self, root)
        self.games_list_page = games_list_page

        self.grid_columnconfigure(0, weight=1)
        self.text_box = tk.Entry(self, width=1000)
        filter_button = tk.Button(self, text="Filter", command=self.filter_button_cb)
        add_button = tk.Button(self, text="Add", command=self.add_button_cb)

        self.text_box.bind("<Return>", lambda _event: self.filter_button_cb())

        self.text_box.grid(column=0, row=0)
        filter_button.grid(column=1, row=0)
        add_button.grid(column=2, row=0)

    def filter_button_cb(self) -> None:
        search_filter = self.text_box.get().lower()
        for game_frame in self.games_list_page.game_widgets:
            if search_filter not in game_frame.game_info.name and search_filter not in game_frame.game_info.order_name:
                game_frame.label_img.configure(image=game_frame.game_info.img_hidden)
            else:
                game_frame.label_img.configure(image=game_frame.game_info.img)

    def add_button_cb(self) -> None:
        game_id: str = self.text_box.get()
        if not game_id.isdigit():
            print(f"Invalid game id: {game_id}")
            return

        # load JSON file
        games_json = load_json(self.games_list_page.tab_name + ".json")

        # fetch game from IGDB
        access_token = get_auth_token()
        game_json = query_igdb(game_id, access_token)
        if game_json is None:
            print(f"Game {game_id} not found")
            return
        games_json["games"] = [game for game in games_json["games"] if game["game_id"] != game_id]
        games_json["games"].append(game_json)

        # update JSON file
        save_json(self.games_list_page.tab_name + ".json", games_json)
        print(f"Game {game_id} added")
        self.text_box.delete(0, "end")

        # update tab
        self.games_list_page.update_games_list_tab()


class GamesTab(tk.Frame):
    """The tab with the games, a scroll bar, and a search bar"""

    cols: int = 5

    def __init__(self, file: str, tab_control: ttk.Notebook, game_width_px: int):
        self.game_width_px: int = game_width_px

        self.tab_name: str = file[:-5]  # remove ".json" suffix
        print(f"\t{self.tab_name}")

        super().__init__(tab_control)
        tab_control.add(self, text=self.tab_name)
        self.update()

        games_list: List[GameDetails] = load_json_as_games_list(file)
        self.games_list_page = GamesListPage(self, self.tab_name, games_list, self.cols, self.game_width_px)
        bottom_search_bar = GameSearchBar(self, self.games_list_page)

        bottom_search_bar.pack(side="bottom", fill="x")
        self.games_list_page.pack(side="top", fill="both", expand=True)


class MainWindow(tk.Tk):
    """Creates the main GUI"""

    cols: int = 5

    def __init__(self, list_of_jsons: List[str]):
        super().__init__()
        width, height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{width}x{height}+0+0")
        self.title("Games Indexer")
        self.iconphoto(False, tk.PhotoImage(file=os.path.join("igdb_indexer", "igdb.png")))
        self.update()

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill="both")

        self.games_width_px: int = round((self.winfo_width() - 40) / self.cols)

        print("Loading tabs:")
        self.tabs: List[GamesTab] = []
        processing_window = ProcessingWindow(len(list_of_jsons))
        processing_window.update()
        for index, file in enumerate(list_of_jsons):
            self.make_tab(file)
            processing_window.update_progress(index)
        processing_window.destroy()

        # Create a context menu
        context_menu = tk.Menu(self.tab_control, tearoff=False)
        context_menu.add_command(label="Add new tab", command=self.show_new_tab_window)
        context_menu.add_command(label="Remove current tab", command=self.remove_tab)
        context_menu.add_command(label="Update current tab", command=self.update_tab)
        context_menu.bind("<Leave>", lambda _event: context_menu.unpost())
        self.tab_control.bind("<Button-3>", lambda event: context_menu.post(event.x_root - 1, event.y_root - 1))

    def make_tab(self, file: str) -> None:
        self.tabs.append(GamesTab(file, self.tab_control, self.games_width_px))

    def remove_tab(self) -> None:
        tab_name: str = self.tab_control.tab(self.tab_control.select(), "text")
        self.tab_control.tab(self.tab_control.select(), state="hidden")
        self.tabs = [games_tab for games_tab in self.tabs if games_tab.tab_name != tab_name]
        remove_json(tab_name + ".json")

    def get_tab_names(self) -> List[str]:
        return [games_tab.tab_name for games_tab in self.tabs]

    def update_tab(self) -> None:
        if len(self.get_tab_names()) == 0:
            return
        tab_name: str = self.tab_control.tab(self.tab_control.select(), "text")
        next(games_tab for games_tab in self.tabs if games_tab.tab_name == tab_name).games_list_page.update_all_games()

    def show_new_tab_window(self) -> None:
        NewTabWindow(self)


class NewTabWindow(tk.Toplevel):
    def __init__(self, main_window: MainWindow):
        super().__init__()
        self.main_window = main_window
        self.title("New Tab Name?")
        self.geometry("300x100")

        # Entry widget for text input
        self.entry = tk.Entry(self, width=30)
        self.entry.pack(pady=5)

        # Buttons
        button_frame = tk.Frame(self)

        ok_button = tk.Button(button_frame, text="Add", command=self.on_ok)
        ok_button.pack(side="left", padx=5)

        cancel_button = tk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side="right", padx=5)

        button_frame.pack(pady=10)

    # Function to handle OK button click
    def on_ok(self) -> None:
        self.main_window.make_tab(self.entry.get() + ".json")
        self.destroy()

    # Function to handle Cancel button click
    def on_cancel(self) -> None:
        self.destroy()


class ProcessingWindow(tk.Toplevel):
    def __init__(self, max_progress: int):
        super().__init__()
        self.title("Processing")
        self.geometry("300x100")

        self.max_progress = max_progress

        # Add a label to the processing window
        self.label = ttk.Label(self, text=f"Processing... 0/{self.max_progress}")
        self.label.pack(pady=20)

    def update_progress(self, progress: int):
        self.label.config(text=f"Processing... {progress}/{self.max_progress}")
        self.update()
