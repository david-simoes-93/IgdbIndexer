"""Specific game-related data"""

import math
import os
from typing import Optional

from PIL import Image, ImageTk


class GameInfo:
    """A small struct to keep track of each game's data"""

    def __init__(self, game_id: str, name: str, order_name: str, year: str):
        self.game_id: str = game_id
        self.name: str = name
        self.order_name: str = order_name
        self.year: str = year
        self.img: Optional[ImageTk.PhotoImage] = None

    def get_img(self, width, _height):
        """generates TK image and returns it"""
        if self.img is None:
            img_name = os.path.join("user_data", self.game_id + ".jpg")
            if os.path.exists(img_name):
                img = Image.open(img_name)
            else:
                img = Image.open(os.path.join("igdb_indexer", "default.jpg"))
            # ratio_x, ratio_y = , (h - 55) / img.height
            ratio = width / img.width  # ratio_x if ratio_x < ratio_y else ratio_y
            self.img = ImageTk.PhotoImage(
                img.resize(
                    (math.floor(img.width * ratio), math.floor(img.height * ratio)),
                    Image.Resampling.LANCZOS,
                )
            )
        return self.img

    def __lt__(self, other):
        """order GameInfo by order_name"""
        return self.order_name < other.order_name
