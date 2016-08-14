"""
Functions used to grab the json data from the fantasy premier league api.
"""
from constants import FANTASY_API_URL, FANTASY_PLAYER_API_URL
import requests

def grab_all():
    """Grab all the json data from the fantasy api url."""
    return requests.get(FANTASY_API_URL).json()

def grab_player_by_id(player_id):
    """Grab a single player's json object from the data using their id."""
    player_array = grab_all()["elements"]
    for player in player_array:
        if player["id"] == player_id:
            return player

def grab_player_by_name(first_name, second_name):
    """Grab a single player's json object from the data using their name."""
    player_array = grab_all()["elements"]
    for player in player_array:
        if (player["first_name"] == first_name) and (player["second_name"] == second_name):
            return player


def grab_player_fixtures(player_id):
    """Grab a single player's full history and fixture list using their id."""
    return requests.get(FANTASY_PLAYER_API_URL + str(player_id)).json()
