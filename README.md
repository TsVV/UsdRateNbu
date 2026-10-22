# UsdRateNbu

Get the official USD exchange rate from the National Bank of Ukraine (NBU) on a specific date.

Uses only the Python standard library (Python 3.8+), no extra packages required.

## Usage

```
python usd_rate_nbu.py                  # prompts for a date; empty input = today
python usd_rate_nbu.py 20240115         # YYYYMMDD
python usd_rate_nbu.py 2024-01-15       # YYYY-MM-DD
python usd_rate_nbu.py 15.01.2024       # DD.MM.YYYY
python usd_rate_nbu.py -c EUR 20240115  # another currency
```

The rate is printed to stdout. On failure (bad date, network error, no rate for
that date) an error message is printed to stderr and the exit code is 1.

## Windows helper scripts (`cmd/`)

- `01_create_venv.cmd` – create a virtual environment in `venv/`
- `02_run.cmd` – run the script with the venv Python (arguments are passed through)
- `03_test.cmd` – run the unit tests

## Tests

```
python -m unittest discover -s tests -t .
```
