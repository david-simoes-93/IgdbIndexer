"""Specific game-related data"""

import math
import os
from typing import Optional

from PIL import Image, ImageTk


class GameDetails:
    """A small struct to keep track of each game's data"""

    def __init__(self, game_id: str, name: str, order_name: str, year: int):
        self.game_id: str = game_id
        self.name: str = name
        self.order_name: str = order_name
        self.year: int = year
        self.img: Optional[ImageTk.PhotoImage] = None
        self.img_hidden: Optional[ImageTk.PhotoImage] = None

    def generate_cover_image(self, width: int, _height: int) -> ImageTk.PhotoImage:
        """generates TK image if it wasn't generated yet"""
        if self.img is None:
            img_name: str = os.path.join("user_data", self.game_id + ".jpg")
            if os.path.exists(img_name):
                img = Image.open(img_name)
            else:
                img = Image.open(os.path.join("igdb_indexer", "default.jpg"))
            ratio: float = width / img.width
            self.img = ImageTk.PhotoImage(
                img.resize(
                    (math.floor(img.width * ratio), math.floor(img.height * ratio)),
                    Image.Resampling.LANCZOS,
                )
            )
        if self.img_hidden is None:
            img = Image.open(os.path.join("igdb_indexer", "default.jpg"))
            ratio_hidden: float = width / img.width
            self.img_hidden = ImageTk.PhotoImage(
                img.resize(
                    (math.floor(img.width * ratio_hidden), math.floor(img.height * ratio_hidden)),
                    Image.Resampling.LANCZOS,
                )
            )
        return self.img

    def __lt__(self, other) -> bool:
        """order GameDetails by order_name"""
        return self.order_name < other.order_name
