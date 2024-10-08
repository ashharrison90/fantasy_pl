"""
Functions used to calculate the expected points total for a given player.
"""
import constants
import logging
import neural_network
import web_service

logger = logging.getLogger()

# Store a dict of players that have had an error when predicting points
# This is to avoid spamming the logs with the same error
HAS_MODEL_ERROR = {}
# Same here, maintain a cache of multipliers to avoid recalculating
INJURY_MULTIPLIERS = {}
PAST_FIXTURE_MULTIPLIERS = {}

def predict_points_multiple_gameweeks(player, fixture_data, num_gameweeks):
    """
    Attempt to predict total number of points across multiple gameweeks
    """
    result = 0
    for gameweek in range(num_gameweeks):
        result += predict_points(player, fixture_data, gameweek)
    logger.debug('Predicted points for {} {} over {} weeks: {}'.format(player['first_name'], player['second_name'], num_gameweeks, result))                                                                    
    return result


def predict_points(player, fixture_data, gameweekOffset=0):
    """
    Given a player's json object, this function attempts to predict
    how many points a given player will score in the next gameweek.
    """
    expected_points = 0
    if player['element_type'] == 1:
        position = 'GK'
    elif player['element_type'] == 2:
        position = 'DEF'
    elif player['element_type'] == 3:
        position = 'MID'
    elif player['element_type'] == 4:
        position = 'FWD'
    gameweek = constants.NEXT_EVENT['id'] + gameweekOffset
    matches_this_gameweek = [x for x in fixture_data['fixtures'] if x['event'] == gameweek]
    for next_match in matches_this_gameweek:
        opposition_team_id = next_match['team_a'] if next_match[
            'is_home'] else next_match['team_h']
        # Get data for all teams.
        team_data = web_service.get_team_data()
        for team in team_data:
            if team['id'] == opposition_team_id:
                opposition_team_name = team['name']
                break
        try:
            expected_points += neural_network.predict_points(
                '{} {}'.format(player['first_name'], player['second_name']),
                opposition_team_name,
                position,
                next_match['is_home'],
                constants.CURRENT_SEASON,
                next_match['kickoff_time'],
                next_match['event'],
                player['now_cost'],
                next_match['event']
            )
        except Exception as e:
            # if the model fails for some reason, fall back to a naive average
            # this can happen for a few reasons:
            #   - player is unknown (new player for this season)
            #   - team is unknown (new team for this season)
            if player['id'] not in HAS_MODEL_ERROR:
                logger.info('Model failed for {} {}, using naive estimate instead.'.format(player['first_name'], player['second_name']))
                logger.debug(e, exc_info=True)
                HAS_MODEL_ERROR[player['id']] = True
            expected_points += float(player['points_per_game'])

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
    if player['id'] not in INJURY_MULTIPLIERS:
        next_round_chance = player['chance_of_playing_next_round'] / 100 if player[
            'chance_of_playing_next_round'] is not None else 1
        INJURY_MULTIPLIERS[player['id']] = next_round_chance
        logger.debug('Injury multiplier for {} {}: {}'.format(player['first_name'], player['second_name'], next_round_chance))
    else:
        next_round_chance = INJURY_MULTIPLIERS[player['id']]

    return next_round_chance

def calculate_past_fixture_multiplier(player, fixture_data):
    """
    Given a player's json fixture object, calculate a past fixture multiplier for
    the expected points. This is a ratio of total minutes played divided by total
    possible minutes. Prevents players being chosen who barely play but have a very
    high points per game.
    """
    multiplier = 1
    if player['id'] not in PAST_FIXTURE_MULTIPLIERS:
        past_games = fixture_data['history']
        past_season_games = fixture_data['history_past']
        if len(past_games):
            total_games = sum(1 if fixture['minutes'] > 0 else 0 for fixture in past_games)
            multiplier = total_games / len(past_games)
        elif len(past_season_games):
            total_minutes = past_season_games[-1]['minutes']
            multiplier = total_minutes / (constants.TOTAL_GAMES_IN_SEASON * 90)
        PAST_FIXTURE_MULTIPLIERS[player['id']] = multiplier
        logger.debug('Past fixture multiplier for {} {}: {}'.format(player['first_name'], player['second_name'], multiplier))
    else:
        multiplier = PAST_FIXTURE_MULTIPLIERS[player['id']]
    return multiplier
