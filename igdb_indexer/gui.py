"""The GUI"""

import tkinter as tk
from tkinter import ttk


class GamesListPage(tk.Frame):
    """A TK Frame that will group and show the actual game frames in a grid-like fashion"""

    def __init__(self, root, games_list, cols, game_width_px):
        tk.Frame.__init__(self, root)
        self.root = root
        self.cols = cols
        self.pack()

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
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw", tags="self.frame")
        self.frame.bind("<Configure>", self._on_frame_configure)
        self.frame.bind("<Enter>", self._bound_to_mousewheel)
        self.frame.bind("<Leave>", self._unbound_to_mousewheel)

        # keep game frames in memory
        self.game_widgets = []
        self.make_game_frames(self.frame, games_list, game_width_px)

    def make_game_frames(self, root, games_list, game_width_px):
        """makes a game frame for each game in games_list, places it in proper grid position"""
        for index in range(len(games_list)):
            row = int(index / self.cols)
            col = index % self.cols
            game_frame = self.make_game_frame(root, games_list[index], game_width_px)
            game_frame.grid(row=row, column=col, sticky="s")
            self.game_widgets.append(game_frame)

    def make_game_frame(self, master_frame, game_info, game_width_px) -> tk.Frame:
        """makes a single game frame"""
        frame = tk.Frame(master=master_frame, borderwidth=1, background="white")
        label_title = tk.Label(
            master=frame,
            text=game_info.name,
            background="white",
            wraplength=game_width_px,
            font="Helvetica 15 bold",
        )
        label_year = tk.Label(
            master=frame,
            text=str(game_info.year) + " - #" + game_info.game_id,
            background="white",
            wraplength=game_width_px,
        )
        label_img = tk.Label(
            master=frame,
            image=game_info.get_img(game_width_px, int(game_width_px * 1.9)),
        )
        label_pad = tk.Label(master=frame, background="white", font="Helvetica 5")
        label_title.pack()
        label_year.pack()
        label_img.pack()
        label_pad.pack()

        return frame

    def _on_frame_configure(self, _):
        """Reset the scroll region to encompass the inner frame"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bound_to_mousewheel(self, event):
        """when frame is focused, bind mousewheel"""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux_up)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux_down)

    def _unbound_to_mousewheel(self, event):
        """when frame is unfocused, unbind mousewheel"""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel_windows(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux_down(self, event):
        self.canvas.yview_scroll(1, "units")

    def _on_mousewheel_linux_up(self, event):
        self.canvas.yview_scroll(-1, "units")


def make_gui(list_of_jsons, list_of_games_lists):
    window = tk.Tk()
    w, h = window.winfo_screenwidth(), window.winfo_screenheight()
    window.geometry("%dx%d+0+0" % (w, h))
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
        GamesListPage(tab, games_list, cols, game_width_px)

    window.mainloop()
