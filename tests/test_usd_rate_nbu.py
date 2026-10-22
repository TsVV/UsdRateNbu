import io
import json
import unittest
from datetime import date
from unittest import mock
from urllib.error import HTTPError, URLError

import usd_rate_nbu as m


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def fake_urlopen(payload):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return mock.patch.object(m, 'urlopen', return_value=FakeResponse(body))


SAMPLE = [{
    'r030': 840, 'txt': 'Долар США', 'rate': 37.9821,
    'cc': 'USD', 'exchangedate': '15.01.2024',
}]


class ParseDateTests(unittest.TestCase):
    def test_compact_format(self):
        self.assertEqual(m.parse_date('20240115'), date(2024, 1, 15))

    def test_iso_format(self):
        self.assertEqual(m.parse_date('2024-01-15'), date(2024, 1, 15))

    def test_dotted_format(self):
        self.assertEqual(m.parse_date('15.01.2024'), date(2024, 1, 15))

    def test_empty_means_today(self):
        self.assertEqual(m.parse_date(''), date.today())
        self.assertEqual(m.parse_date(None), date.today())

    def test_invalid(self):
        with self.assertRaises(m.RateError):
            m.parse_date('2024-13-45')
        with self.assertRaises(m.RateError):
            m.parse_date('yesterday')


class BuildUrlTests(unittest.TestCase):
    def test_url(self):
        url = m.build_url(date(2024, 1, 15))
        self.assertTrue(url.startswith(m.API_URL + '?'))
        self.assertIn('valcode=USD', url)
        self.assertIn('date=20240115', url)
        self.assertIn('json', url)

    def test_currency(self):
        self.assertIn('valcode=EUR', m.build_url(date(2024, 1, 15), 'EUR'))


class FetchRateTests(unittest.TestCase):
    def test_success(self):
        with fake_urlopen(SAMPLE):
            self.assertEqual(m.fetch_rate(date(2024, 1, 15)), 37.9821)

    def test_empty_list(self):
        with fake_urlopen([]):
            with self.assertRaises(m.RateError):
                m.fetch_rate(date(1990, 1, 1))

    def test_invalid_json(self):
        with fake_urlopen(b'<html>oops</html>'):
            with self.assertRaises(m.RateError):
                m.fetch_rate(date(2024, 1, 15))

    def test_missing_rate_key(self):
        with fake_urlopen([{'cc': 'USD'}]):
            with self.assertRaises(m.RateError):
                m.fetch_rate(date(2024, 1, 15))

    def test_http_error(self):
        err = HTTPError('url', 503, 'Unavailable', {}, None)
        with mock.patch.object(m, 'urlopen', side_effect=err):
            with self.assertRaises(m.RateError):
                m.fetch_rate(date(2024, 1, 15))

    def test_url_error(self):
        with mock.patch.object(m, 'urlopen', side_effect=URLError('dns')):
            with self.assertRaises(m.RateError):
                m.fetch_rate(date(2024, 1, 15))


class MainTests(unittest.TestCase):
    def test_main_with_arg(self):
        out = io.StringIO()
        with fake_urlopen(SAMPLE), mock.patch('sys.stdout', out):
            self.assertEqual(m.main(['20240115']), 0)
        self.assertEqual(out.getvalue().strip(), '37.9821')

    def test_main_prompts_when_no_arg(self):
        out = io.StringIO()
        with fake_urlopen(SAMPLE), mock.patch('sys.stdout', out), \
                mock.patch('builtins.input', return_value='20240115'):
            self.assertEqual(m.main([]), 0)
        self.assertEqual(out.getvalue().strip(), '37.9821')

    def test_main_invalid_date(self):
        err = io.StringIO()
        with mock.patch('sys.stderr', err):
            self.assertEqual(m.main(['bad-date']), 1)
        self.assertIn('Invalid date', err.getvalue())


if __name__ == '__main__':
    unittest.main()
