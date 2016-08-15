"""
The main program.
    1. Log in to fantasy premier league.
    2. Get the current squad.
    3. Calculate the best squad possible for next week.
    4. Update the squad on fantasy premier league.
    5. Calculate the best possible starting lineup for next week.
    6. Update the starting lineup on fantasy premier league.
"""
import sys
import auth_service
import linear_solver

# Login
USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
auth_service.login(USERNAME, PASSWORD)

# Get the current squad
CURRENT_SQUAD = auth_service.get_transfers_squad()

# Calculate the new squad
new_squad = linear_solver.select_squad(CURRENT_SQUAD)

# TODO make transfers to update the squad

# Calculate the new starting lineup
new_starting = linear_solver.select_starting(new_squad)
