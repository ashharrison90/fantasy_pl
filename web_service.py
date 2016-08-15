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
    static_data = MY_SESSION.get(constants.FANTASY_API_DYNAMIC_URL).json()
    constants.EVENT_NUMBER = static_data['next-event']
    constants.SQUAD_URL += str(static_data['entry']['id']) + "/"

def make_transfers(old_squad, new_squad):
    """
    Given lists containing the old(/current)_squad and the new_squad, make the necessary transfers.
    """
    # Create our transfers object and players_in/out lists
    new_squad_ids = [player['id'] for player in new_squad]
    old_squad_ids = [player['element'] for player in old_squad]
    players_in = [player for player in new_squad if player['id'] not in old_squad_ids]
    players_out = [player for player in old_squad if player['element'] not in new_squad_ids]
    transfer_object = {
        'confirmed': 'true',
        'entry': constants.SQUAD_ID,
        'event': constants.EVENT_NUMBER,
        'transfers': [],
        'wildcard': 'false'
    }

    # for each player_in/player_out create a transfer
    for i in range(len(players_in)):
        transfer_object['transfers'].append({
            'element_in': players_in[i]['id'],
            'purchase_price': players_in[i]['now_cost'],
            'element_out': players_out[i]['element'],
            'selling_price': players_out[i]['selling_price']
        })

    # if we need to make transfers, then do so and return the response object
    # else return a generic success response (since we didn't need to do anything!)
    if len(transfer_object['transfers']) > 0:
        MY_SESSION.get('https://fantasy.premierleague.com/a/squad/transfers')
        csrf_token = MY_SESSION.cookies.get('csrftoken', domain='fantasy.premierleague.com')

        transfer_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://fantasy.premierleague.com/a/squad/transfers'
        }
        return MY_SESSION.post(constants.TRANSFER_URL, headers=transfer_headers, json=transfer_object)
    else:
        response_success = requests.Response
        response_success.status_code = 200
        return response_success

def set_starting_lineup(starting_lineup):
    # Make a GET request to get the correct cookies
    MY_SESSION.get(constants.SQUAD_URL)
    csrf_token = MY_SESSION.cookies.get('csrftoken', domain='fantasy.premierleague.com')
    starting_lineup_headers = {
        'X-CSRFToken': csrf_token,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://fantasy.premierleague.com/a/team/my'
    }
    return MY_SESSION.post(constants.SQUAD_URL, headers=starting_lineup_headers, json=starting_lineup)
