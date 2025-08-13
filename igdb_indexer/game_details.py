"""Specific game-related data"""

import math
import os
from typing import Any, Dict

from PIL import Image, ImageEnhance, ImageTk
from pydantic import BaseModel


class GameDetails(BaseModel):
    """A small struct to keep track of each game's data"""

    game_id: str
    name: str
    order_name: str
    year: int
    img: ImageTk.PhotoImage = None
    img_hidden: ImageTk.PhotoImage = None

    # needed due to img and img_hidden, to appease Pydantic
    class Config:
        arbitrary_types_allowed = True

    def generate_cover_image(self, width: int, _height: int, dir: str = "user_data") -> ImageTk.PhotoImage:
        """generates TK image if it wasn't generated yet"""
        if self.img is None:
            img_name: str = os.path.join(dir, self.game_id + ".jpg")
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

            dark_img = ImageEnhance.Brightness(img).enhance(0.1)
            self.img_hidden = ImageTk.PhotoImage(
                dark_img.resize(
                    (math.floor(dark_img.width * ratio), math.floor(dark_img.height * ratio)),
                    Image.Resampling.LANCZOS,
                )
            )
        return self.img

    def __lt__(self, other) -> bool:
        """order GameDetails by order_name"""
        return self.order_name < other.order_name

    def to_json(self) -> Dict[str, Any]:
        return {"game_id": self.game_id, "name": self.name, "order_name": self.order_name, "year": self.year}
