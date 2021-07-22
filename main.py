"""
The main program.
    1. Log in to fantasy.premierleague.com.
    2. Get the current squad.
    3. Calculate the best squad possible for next week.
    4. Update the squad on fantasy.premierleague.com.
    5. Calculate the best possible starting lineup for next week.
    6. Update the starting lineup on fantasy.premierleague.com.
"""
import codecs
import sys
import constants
import linear_solver
import web_service
import logging
from logging.handlers import RotatingFileHandler
logging.basicConfig(
    handlers=[RotatingFileHandler('./.debug.log', maxBytes=10000000, backupCount=1)],
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)

# Use a StreamWriter to output in UTF-8 else some of the logs can cause errors
# This may result in some characters not rendering correctly in Windows cmd window
# http://stackoverflow.com/questions/16346914/python-3-2-unicodeencodeerror-charmap-codec-cant-encode-character-u2013-i
if sys.stdout.encoding != 'UTF-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Get Elo data for clubs and save it to the constants
# This will be a dictionary of team ids and corresponding Elo ratings
print('Getting Elo ratings...')
constants.CLUB_ELO_RATINGS = web_service.get_club_elo_ratings()

# Login
print('Logging in to {}'.format(constants.LOGIN_URL))
USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
web_service.login(USERNAME, PASSWORD)

# Get the current squad
print('Retrieving the current squad')
CURRENT_SQUAD = web_service.get_transfers_squad()

# Calculate the new squad
print('Calculating the new squad')
NEW_SQUAD = linear_solver.select_squad(CURRENT_SQUAD)

# make transfers to update the squad on fantasy.premierleague.com
print('Making transfers')
WILDCARD_STATUS = (CURRENT_SQUAD['helper']['wildcard_status'] == 'available')
TRANSFER_OBJECT = web_service.create_transfers_object(
    CURRENT_SQUAD['picks'], NEW_SQUAD, (constants.NUM_CHANGES >= 6) and WILDCARD_STATUS)
web_service.make_transfers(TRANSFER_OBJECT)

# Calculate the new starting lineup
print('Calculating the new starting lineup')
NEW_STARTING = linear_solver.select_starting(NEW_SQUAD)

# update the starting lineup on fantasy.premierleague.com
print('Updating the starting lineup')
web_service.set_starting_lineup(NEW_STARTING)
