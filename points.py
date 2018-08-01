"""
Functions used to calculate the expected points total for a given player.
"""
import json
import constants


def predict_points_multiple_gameweeks(json_object, json_fixture_object, num_gameweeks):
    """
    Attempt to predict total number of points across multiple gameweeks
    """
    result = 0
    for gameweek in range(num_gameweeks):
        result += predict_points(json_object, json_fixture_object, gameweek)
    print('#predict_points_multiple_gameweeks({}..., {}..., {})'.format(json.dumps(json_object)
                                                                        [:100], json.dumps(json_fixture_object)[:100], num_gameweeks), result)
    return result


def predict_points(json_object, json_fixture_object, gameweek=0):
    """
    Given a player's json object, this function attempts to predict
    how many points a given player will score in the next gameweek.
    We use the highest out of 'form' and 'points_per_game'
    """
    form = float(json_object['form'])
    ppg = float(json_object['points_per_game'])
    expected_points = max(form, ppg)
    injury_ratio = calculate_injury_multiplier(json_object)
    fixture_ratio = calculate_fixture_multiplier(
        json_object, json_fixture_object, gameweek)
    past_fixture_ratio = calculate_past_fixture_multiplier(json_fixture_object)
    result = expected_points * injury_ratio * fixture_ratio * past_fixture_ratio
    print('#predict_points({}..., {}..., {})'.format(json.dumps(json_object)
                                                     [:100], json.dumps(json_fixture_object)[:100], gameweek), result)
    return result


def calculate_injury_multiplier(json_object):
    """
    Given a player's json object, extract an injury/suspension ratio.
    This will act as a multiplier for the expected points. For example, if a player
    is expected to score 10 points, but is only 50% likely to play, the expected points
    are adjusted to 10*0.5 = 5
    """
    next_round_chance = json_object['chance_of_playing_next_round'] / 100 if json_object[
        'chance_of_playing_next_round'] is not None else 1

    print('#calculate_injury_multiplier({}...)'.format(
        json.dumps(json_object)[:100]), next_round_chance)
    return next_round_chance


def calculate_fixture_multiplier(json_object, json_fixture_object, gameweek=0):
    """
    Given a player's json fixture object, calculate a fixture multiplier for
    the expected points. This is calculated using each club's Elo rating.
    """
    next_match = json_fixture_object['fixtures_summary'][gameweek]
    team_id = json_object['team']
    opposition_team_id = next_match['team_a'] if next_match[
        'is_home'] else next_match['team_h']

    team_elo = constants.CLUB_ELO_RATINGS[team_id]
    opposition_team_elo = constants.CLUB_ELO_RATINGS[opposition_team_id]

    normalised_adjustment = team_elo / opposition_team_elo
    print('#calculate_fixture_multiplier({}..., {}..., {})'.format(
        json.dumps(json_object)[:100], json.dumps(json_fixture_object)[:100], gameweek), normalised_adjustment)
    return normalised_adjustment

def calculate_past_fixture_multiplier(json_fixture_object):
    """
    Given a player's json fixture object, calculate a past fixture multiplier for
    the expected points. This is a ratio of total minutes played divided by total
    possible minutes. Prevents players being chosen who barely play but have a very
    high points per game.
    """
    past_games = json_fixture_object['history_summary']
    multiplier = 1
    if len(past_games):
        total_minutes = sum([fixture['minutes'] for fixture in past_games])
        multiplier = total_minutes / (len(past_games) * 90)
    print('#calculate_past_fixture_multiplier({}...)'.format(json.dumps(json_fixture_object)[:100]), multiplier)
    return multiplier
