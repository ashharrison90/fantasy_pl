"""
Functions needed to solve the linear optimisation problem
"""
import locale
import constants
import data_grabber
import points
import pulp

locale.setlocale(locale.LC_ALL, '')

PLAYER_DATA = data_grabber.grab_all()["elements"]
PROB = pulp.LpProblem('Fantasy PL', pulp.LpMaximize)
TOTAL_POINTS = 0
TEAM_VALUE = 0
NUM_GOAL = 0
NUM_DEF = 0
NUM_MID = 0
NUM_ATT = 0

for player in PLAYER_DATA:
    print("\rGetting data for player:", player['id'], end='')
    player['selected'] = pulp.LpVariable(player['id'], cat='Binary')
    fixture_data = data_grabber.grab_player_fixtures(player['id'])
    player['expected_points'] = points.predict_points(player, fixture_data)
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

print("\n")

# Add our function to maximise to the problem
PROB += TOTAL_POINTS

# Add constraints
PROB += (TEAM_VALUE <= constants.INITIAL_TEAM_VALUE)
PROB += (NUM_GOAL == constants.SQUAD_NUM_GOALKEEPERS)
PROB += (NUM_DEF == constants.SQUAD_NUM_DEFENDERS)
PROB += (NUM_MID == constants.SQUAD_NUM_MIDFIELDERS)
PROB += (NUM_ATT == constants.SQUAD_NUM_ATTACKERS)

# Solve!
RESULT = PROB.solve()
print("Total expected points:", pulp.value(TOTAL_POINTS))
print("Team value: ", locale.currency(pulp.value(TEAM_VALUE)), "\n")

for player in PLAYER_DATA:
    if pulp.value(player['selected']) == 1:
        print(player['expected_points'], player['id'], player['first_name'], player['second_name'], player['element_type'], locale.currency(player['now_cost']))
