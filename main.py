"""
The main program.
    1. Log in to fantasy.premierleague.com.
    2. Get the current squad.
    3. Calculate the best squad possible for next week.
    4. Update the squad on fantasy.premierleague.com.
    5. Calculate the best possible starting lineup for next week.
    6. Update the starting lineup on fantasy.premierleague.com.
"""
import sys
import linear_solver
import web_service

# Login
USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
web_service.login(USERNAME, PASSWORD)

# Get the current squad
CURRENT_SQUAD = web_service.get_transfers_squad()

# Calculate the new squad
NEW_SQUAD = linear_solver.select_squad(CURRENT_SQUAD)

# make transfers to update the squad on fantasy.premierleague.com
TRANSFER_OBJECT = web_service.calculate_transfers(
    CURRENT_SQUAD['picks'], NEW_SQUAD)
web_service.make_transfers(TRANSFER_OBJECT)

# Calculate the new starting lineup
NEW_STARTING = linear_solver.select_starting(NEW_SQUAD)

# update the starting lineup on fantasy.premierleague.com
web_service.set_starting_lineup(NEW_STARTING)
