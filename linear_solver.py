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
TEAM_VALUE = 0
TOTAL_POINTS = 0
NUM_GOAL = 0
NUM_DEF = 0
NUM_MID = 0
NUM_ATT = 0
NUM_CHANGES = 0

# Login and get the current team
auth_service.login(USERNAME, PASSWORD)
TEAM = auth_service.get_squad()
TEAM_IDS = [player['element'] for player in TEAM]

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
    TOTAL_POINTS += player['selected'] * player['expected_points']
    TEAM_VALUE += player['selected'] * player['now_cost']
    if PLAYER_TYPE == 1:
        NUM_GOAL += player['selected']
    elif PLAYER_TYPE == 2:
        NUM_DEF += player['selected']
    elif PLAYER_TYPE == 3:
        NUM_MID += player['selected']
    elif PLAYER_TYPE == 4:
        NUM_ATT += player['selected']
    if player['id'] not in TEAM_IDS:
        NUM_CHANGES += player['selected']

print("\rPlayer data retrieved!\n")

# Add our function to maximise to the problem
TOTAL_POINTS -= (NUM_CHANGES * constants.TRANSFER_POINT_DEDUCTION)
PROB += TOTAL_POINTS

# Add constraints
for TEAM_COUNT in TEAM_REPRESENTATION:
    PROB += (TEAM_COUNT <= constants.SQUAD_MAX_PLAYERS_SAME_TEAM)
PROB += (TEAM_VALUE <= constants.INITIAL_TEAM_VALUE)
PROB += (NUM_GOAL == constants.SQUAD_NUM_GOALKEEPERS)
PROB += (NUM_DEF == constants.SQUAD_NUM_DEFENDERS)
PROB += (NUM_MID == constants.SQUAD_NUM_MIDFIELDERS)
PROB += (NUM_ATT == constants.SQUAD_NUM_ATTACKERS)

# Solve!
RESULT = PROB.solve()
print("Total expected points:", pulp.value(TOTAL_POINTS))
print("Number of transfers:", pulp.value(NUM_CHANGES))
print("Team value: ", locale.currency(pulp.value(TEAM_VALUE)), "\n")

for player in PLAYER_DATA:
    if pulp.value(player['selected']) == 1:
        print(player['expected_points'], player['id'], player['first_name'], player['second_name'], player['element_type'], locale.currency(player['now_cost']))
