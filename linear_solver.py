"""
Functions needed to solve the linear optimisation problem
"""
import locale
import constants
import points
import pulp
import web_service

locale.setlocale(locale.LC_ALL, '')

def select_squad(current_squad):
    """
    Given the current squad, calculate the best possible squad for next week.
    """
    print("Calculating optimal squad...")
    # Define and get some necessary constants
    teams_represented = [0] * 20
    new_squad = []
    new_squad_points = num_changes = num_goal = num_def = num_mid = num_att = 0
    current_squad_ids = [player['element'] for player in current_squad['picks']]
    free_transfers = current_squad['helper']['transfers_state']['free']
    squad_value = current_squad['helper']['value']
    bank = squad_value + current_squad['helper']['bank']

    # Define the squad linear optimisation problem
    squad_prob = pulp.LpProblem('Squad points', pulp.LpMaximize)

    # Loop through every player and add them to the constraints
    all_players = web_service.grab_all()["elements"]
    for player in all_players:
        print("\rRetrieving player:", player['id'], end='')
        player['selected'] = pulp.LpVariable("player_" + str(player['id']), cat='Binary')
        fixture_data = web_service.grab_player_fixtures(player['id'])
        player['expected_points'] = points.predict_points(player, fixture_data)
        teams_represented[player['team'] - 1] += player['selected']
        player_type = player['element_type']
        new_squad_points += player['selected'] * player['expected_points']
        if player_type == 1:
            num_goal += player['selected']
        elif player_type == 2:
            num_def += player['selected']
        elif player_type == 3:
            num_mid += player['selected']
        elif player_type == 4:
            num_att += player['selected']
        if player['id'] in current_squad_ids:
            index = current_squad_ids.index(player['id'])
            selling_price = current_squad['picks'][index]['selling_price']
            squad_value -= (1 - player['selected']) * selling_price
        else:
            num_changes += player['selected']
            squad_value += player['selected'] * player['now_cost']

    print("\rPlayer data retrieved!\n")

    # Account for free transfers and cost transfers
    free_transfers_used = pulp.LpVariable(
        'free_transfers_used',
        cat='Integer',
        lowBound=0,
        upBound=free_transfers
    )
    transfer_cost = ((num_changes - free_transfers_used) * constants.TRANSFER_POINT_DEDUCTION)

    # Add problem and constraints
    squad_prob += new_squad_points - transfer_cost
    for team_count in teams_represented:
        squad_prob += (team_count <= constants.SQUAD_MAX_PLAYERS_SAME_TEAM)
    squad_prob += (squad_value <= bank)
    squad_prob += (num_goal == constants.SQUAD_NUM_GOALKEEPERS)
    squad_prob += (num_def == constants.SQUAD_NUM_DEFENDERS)
    squad_prob += (num_mid == constants.SQUAD_NUM_MIDFIELDERS)
    squad_prob += (num_att == constants.SQUAD_NUM_ATTACKERS)
    squad_prob += (num_changes - free_transfers_used >= 0)

    # Solve!
    # On the pi, we need to use the GLPK solver.
    squad_prob.solve(pulp.GLPK_CMD(msg=0))

    for player in all_players:
        if pulp.value(player['selected']) == 1:
            new_squad.append(player)

    print("Estimated squad points:", pulp.value(new_squad_points))
    print("Number of transfers:", pulp.value(num_changes))
    print("Cost of transfers:", pulp.value(transfer_cost))
    print("Team value: ", locale.currency(pulp.value(squad_value)), "\n")
    return new_squad

