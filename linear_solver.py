"""
Functions needed to solve the linear optimisation problem
"""
import constants
import locale
import logging
import platform
import points
import pulp
import web_service

logger = logging.getLogger()
locale.setlocale(locale.LC_ALL, '')

def select_squad(current_squad):
    """
    Given the current squad, calculate the best possible squad for next week.
    """
    # Define the squad linear optimisation problem
    squad_prob = pulp.LpProblem('squad', pulp.LpMaximize)

    # Define and get some necessary constants
    teams_represented = [0] * 20
    new_squad = []
    new_squad_points = num_changes = num_goal = num_def = num_mid = num_att = num_cheap = 0
    current_squad_ids = [player['element']
                         for player in current_squad['picks']]
    free_transfers = max(0, current_squad['transfers']['limit'] or 0)
    squad_value = current_squad['transfers']['value']
    bank = current_squad['transfers']['bank']
    total_bank = squad_value + bank

    # Loop through every player and add them to the constraints
    all_players = web_service.get_all_player_data()['elements']
    for player in all_players:
        fixture_data = web_service.get_player_fixtures(player['id'])
        player['expected_points'] = points.predict_points_multiple_gameweeks(player, fixture_data, 3)
        expected_points_this_gameweek = points.predict_points(player, fixture_data)
        player['expected_points_this_gameweek'] = expected_points_this_gameweek
        player['selected'] = pulp.LpVariable(
            'player_' + str(player['id']), cat='Binary')
        teams_represented[player['team'] - 1] += player['selected']
        player_type = player['element_type']
        new_squad_points += player['selected'] * player['expected_points_this_gameweek']
        if player['now_cost'] <= 51.00:
            num_cheap += player['selected']
        logger.info('Predicted points for {} {}: {:.2f}'.format(player['first_name'], player['second_name'], expected_points_this_gameweek))

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
            bank += (1 - player['selected']) * selling_price
            squad_value -= (1 - player['selected']) * player['now_cost']
        else:
            num_changes += player['selected']
            bank -= player['selected'] * player['now_cost']
            squad_value += player['selected'] * player['now_cost']

    # Account for free transfers and cost transfers
    free_transfers_used = pulp.LpVariable(
        'free_transfers_used',
        cat='Integer',
        lowBound=0,
        upBound=free_transfers
    )
    transfer_cost = ((num_changes - free_transfers_used)
                     * constants.TRANSFER_POINT_DEDUCTION)

    # Add problem and constraints
    squad_prob += new_squad_points - transfer_cost
    for team_count in teams_represented:
        squad_prob += (team_count <= constants.SQUAD_MAX_PLAYERS_SAME_TEAM)
    squad_prob += (squad_value + bank <= total_bank)
    squad_prob += (bank >= 0)
    squad_prob += (num_goal == constants.SQUAD_NUM_GOALKEEPERS)
    squad_prob += (num_def == constants.SQUAD_NUM_DEFENDERS)
    squad_prob += (num_mid == constants.SQUAD_NUM_MIDFIELDERS)
    squad_prob += (num_att == constants.SQUAD_NUM_ATTACKERS)
    squad_prob += (num_changes - free_transfers_used >= 0)
    # We want to prioritise the starting lineup by setting a limit on the cost of the bench.
    # But this seems impossible to write as a condition.
    # Instead, write the condition as having at least 4 cheap players.
    # This effectively gives us a limit for the whole bench.
    squad_prob += (num_cheap >= 4)

    # Solve! On the pi, we need to use the GLPK solver.
    if platform.system() == 'Linux':
        squad_prob.solve(pulp.GLPK_CMD(msg=0))
    else:
        squad_prob.solve()

    for player in all_players:
        if pulp.value(player['selected']) == 1:
            new_squad.append(player)

    logger.info('Estimated squad points: {:.2f}'.format(pulp.value(new_squad_points)))
    logger.info('Number of transfers: {}'.format(pulp.value(num_changes)))
    logger.info('Cost of transfers: {}'.format(pulp.value(transfer_cost)))
    logger.info('Team value: {}'.format(locale.currency(pulp.value(squad_value))))
    logger.info('Bank: {}'.format(locale.currency(pulp.value(bank))))

    constants.NUM_CHANGES = pulp.value(num_changes)

    logger.debug('Current squad: {}'.format(current_squad))
    logger.debug('New squad: {}'.format(new_squad))
    return new_squad


