"""
Functions used to calculate the expected points total for a given player.
"""
import constants
import logging
import neural_network
import web_service

logger = logging.getLogger()

def predict_points_multiple_gameweeks(player, fixture_data, num_gameweeks):
    """
    Attempt to predict total number of points across multiple gameweeks
    """
    result = 0
    for gameweek in range(num_gameweeks):
        result += predict_points(player, fixture_data, gameweek)
    logger.debug('Predicted points for {} {} over {} weeks: {}'.format(player['first_name'], player['second_name'], num_gameweeks, result))                                                                    
    return result


def predict_points(player, fixture_data, gameweek=0):
    """
    Given a player's json object, this function attempts to predict
    how many points a given player will score in the next gameweek.
    We use the highest out of 'form' and 'points_per_game'
    """
    next_match = fixture_data['fixtures'][gameweek]
    opposition_team_id = next_match['team_a'] if next_match[
        'is_home'] else next_match['team_h']
    # Get data for all teams.
    team_data = web_service.get_team_data()
    for team in team_data:
        if team['id'] == opposition_team_id:
            opposition_team_name = team['name']
            break
    if player['element_type'] == 1:
        position = 'GK'
    elif player['element_type'] == 2:
        position = 'DEF'
    elif player['element_type'] == 3:
        position = 'MID'
    elif player['element_type'] == 4:
        position = 'FWD'
    try:
        expected_points = neural_network.predict_points(
            '{} {}'.format(player['first_name'], player['second_name']),
            opposition_team_name,
            position,
            next_match['is_home'],
            2021,
            next_match['kickoff_time'],
            next_match['event'],
            player['now_cost'],
            next_match['event']
        )
    except:
        # if the model fails for some reason, fall back to a naive average
        # this can happen for a few reasons:
        #   - player is unknown (new player for this season)
        #   - team is unknown (new team for this season)
        expected_points = float(player['points_per_game'])

    injury_ratio = calculate_injury_multiplier(player)
    past_fixture_ratio = calculate_past_fixture_multiplier(player, fixture_data)
    result = expected_points * injury_ratio * past_fixture_ratio
    logger.debug('Predicted points for {} {} in gameweek {}: {}'.format(player['first_name'], player['second_name'], gameweek, result))                                                                    
    return result


def calculate_injury_multiplier(player):
    """
    Given a player's json object, extract an injury/suspension ratio.
    This will act as a multiplier for the expected points. For example, if a player
    is expected to score 10 points, but is only 50% likely to play, the expected points
    are adjusted to 10*0.5 = 5
    """
    next_round_chance = player['chance_of_playing_next_round'] / 100 if player[
        'chance_of_playing_next_round'] is not None else 1

    logger.debug('Injury multiplier for {} {}: {}'.format(player['first_name'], player['second_name'], next_round_chance))
    return next_round_chance

def calculate_past_fixture_multiplier(player, fixture_data):
    """
    Given a player's json fixture object, calculate a past fixture multiplier for
    the expected points. This is a ratio of total minutes played divided by total
    possible minutes. Prevents players being chosen who barely play but have a very
    high points per game.
    """
    past_games = fixture_data['history']
    past_season_games = fixture_data['history_past']
    multiplier = 1
    if len(past_games):
        total_games = sum(1 if fixture['minutes'] > 0 else 0 for fixture in past_games)
        multiplier = total_games / len(past_games)
    elif len(past_season_games):
        total_minutes = past_season_games[-1]['minutes']
        multiplier = total_minutes / (constants.TOTAL_GAMES_IN_SEASON * 90)
    logger.debug('Past fixture multiplier for {} {}: {}'.format(player['first_name'], player['second_name'], multiplier))
    return multiplier