def select_squad_ignore_transfers(bank):
    """
    Ignoring the current squad, calculate the best possible squad for next week.
    """
    print("Calculating optimal squad...")
    # Define and get some necessary constants
    teams_represented = [0] * 20
    new_squad = []
    new_squad_points = squad_value = num_goal = num_def = num_mid = num_att = 0

    # Define the squad linear optimisation problem
    squad_prob = pulp.LpProblem('Squad points', pulp.LpMaximize)

    # Loop through every player and add them to the constraints
    all_players = web_service.grab_all()["elements"]
    for player in all_players:
        print("\rRetrieving player:", player['id'], end='')
        player['selected'] = pulp.LpVariable("player_" + player['id'], cat='Binary')
        fixture_data = web_service.grab_player_fixtures(player['id'])
        player['expected_points'] = points.predict_points(player, fixture_data)
        teams_represented[player['team'] - 1] += player['selected']
        player_type = player['element_type']
        new_squad_points += player['selected'] * player['expected_points']
        squad_value += player['selected'] * player['now_cost']
        if player_type == 1:
            num_goal += player['selected']
        elif player_type == 2:
            num_def += player['selected']
        elif player_type == 3:
            num_mid += player['selected']
        elif player_type == 4:
            num_att += player['selected']

    print("\rPlayer data retrieved!\n")

    # Add problem and constraints
    squad_prob += new_squad_points
    for team_count in teams_represented:
        squad_prob += (team_count <= constants.SQUAD_MAX_PLAYERS_SAME_TEAM)
    squad_prob += (squad_value <= bank)
    squad_prob += (num_goal == constants.SQUAD_NUM_GOALKEEPERS)
    squad_prob += (num_def == constants.SQUAD_NUM_DEFENDERS)
    squad_prob += (num_mid == constants.SQUAD_NUM_MIDFIELDERS)
    squad_prob += (num_att == constants.SQUAD_NUM_ATTACKERS)

    # Solve!
    # On the pi, we need to use the GLPK solver.
    squad_prob.solve(pulp.GLPK_CMD(msg=0))

    for player in all_players:
        if pulp.value(player['selected']) == 1:
            new_squad.append(player)

    print("Estimated squad points:", pulp.value(new_squad_points))
    print("Team value: ", locale.currency(pulp.value(squad_value)), "\n")
    return new_squad

def select_starting(squad):
    """
    Given a squad, select the best possible starting lineup.
    """
    print("Calculating optimal starting lineup...")
    # Define and get some necessary constants
    starting_points = num_goal_starting = num_def_starting = num_mid_starting = num_att_starting = num_starting = 0
    starting_lineup = {'picks': []}
    # Define the starting lineup linear optimisation problem
    starting_prob = pulp.LpProblem('Starting line up points', pulp.LpMaximize)

    for player in squad:
        player['starting'] = pulp.LpVariable("player_" + str(player['id']) + "_starting", cat='Binary')
        player_type = player['element_type']
        num_starting += player['starting']
        starting_points += player['starting'] * player['expected_points']
        if player_type == 1:
            num_goal_starting += player['starting']
        elif player_type == 2:
            num_def_starting += player['starting']
        elif player_type == 3:
            num_mid_starting += player['starting']
        elif player_type == 4:
            num_att_starting += player['starting']

    # Add problem and constraints
    starting_prob += starting_points
    starting_prob += (num_goal_starting == constants.STARTING_MIN_GOALKEEPERS)
    starting_prob += (num_def_starting >= constants.STARTING_MIN_DEFENDERS)
    starting_prob += (num_mid_starting >= constants.STARTING_MIN_MIDFIELDERS)
    starting_prob += (num_att_starting >= constants.STARTING_MIN_ATTACKERS)
    starting_prob += (num_starting == constants.STARTING_SIZE)

    # Solve!
    # On the pi, we need to use the GLPK solver.
    starting_prob.solve(pulp.GLPK_CMD(msg=0))
    print("Estimated starting points:", pulp.value(starting_points))

    counter = 1
    sub_counter = 13
    captain = vice_captain = (0, 0)
    squad = sorted(squad, key=lambda player: (player['starting'], player['element_type']))
    for player in squad:
        player_type = player['element_type']
        if pulp.value(player['starting']) == 1:
            print("X", player['expected_points'], player['id'], player['first_name'], player['second_name'], player['element_type'], locale.currency(player['now_cost']))
            if player['expected_points'] > captain[1]:
                vice_captain = captain
                captain = (player['id'], player['expected_points'])
            elif player['expected_points'] > vice_captain[1]:
                vice_captain = (player['id'], player['expected_points'])
            starting_lineup['picks'].append({
                'element': player['id'],
                'position': counter,
                'is_captain': 'false',
                'is_vice_captain': 'false'
            })
            counter += 1
        else:
            print("-", player['expected_points'], player['id'], player['first_name'], player['second_name'], player['element_type'], locale.currency(player['now_cost']))
            if player_type == 1:
                starting_lineup['picks'].append({
                    'element': player['id'],
                    'position': 12,
                    'is_captain': 'false',
                    'is_vice_captain': 'false'
                })
            else:
                starting_lineup['picks'].append({
                    'element': player['id'],
                    'position': sub_counter,
                    'is_captain': 'false',
                    'is_vice_captain': 'false'
                })
                sub_counter += 1


    # Set the captain and vice captain
    for player in starting_lineup['picks']:
        if player['element'] == captain[0]:
            player['is_captain'] = 'true'
        elif player['element'] == vice_captain[0]:
            player['is_vice_captain'] = 'true'

    return starting_lineup