def select_squad_ignore_transfers(bank):
    """
    Ignoring the current squad, calculate the best possible squad for next week.
    """
    # Define the squad linear optimisation problem
    squad_prob = pulp.LpProblem('squad', pulp.LpMaximize)

    # Define and get some necessary constants
    teams_represented = [0] * 20
    new_squad = []
    new_squad_points = squad_value = num_goal = num_def = num_mid = num_att = num_cheap = 0

    # Loop through every player and add them to the constraints
    all_players = web_service.get_all_player_data()['elements']
    for player in all_players:
        fixture_data = web_service.get_player_fixtures(player['id'])
        player['expected_points'] = points.predict_points_multiple_gameweeks(player, fixture_data, 3)
        expected_points_this_gameweek = points.predict_points(player, fixture_data)
        player['expected_points_this_gameweek'] = expected_points_this_gameweek
        player['selected'] = pulp.LpVariable(
            'player_' + str(player['id']), cat='Binary')
        teams_represented[player['team'] - 1] += player['selected']
        player_type = player['element_type']
        new_squad_points += player['selected'] * player['expected_points']
        squad_value += player['selected'] * player['now_cost']
        if player['now_cost'] <= 51.00:
            num_cheap += player['selected']
        logger.info('Predicted points for {} {}: {:.2f}'.format(player['first_name'], player['second_name'], expected_points_this_gameweek))

        if player_type == 1:
            num_goal += player['selected']
        elif player_type == 2:
            num_def += player['selected']
        elif player_type == 3:
            num_mid += player['selected']
        elif player_type == 4:
            num_att += player['selected']

    # Add problem and constraints
    squad_prob += new_squad_points
    for team_count in teams_represented:
        squad_prob += (team_count <= constants.SQUAD_MAX_PLAYERS_SAME_TEAM)
    squad_prob += (squad_value <= bank)
    squad_prob += (num_goal == constants.SQUAD_NUM_GOALKEEPERS)
    squad_prob += (num_def == constants.SQUAD_NUM_DEFENDERS)
    squad_prob += (num_mid == constants.SQUAD_NUM_MIDFIELDERS)
    squad_prob += (num_att == constants.SQUAD_NUM_ATTACKERS)
    # We want to prioritise the starting lineup by setting a limit on the cost of the bench.
    # But this seems impossible to write as a condition.
    # Instead, write the condition as having at least 4 cheap players.
    # This effectively gives us a limit for the whole bench.
    squad_prob += (num_cheap >= 4)

    # Solve! On the pi, we need to use the GLPK solver.
    if platform.system() == 'Linux':
        squad_prob.solve(pulp.GLPK_CMD(msg=0))
    else:
        squad_prob.solve()

    for player in all_players:
        if pulp.value(player['selected']) == 1:
            new_squad.append(player)

    logger.info('Estimated squad points: {:.2f}'.format(pulp.value(new_squad_points)))
    logger.info('Team value: {}'.format(locale.currency(pulp.value(squad_value))))

    logger.debug('New squad: {}'.format(new_squad))
    return new_squad


def select_starting(squad):
    """
    Given a squad, select the best possible starting lineup.
    """
    # Define the starting lineup linear optimisation problem
    starting_prob = pulp.LpProblem('starting_line_up', pulp.LpMaximize)

    # Define and get some necessary constants
    starting_points = num_goal_starting = num_def_starting = num_mid_starting = num_att_starting = num_starting = 0
    starting_lineup = {'picks': []}

    for player in squad:
        player['starting'] = pulp.LpVariable(
            'player_' + str(player['id']) + '_starting', cat='Binary')
        player_type = player['element_type']
        num_starting += player['starting']
        starting_points += player['starting'] * player['expected_points_this_gameweek']

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

    # Solve! On the pi, we need to use the GLPK solver.
    if platform.system() == 'Linux':
        starting_prob.solve(pulp.GLPK_CMD(msg=0))
    else:
        starting_prob.solve()
    logger.info('Estimated starting points: {:.2f}'.format(pulp.value(starting_points)))

    # Split the squad into starting lineup and subs
    starting_list = [player for player in squad if pulp.value(
        player['starting']) == 1]
    subs_list = [player for player in squad if pulp.value(
        player['starting']) == 0]

    # First sort the starting lineup by expected points to give us the captain
    # and vice captain
    starting_list = sorted(
        starting_list, key=lambda player: -player['expected_points_this_gameweek'])
    captain_id = starting_list[0]['id']
    vice_captain_id = starting_list[1]['id']

    # Now sort the starting lineup by element type
    # This will allow us to give each player the correct position
    starting_list = sorted(
        starting_list, key=lambda player: player['element_type'])
    for player in starting_list:
        starting_lineup['picks'].append({
            'element': player['id'],
            'position': starting_list.index(player) + 1,
            'is_captain': 'false',
            'is_vice_captain': 'false'
        })
        marker = 'X'
        if player['id'] == captain_id:
            starting_lineup['picks'][-1]['is_captain'] = 'true'
            marker = 'C'
        elif player['id'] == vice_captain_id:
            starting_lineup['picks'][-1]['is_vice_captain'] = 'true'
            marker='V'
        logger.info('{} {}  {}  {}  {:.2f}  {:.2f}'.format(
            marker,
            locale.currency(player['now_cost']),
            player['first_name'],
            player['second_name'],
            player['expected_points_this_gameweek'],
            player['expected_points']
        ))

    # Sort the subs by expected points.
    # We want the subs expected to score the most points ordered first.
    sub_counter = 13
    subs_list = sorted(subs_list, key=lambda player: -
                       player['expected_points'])
    for player in subs_list:
        logger.info('{} {}  {}  {}  {:.2f}  {:.2f}'.format(
            '-',
            locale.currency(player['now_cost']),
            player['first_name'],
            player['second_name'],
            player['expected_points_this_gameweek'],
            player['expected_points']
        ))

        starting_lineup['picks'].append({
            'element': player['id'],
            'position': sub_counter,
            'is_captain': 'false',
            'is_vice_captain': 'false'
        })

        if player['element_type'] == 1:
            starting_lineup['picks'][-1]['position'] = 12
        else:
            sub_counter += 1

    logger.debug('New starting lineup: {}'.format(starting_lineup))
    return starting_lineup
