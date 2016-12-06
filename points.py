"""
Functions used to calculate the expected points total for a given player.
"""
import json
import re
import constants


def predict_points_multiple_gameweeks(json_object, json_fixture_object, num_gameweeks):
    """
    Attempt to predict total number of points across multiple gameweeks
    """
    print('#predict_points_multiple_gameweeks({}..., {}..., {})'.format(json.dumps(json_object)
                                                     [:100], json.dumps(json_fixture_object)[:100], num_gameweeks))
    result = 0
    for gameweek in range(num_gameweeks):
        print(gameweek)
        result += predict_points(json_object, json_fixture_object, gameweek)
    return result

def predict_points(json_object, json_fixture_object, gameweek=0):
    """
    Given a player's json object, this function attempts to predict
    how many points a given player will score in the next gameweek.
    We use the lowest out of 'form' and 'points_per_game' - this should
    make the bot more conservative with transfers.
    """
    print('#predict_points({}..., {}..., {})'.format(json.dumps(json_object)
                                                     [:100], json.dumps(json_fixture_object)[:100], gameweek))
    form = float(json_object["form"])
    ppg = float(json_object["points_per_game"])
    expected_points = (form + ppg) / 2
    injury_ratio = calculate_injury_multiplier(json_object)
    fixture_ratio = calculate_fixture_multiplier(
        json_object, json_fixture_object, gameweek)
    result = expected_points * injury_ratio * fixture_ratio
    print('#predict_points returning: ', result)
    return result


def calculate_injury_multiplier(json_object):
    """
    Given a player's json object, extract an injury/suspension ratio.
    This will act as a multiplier for the expected points. For example, if a player
    is expected to score 10 points, but is only 50% likely to play, the expected points
    are adjusted to 10*0.5 = 5
    """
    print('#calculate_injury_multiplier({}...)'.format(
        json.dumps(json_object)[:100]))
    status = json_object["status"]
    injury_ratio = 1
    if status == "a":
        injury_ratio = 1
    elif status == "i" or status == "s":
        injury_ratio = 0
    elif status == "d":
        news = json_object["news"]
        search_matched = re.search('.*\\s([\\d]+)\\%\\s.*', news)
        if search_matched:
            injury_ratio = int(search_matched.group(1)) / 100
    print('#calculate_injury_multiplier returning: ', injury_ratio)
    return injury_ratio


def calculate_fixture_multiplier(json_object, json_fixture_object, gameweek=0):
    """
    Given a player's json fixture object, calculate a fixture multiplier for
    the expected points. This is calculated using each club's Elo rating.
    """
    print('#calculate_fixture_multiplier({}..., {}..., {})'.format(
        json.dumps(json_object)[:100], json.dumps(json_fixture_object)[:100], gameweek))
    next_match = json_fixture_object["fixtures_summary"][gameweek]
    team_id = json_object['team']
    opposition_team_id = next_match['team_a'] if next_match[
        'is_home'] else next_match['team_h']

    team_elo = constants.CLUB_ELO_RATINGS[team_id]
    opposition_team_elo = constants.CLUB_ELO_RATINGS[opposition_team_id]

    normalised_adjustment = team_elo / opposition_team_elo
    print('#calculate_fixture_multiplier returning: ', normalised_adjustment)
    return normalised_adjustment
