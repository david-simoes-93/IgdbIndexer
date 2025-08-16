# IgdbIndexer

<img width="1849" height="1173" alt="image" src="https://github.com/user-attachments/assets/c052ed14-870b-49e5-a2a2-a61debf2203d" />

## Launching

Install all dependencies as such:

    sudo apt install libjpeg8-dev zlib1g-dev python3-tk
    pip install -r requirements.txt

Go to [twitch](https://dev.twitch.tv/console/apps) and get your `CLIENT_ID` and `CLIENT_SECRET` keys.

Export them and run as such:

    export CLIENT_ID="...."
    export CLIENT_SECRET="...."

    python3 -m igdb_indexer.main

## Using the GUI

Right click on the top-left corner to add new tabs, or to add/update/remove games on the current tab.

<img width="733" height="181" alt="image" src="https://github.com/user-attachments/assets/210a6bdd-2fbd-492d-a68e-55679b83fe2c" />

Use the ID from IGDB. For example, for [World of Warcraft](https://www.igdb.com/games/world-of-warcraft), you would use ``IGDB ID: 123``.

Filter games using the search bar on the bottom.

<img width="1463" height="588" alt="image" src="https://github.com/user-attachments/assets/9949aa8f-0ef5-400c-b9e4-c616615198b6" />

Enjoy!
