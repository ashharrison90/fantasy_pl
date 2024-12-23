"""
Functions to manage CRUD operations on fantasy.premierleague.com.
"""
import json
import urllib
import requests
import constants
import logging

logger = logging.getLogger()
# Create a session - this persists cookies across requests
MY_SESSION = requests.Session()

def get_deadline_date():
    """
    Get the next deadline for submitting transfers/team choice
    """
    static_data = MY_SESSION.get(constants.FANTASY_API_URL).json()
    events = static_data['events'];
    next_event = next(x for x in events if x["is_next"] == True)
    logger.debug('Next event is {}'.format(next_event))
    result = next_event['deadline_time'].split('T')[0]
    logger.info('Deadline is {}'.format(result))
    return result

def get_team_data():
    team_data = MY_SESSION.get(constants.FANTASY_API_URL).json()['teams']
    return team_data

def get_transfers_squad():
    """
    Get the current selected squad from the transfers page.
    This gives more information about transfers, such as selling price.
    Note: must be logged in first!
    """
    squad_request_headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    result = MY_SESSION.get(constants.SQUAD_URL,
                            headers=squad_request_headers).json()
    logger.debug('Current transfers squad is {}'.format(result))
    return result


def get_all_player_data():
    """
    Grab all the json data from the fantasy api url.
    """
    result = MY_SESSION.get(constants.FANTASY_API_URL).json()
    logger.debug('Got player data: {}'.format(json.dumps(result)[:100], '...'))
    return result


def get_player_fixtures(player_id):
    """
    Grab a single player's full history and fixture list using their id.
    """
    result = MY_SESSION.get(
        constants.FANTASY_PLAYER_API_URL + str(player_id) + '/').json()
    logger.debug('Got fixtures for player with id {}: {}...'.format(player_id, json.dumps(result)[:100]))
    return result


def login(username, password):
    """
    Login to the fantasy football web app.
    """
    logger.info('Logging in to {} with username {}'.format(constants.LOGIN_URL, username))

    # Make a GET request to users.premierleague.com to get the correct cookies
    MY_SESSION.get(constants.LOGIN_URL)
    csrf_token = MY_SESSION.cookies.get(
        'csrftoken', domain='users.premierleague.com')

    # POST to the users url with the login credentials and csrfcookie
    login_data = urllib.parse.urlencode({
        'csrfmiddlewaretoken': csrf_token,
        'login': username,
        'password': password,
        'app': 'plusers',
        'redirect_uri': 'https://users.premierleague.com/'
    })

    login_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        # Without this, FPL will reject the automated login :|
        # See https://github.com/sertalpbilal/FPL-Optimization-Tools/commit/93b633d59fe7176b171a2b133daa01aa85541c87
        "user-agent": "Dalvik/2.1.0 (Linux; U; Android 6.0; Android SDK built for x86_64 Build/MASTER)",
    }

    result = MY_SESSION.post(
        constants.LOGIN_URL, headers=login_headers, data=login_data)
    if result.status_code != 200:
        logger.error('Error logging in!', result)

    # Make a GET request to fantasy.premierleague.com to get the correct
    # cookies
    MY_SESSION.get(constants.FANTASY_URL)
    dynamic_data = MY_SESSION.get(constants.FANTASY_API_DYNAMIC_URL).json()
    static_data = MY_SESSION.get(constants.FANTASY_API_URL).json()
    constants.NEXT_EVENT = next(event for event in static_data['events'] if event['finished']==False)
    constants.SQUAD_ID = dynamic_data['player']['entry']
    constants.SQUAD_URL += str(constants.SQUAD_ID) + '/'
    constants.TRANSFER_DEADLINE = constants.NEXT_EVENT['deadline_time']


def create_transfers_object(old_squad, new_squad, use_wildcard=False):
    """
    Given lists containing the old(/current)_squad and the new_squad,
    calculate the new transfers object.
    """
    # Create our transfers object and players_in/out lists
    new_squad_ids = [player['id'] for player in new_squad]
    old_squad_ids = [player['element'] for player in old_squad]
    players_in = [player for player in new_squad if player[
        'id'] not in old_squad_ids]
    players_out = [player for player in old_squad if player[
        'element'] not in new_squad_ids]
    transfer_object = {
        'entry': constants.SQUAD_ID,
        'event': constants.NEXT_EVENT['id'],
        'transfers': [],
        'chip': 'wildcard' if use_wildcard else None
    }

    # We sort the players_in and players_out list by player_type
    # as each transfer must be of the same type
    players_out = sorted(
        players_out, key=lambda player: (constants.PLAYERS[player['element']]['element_type']))
    players_in = sorted(
        players_in, key=lambda player: (player['element_type']))

    # for each player_in/player_out create a transfer
    for i in range(len(players_in)):
        transfer_object['transfers'].append({
            'element_in': players_in[i]['id'],
            'purchase_price': players_in[i]['now_cost'],
            'element_out': players_out[i]['element'],
            'selling_price': players_out[i]['selling_price']
        })
    logger.debug('Created transfer object: {}'.format(transfer_object))
    return transfer_object


def make_transfers(transfer_object):
    """
    Given a transfers object, make the corresponding transfers in the webapp.
    """
    # if we need to make transfers, then do so and return the response object
    # else return a generic success response (since we didn't need to do
    # anything!)
    if len(transfer_object['transfers']) > 0:
        MY_SESSION.get('https://fantasy.premierleague.com/transfers')
        csrf_token = MY_SESSION.cookies.get(
            'csrftoken', domain='fantasy.premierleague.com')

        transfer_headers = {
            'X-CSRFToken': csrf_token,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://fantasy.premierleague.com/transfers'
        }

        result = MY_SESSION.post(
            constants.TRANSFER_URL,
            headers=transfer_headers,
            json=transfer_object
        )

        if result.status_code != 200:
            logger.error('Error making transfers: {}'.format(result.json()))
    else:
        response_success = requests.Response
        response_success.status_code = 200
        result = response_success
    logger.debug('Made transfers successfully: {}'.format(result))
    return result


def set_starting_lineup(starting_lineup):
    """
    Set the starting lineup correctly in the webapp.
    """
    # Make a GET request to get the correct cookies
    MY_SESSION.get(constants.SQUAD_URL)
    csrf_token = MY_SESSION.cookies.get(
        'csrftoken', domain='fantasy.premierleague.com')

    starting_lineup_headers = {
        'X-CSRFToken': csrf_token,
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://fantasy.premierleague.com/my-team'
    }

    result = MY_SESSION.post(
        constants.SQUAD_URL,
        headers=starting_lineup_headers,
        json=starting_lineup
    )

    if result.status_code != 200:
        logger.error('Error setting starting lineup: {}'.format(result))
    logger.debug('Set starting lineup successfully: {}'.format(result))
    return result
