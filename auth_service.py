"""
Connect and manage authorisation to fantasy.premierleague.com.
"""
import urllib.parse
import requests
from constants import LOGIN_URL, FANTASY_URL, SQUAD_URL, TRANSFER_URL

# Create a session - this persists cookies across requests
MY_SESSION = requests.Session()

def login(username, password):
    """
    Login to the fantasy football web app.
    """
    # Make a GET request to users.premierleague.com to get the correct cookies
    MY_SESSION.get(LOGIN_URL)
    CSRF_TOKEN = MY_SESSION.cookies.get('csrftoken', domain='users.premierleague.com')

    # POST to the users url with the login credentials and csrfcookie
    LOGIN_DATA = urllib.parse.urlencode({
        'csrfmiddlewaretoken': CSRF_TOKEN,
        'login': username,
        'password': password,
        'app': 'plusers',
        'redirect_uri': 'https://users.premierleague.com/'
    })
    LOGIN_HEADERS = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    MY_SESSION.post(LOGIN_URL, headers=LOGIN_HEADERS, data=LOGIN_DATA)

    # Make a GET request to fantasy.premierleague.com to get the correct cookies
    MY_SESSION.get(FANTASY_URL)

def get_squad():
    """
    Get the current selected squad from the fantasy football web app.
    Note: must be logged in first!
    """
    SQUAD_REQUEST_HEADERS = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    squad = MY_SESSION.get(SQUAD_URL, headers=SQUAD_REQUEST_HEADERS).json()['picks']
    return squad

def get_transfers_squad():
    """
    Get the current selected squad from the transfers page.
    This gives more information about transfers, such as selling price.
    Note: must be logged in first!
    """
    SQUAD_REQUEST_HEADERS = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    squad = MY_SESSION.get(TRANSFER_URL, headers=SQUAD_REQUEST_HEADERS).json()
    return squad
