import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

import requests
from src.deduplicate import normalize_url
from src.filters import is_new_england, season_confidence
from src.http_client import HttpClient
from src.make_readme import is_new, safe


class RegressionTests(unittest.TestCase):
    def test_ambiguous_cities_and_excluded_remote(self):
        self.assertFalse(is_new_england('Manchester, Tennessee'))
        self.assertFalse(is_new_england('Remote US excluding MA'))
        self.assertTrue(is_new_england('Boston, ma'))
        self.assertTrue(is_new_england('Portland, OR; Boston, MA'))
        self.assertFalse(is_new_england('Contact me'))

    def test_old_intern_year_cannot_borrow_source_season(self):
        self.assertEqual(season_confidence({'title': '2026 Data Intern', 'season': 'summer-2027'}), 'low')
        self.assertEqual(season_confidence({'title': 'Summer Intern', 'date_posted': '2026-09-01'}, date(2027, 9, 1)), 'low')

    def test_workday_locale_duplicates(self):
        self.assertEqual(normalize_url('https://example.wd1.myworkdayjobs.com/en-US/External/job/1?ref=test'),
                         normalize_url('https://example.wd1.myworkdayjobs.com/External/job/1'))

    def test_real_rolling_day(self):
        now = datetime(2026, 9, 13, 1, tzinfo=timezone.utc)
        job = {'first_seen': '2026-09-12', 'first_seen_at': (now - timedelta(hours=23)).isoformat()}
        self.assertTrue(is_new(job, now))
        self.assertFalse(is_new(job, now + timedelta(hours=2)))
        self.assertNotIn('|', safe('Role | <script>'))
        self.assertNotIn('<script>', safe('Role | <script>'))

    @patch('src.http_client.time.sleep')
    def test_connection_retry(self, sleep):
        client = HttpClient(delay=0)
        response = Mock(status_code=200)
        client.session.request = Mock(side_effect=[requests.Timeout(), response])
        self.assertIs(client.request('GET', 'https://example.com/jobs'), response)
        self.assertEqual(client.session.request.call_count, 2)

    @patch('src.http_client.time.sleep')
    def test_no_retry_for_forbidden(self, sleep):
        client = HttpClient(delay=0)
        response = Mock(status_code=403)
        response.raise_for_status.side_effect = requests.HTTPError('Forbidden')
        client.session.request = Mock(return_value=response)
        with self.assertRaises(requests.HTTPError):
            client.request('GET', 'https://example.com/jobs')
        self.assertEqual(client.session.request.call_count, 1)
