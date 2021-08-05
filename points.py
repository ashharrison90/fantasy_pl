"""
Functions used to calculate the expected points total for a given player.
"""
import json
import constants
import logging
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
    form = float(player['form'])
    ppg = float(player['points_per_game'])
    expected_points = max(form, ppg)
    injury_ratio = calculate_injury_multiplier(player)
    fixture_ratio = calculate_fixture_multiplier(
        player, fixture_data, gameweek)
    past_fixture_ratio = calculate_past_fixture_multiplier(player, fixture_data)
    result = expected_points * injury_ratio * fixture_ratio * past_fixture_ratio
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


def calculate_fixture_multiplier(player, fixture_data, gameweek=0):
    """
    Given a player's json fixture object, calculate a fixture multiplier for
    the expected points. This is calculated using each club's Elo rating.
    """
    next_match = fixture_data['fixtures'][gameweek]
    team_id = player['team']
    opposition_team_id = next_match['team_a'] if next_match[
        'is_home'] else next_match['team_h']

    team_elo = constants.CLUB_ELO_RATINGS[team_id]
    opposition_team_elo = constants.CLUB_ELO_RATINGS[opposition_team_id]

    normalised_adjustment = team_elo / opposition_team_elo
    logger.debug('Fixture multiplier for {} {} in gameweek {}: {}'.format(player['first_name'], player['second_name'], gameweek, normalised_adjustment))
    return normalised_adjustment

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
