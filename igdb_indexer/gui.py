"""The GUI"""

import tkinter as tk
from tkinter import ttk

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

    def __init__(self, root: ttk.Frame, games_list: list[GameDetails], cols: int, game_width_px: int):
        tk.Frame.__init__(self, root)
        self.root: ttk.Frame = root
        self.cols: int = cols
        self.game_widgets: list[GameDetails] = []

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


class GameSearchBar(tk.Frame):
    """A TK Frame that will filter/add/remove games on the given page"""

    def __init__(self, root: ttk.Frame, games_list_page: GamesListPage):
        tk.Frame.__init__(self, root)
        self.games_list_page = games_list_page

        self.grid_columnconfigure(0, weight=1)

        # Create text widget and specify size.
        self.text_box = tk.Entry(self, width=1000)
        filter_button = tk.Button(self, text="Filter", command=self.filter_button_cb)
        add_button = tk.Button(
            self,
            text="Add",
        )
        remove_button = tk.Button(
            self,
            text="Remove",
        )

        self.text_box.grid(column=0, row=0)
        filter_button.grid(column=1, row=0)
        add_button.grid(column=2, row=0)
        remove_button.grid(column=3, row=0)

    def filter_button_cb(self):
        for game_frame in self.games_list_page.game_widgets:
            search_filter = self.text_box.get()
            if search_filter not in game_frame.game_info.name and search_filter not in game_frame.game_info.order_name:
                game_frame.label_img.configure(image=game_frame.game_info.img_hidden)
            else:
                game_frame.label_img.configure(image=game_frame.game_info.img)


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
        tab_control.add(tab, text=file[:-5])
        tab.update()

        games_list_page = GamesListPage(tab, games_list, cols, game_width_px)
        bottom_search_bar = GameSearchBar(tab, games_list_page)

        bottom_search_bar.pack(side="bottom", fill="x")
        games_list_page.pack(side="top", fill="both", expand=True)

    return window
