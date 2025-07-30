"""A GUI to keep track of videogames from IGDB.com"""

# Define the __all__ variable
__all__ = ["gui", "game_details", "igdb_interface", "json_interface"]

# Import the submodules
from . import game_details, gui, igdb_interface, json_interface
