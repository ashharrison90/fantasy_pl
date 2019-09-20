"""
Some useful constants for the fantasy premier league
"""
# URLs needed
CLUB_ELO_URL = 'http://api.clubelo.com/'
FANTASY_URL = 'https://fantasy.premierleague.com'
FANTASY_API_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'
FANTASY_API_DYNAMIC_URL = 'https://fantasy.premierleague.com/api/me/'
FANTASY_PLAYER_API_URL = 'https://fantasy.premierleague.com/api/element-summary/'
LOGIN_URL = 'https://users.premierleague.com/accounts/login/'
SQUAD_URL = 'https://fantasy.premierleague.com/api/my-team/'
TRANSFER_URL = 'https://fantasy.premierleague.com/api/transfers/'

# Other constants
NUM_CHANGES = 0
TOTAL_GAMES_IN_SEASON = 38

# Data we grab from the web services
NEXT_EVENT = None
SQUAD_ID = None
TRANSFER_DEADLINE = None
CLUB_ELO_RATINGS = {}

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
