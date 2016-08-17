"""
Some useful constants for the fantasy premier league
"""
# URLs needed
FANTASY_URL = 'https://fantasy.premierleague.com'
FANTASY_API_URL = 'https://fantasy.premierleague.com/drf/bootstrap-static'
FANTASY_API_DYNAMIC_URL = 'https://fantasy.premierleague.com/drf/bootstrap-dynamic'
FANTASY_PLAYER_API_URL = 'https://fantasy.premierleague.com/drf/element-summary/'
LOGIN_URL = 'https://users.premierleague.com/accounts/login/'
SQUAD_URL = 'https://fantasy.premierleague.com/drf/my-team/'
TRANSFER_URL = 'https://fantasy.premierleague.com/drf/transfers'

# Data we grab from the web services
NEXT_EVENT = None
SQUAD_ID = None
TRANSFER_DEADLINE = None

# Constraints
STARTING_MIN_ATTACKERS = 1
STARTING_MIN_DEFENDERS = 3
STARTING_MIN_GOALKEEPERS = 1
STARTING_MIN_MIDFIELDERS = 2
STARTING_SIZE = 11
SQUAD_MAX_PLAYERS_SAME_TEAM = 3
SQUAD_NUM_ATTACKERS = 3
SQUAD_NUM_DEFENDERS = 5
SQUAD_NUM_GOALKEEPERS = 2
SQUAD_NUM_MIDFIELDERS = 5
INITIAL_TEAM_VALUE = 1000
TRANSFER_POINT_DEDUCTION = 4
