"""
The main program.
    1. Log in to fantasy.premierleague.com.
    2. Get the current squad.
    3. Calculate the best squad possible for next week.
    4. Update the squad on fantasy.premierleague.com.
    5. Calculate the best possible starting lineup for next week.
    6. Update the starting lineup on fantasy.premierleague.com.
"""
import argparse
import codecs
import constants
import linear_solver
import logging
import neural_network
import sys
import web_service
import getpass

# Set up the logger
# Log info to stdout, debug to file
fileHandler = logging.FileHandler('./.debug.log', 'w')
fileHandler.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.INFO)
logging.basicConfig(
    handlers=[
        consoleHandler,
        fileHandler
    ],
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)
logger = logging.getLogger()

# Use a StreamWriter to output in UTF-8 else some of the logs can cause errors
# This may result in some characters not rendering correctly in Windows cmd window
# http://stackoverflow.com/questions/16346914/python-3-2-unicodeencodeerror-charmap-codec-cant-encode-character-u2013-i
if sys.stdout.encoding != 'UTF-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Set up the command line parser
parser = argparse.ArgumentParser(description='Mr Robot v3.0')
parser.add_argument('username', help='Login username for fantasy.premierleague.com')
parser.add_argument('--password', help='Login password for fantasy.premierleague.com')
parser.add_argument('--apply', action='store_true', help='Whether to apply the changes (default: False)')
parser.add_argument('--ignore-squad', action='store_true', help='Whether to ignore the current squad when calculating the new squad (default: False)')
parser.add_argument('--update-model', action='store_true', help='Whether to recalculate the model or use the stored one. Note: this can take a long time! (default: False)')

args = parser.parse_args()

if not args.password:
    args.password = getpass.getpass(prompt='Password for {}'.format(constants.LOGIN_URL))

# Login
logger.info('Logging in to {}'.format(constants.LOGIN_URL))
web_service.login(args.username, args.password)

# Initialise the neural network
logger.info('Initialising the neural network')
neural_network.init()
if args.update_model:
    logger.info('Updating the model')
    neural_network.train_model()
    neural_network.test_model()
    neural_network.save_model()
else:
    logger.info('Loading model')
    neural_network.load_model()

# Get the current squad
if not args.ignore_squad:
    logger.info('Retrieving the current squad')
    CURRENT_SQUAD = web_service.get_transfers_squad()

# Calculate the new squad
logger.info('Calculating the new squad')
if args.ignore_squad:
    NEW_SQUAD = linear_solver.select_squad_ignore_transfers(constants.INITIAL_TEAM_VALUE)
else:
    NEW_SQUAD = linear_solver.select_squad(CURRENT_SQUAD)

# Calculate the new starting lineup
logger.info('Calculating the new starting lineup')
NEW_STARTING = linear_solver.select_starting(NEW_SQUAD)

if args.apply:
    # make transfers to update the squad on fantasy.premierleague.com
    logger.info('Making transfers')
    WILDCARD_STATUS = (CURRENT_SQUAD['helper']['wildcard_status'] == 'available')
    TRANSFER_OBJECT = web_service.create_transfers_object(
        CURRENT_SQUAD['picks'], NEW_SQUAD, (constants.NUM_CHANGES >= 6) and WILDCARD_STATUS)
    web_service.make_transfers(TRANSFER_OBJECT)

    # update the starting lineup on fantasy.premierleague.com
    logger.info('Updating the starting lineup')
    web_service.set_starting_lineup(NEW_STARTING)
