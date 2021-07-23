# fantasy_pl
An attempt to write a fantasy football bot in a week.

## Requirements
- Python 3
- Python modules `pulp` and `requests`:
  - `pip3 install pulp`
  - `pip3 install requests`

## Installation

```bash
git clone https://github.com/ashharrison90/fantasy_pl.git
```

## Running

```bash
python3 main.py <FANTASY_PL_USERNAME> <FANTASY_PL_PASSWORD>
```

To automatically make the transfers and set the starting lineup, set the `--apply` flag:
```bash
python3 main.py <FANTASY_PL_USERNAME> <FANTASY_PL_PASSWORD> --apply
```

To ignore the current squad when calculating a new squad (useful when starting the season/using a wildcard), set the `--ignore-squad` flag:
```bash
python3 main.py <FANTASY_PL_USERNAME> <FANTASY_PL_PASSWORD> --ignore-squad
```

For help:
```bash
python3 main.py --help
```
