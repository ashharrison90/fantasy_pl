"""
Functions to manage CRUD operations on fantasy.premierleague.com.
"""
import urllib.parse
import requests
import constants

# Create a session - this persists cookies across requests
MY_SESSION = requests.Session()

def get_squad():
    """
    Get the current selected squad from the fantasy football web app.
    Note: must be logged in first!
    """
    squad_request_headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    squad = MY_SESSION.get(constants.SQUAD_URL, headers=squad_request_headers).json()['picks']
    return squad

def get_transfers_squad():
    """
    Get the current selected squad from the transfers page.
    This gives more information about transfers, such as selling price.
    Note: must be logged in first!
    """
    squad_request_headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    squad = MY_SESSION.get(constants.TRANSFER_URL, headers=squad_request_headers).json()
    return squad

def grab_all():
    """
    Grab all the json data from the fantasy api url.
    """
    return requests.get(constants.FANTASY_API_URL).json()

def grab_player_by_id(player_id):
    """
    Grab a single player's json object from the data using their id.
    """
    player_array = grab_all()["elements"]
    for player in player_array:
        if player["id"] == player_id:
            return player

def grab_player_by_name(first_name, second_name):
    """
    Grab a single player's json object from the data using their name.
    """
    player_array = grab_all()["elements"]
    for player in player_array:
        if (player["first_name"] == first_name) and (player["second_name"] == second_name):
            return player

def grab_player_fixtures(player_id):
    """
    Grab a single player's full history and fixture list using their id.
    """
    return requests.get(constants.FANTASY_PLAYER_API_URL + str(player_id)).json()

def login(username, password):
    """
    Login to the fantasy football web app.
    """
    # Make a GET request to users.premierleague.com to get the correct cookies
    MY_SESSION.get(constants.LOGIN_URL)
    csrf_token = MY_SESSION.cookies.get('csrftoken', domain='users.premierleague.com')

    # POST to the users url with the login credentials and csrfcookie
    login_data = urllib.parse.urlencode({
        'csrfmiddlewaretoken': csrf_token,
        'login': username,
        'password': password,
        'app': 'plusers',
        'redirect_uri': 'https://users.premierleague.com/'
    })
    login_headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    MY_SESSION.post(constants.LOGIN_URL, headers=login_headers, data=login_data)

    # Make a GET request to fantasy.premierleague.com to get the correct cookies
    MY_SESSION.get(constants.FANTASY_URL)
