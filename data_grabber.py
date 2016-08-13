"""Functions used to grab the json data from the fantasy premier league api."""
import requests
FANTASY_API_URL = "https://fantasy.premierleague.com/drf/bootstrap-static"

def grab_all():
    """Grab all the json data from the fantasy api url."""
    return requests.get(FANTASY_API_URL).json()

def grab_player(player_id):
    """Grab a single player's json object from the data using their id."""
    player_array = grab_all()["elements"]
    for player_json in player_array:
        if player_json["id"] == player_id:
            return player_json
