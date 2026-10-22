"""Get the official USD exchange rate from the National Bank of Ukraine (NBU).

Usage:
    python usd_rate_nbu.py              # prompts for a date, empty input = today
    python usd_rate_nbu.py 20240115     # YYYYMMDD
    python usd_rate_nbu.py 2024-01-15   # YYYY-MM-DD is accepted too
    python usd_rate_nbu.py --currency EUR 20240115
"""

import argparse
import json
import sys
from datetime import date, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

CURRENCY = 'USD'
API_URL = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange'
TIMEOUT_SECONDS = 15

DATE_FORMATS = ('%Y%m%d', '%Y-%m-%d', '%d.%m.%Y')


class RateError(Exception):
    """Raised when the rate cannot be obtained."""


def parse_date(text):
    """Parse user input into a date. Empty input means today."""
    text = (text or '').strip()
    if not text:
        return date.today()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise RateError(
        f'Invalid date "{text}". Use YYYYMMDD, YYYY-MM-DD or DD.MM.YYYY.'
    )


def build_url(by_date, currency=CURRENCY):
    query = urlencode({
        'valcode': currency,
        'date': by_date.strftime('%Y%m%d'),
        'json': '',
    })
    return f'{API_URL}?{query}'


def fetch_rate(by_date, currency=CURRENCY):
    """Return the NBU rate (float) for *currency* on *by_date*."""
    url = build_url(by_date, currency)
    try:
        with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read()
    except HTTPError as exc:
        raise RateError(f'NBU API returned HTTP {exc.code} for {url}') from exc
    except URLError as exc:
        raise RateError(f'Could not reach NBU API: {exc.reason}') from exc
    except OSError as exc:  # e.g. socket timeout
        raise RateError(f'Network error while calling NBU API: {exc}') from exc

    try:
        data = json.loads(payload)
    except ValueError as exc:
        raise RateError('NBU API returned a response that is not valid JSON') from exc

    if not isinstance(data, list) or not data:
        raise RateError(
            f'No {currency} rate found for {by_date.isoformat()} '
            '(the date may be too early or the currency code is unknown).'
        )

    try:
        return float(data[0]['rate'])
    except (KeyError, TypeError, ValueError) as exc:
        raise RateError('NBU API response has an unexpected format') from exc


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Get the official NBU exchange rate for a given date.'
    )
    parser.add_argument(
        'date',
        nargs='?',
        help='date as YYYYMMDD, YYYY-MM-DD or DD.MM.YYYY (default: prompt; empty = today)',
    )
    parser.add_argument(
        '-c', '--currency',
        default=CURRENCY,
        help=f'ISO 4217 currency code (default: {CURRENCY})',
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    currency = args.currency.upper()

    text = args.date
    if text is None:
        try:
            text = input('YYYYMMDD (empty = today): ')
        except EOFError:
            text = ''

    try:
        by_date = parse_date(text)
        nbu_rate = fetch_rate(by_date, currency)
    except RateError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1

    print(nbu_rate)
    return 0


if __name__ == '__main__':
    sys.exit(main())
