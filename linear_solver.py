"""
Functions needed to solve the linear optimisation problem
"""
import sys
import locale
import constants
import data_grabber
import points
import pulp
import auth_service

locale.setlocale(locale.LC_ALL, '')

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
TEAM_REPRESENTATION = [0] * 20
ESTIMATED_POINTS = 0
NUM_GOAL = 0
NUM_DEF = 0
NUM_MID = 0
NUM_ATT = 0
NUM_CHANGES = 0

# Login and get the current team
auth_service.login(USERNAME, PASSWORD)
TEAM = auth_service.get_transfers_squad()
TEAM_IDS = [player['element'] for player in TEAM['picks']]

# Get some necessary constants
FREE_TRANSFERS = TEAM['helper']['transfers_state']['free']
TEAM_VALUE = TEAM['helper']['value']
BANK = TEAM_VALUE + TEAM['helper']['bank']

# Define the linear optimisation problem
PROB = pulp.LpProblem('Fantasy PL', pulp.LpMaximize)

# Loop through every player and add them to the constraints
PLAYER_DATA = data_grabber.grab_all()["elements"]
for player in PLAYER_DATA:
    print("\rRetrieving player:", player['id'], end='')
    player['selected'] = pulp.LpVariable(player['id'], cat='Binary')
    fixture_data = data_grabber.grab_player_fixtures(player['id'])
    player['expected_points'] = points.predict_points(player, fixture_data)
    TEAM_REPRESENTATION[player['team'] - 1] += player['selected']
    PLAYER_TYPE = player['element_type']
    ESTIMATED_POINTS += player['selected'] * player['expected_points']
    if PLAYER_TYPE == 1:
        NUM_GOAL += player['selected']
    elif PLAYER_TYPE == 2:
        NUM_DEF += player['selected']
    elif PLAYER_TYPE == 3:
        NUM_MID += player['selected']
    elif PLAYER_TYPE == 4:
        NUM_ATT += player['selected']
    if player['id'] in TEAM_IDS:
        index = TEAM_IDS.index(player['id'])
        selling_price = TEAM['picks'][index]['selling_price']
        TEAM_VALUE -= (1 - player['selected']) * selling_price
    else:
        NUM_CHANGES += player['selected']
        TEAM_VALUE += player['selected'] * player['now_cost']

print("\rPlayer data retrieved!\n")

# Add our function to maximise to the problem
FREE_TRANSFERS_USED = pulp.LpVariable('FREE_TRANSFERS_USED', cat='Integer', lowBound=0, upBound=FREE_TRANSFERS)
ESTIMATED_POINTS -= ((NUM_CHANGES - FREE_TRANSFERS_USED) * constants.TRANSFER_POINT_DEDUCTION)
PROB += ESTIMATED_POINTS

# Add constraints
for TEAM_COUNT in TEAM_REPRESENTATION:
    PROB += (TEAM_COUNT <= constants.SQUAD_MAX_PLAYERS_SAME_TEAM)
PROB += (TEAM_VALUE <= BANK)
PROB += (NUM_GOAL == constants.SQUAD_NUM_GOALKEEPERS)
PROB += (NUM_DEF == constants.SQUAD_NUM_DEFENDERS)
PROB += (NUM_MID == constants.SQUAD_NUM_MIDFIELDERS)
PROB += (NUM_ATT == constants.SQUAD_NUM_ATTACKERS)
PROB += (NUM_CHANGES - FREE_TRANSFERS_USED >= 0)

# Solve!
RESULT = PROB.solve()
print("Total expected points:", pulp.value(ESTIMATED_POINTS))
print("Number of transfers:", pulp.value(NUM_CHANGES))
print("Team value: ", locale.currency(pulp.value(TEAM_VALUE)), "\n")

for player in PLAYER_DATA:
    if pulp.value(player['selected']) == 1:
        print(player['expected_points'], player['id'], player['first_name'], player['second_name'], player['element_type'], locale.currency(player['now_cost']))
