import unittest
from datetime import datetime, timezone

from src.deduplicate import deduplicate
from src.make_readme import posting_age
from src.storage import reconcile


class PostingAgeTests(unittest.TestCase):
    now = datetime(2026, 9, 13, tzinfo=timezone.utc)

    def test_age_is_from_employer_date(self):
        job = {'date_posted': '2026-09-01', 'first_seen': '2026-09-13'}
        self.assertEqual(posting_age(job, self.now), '2026-09-01 · 12 days ago')
        self.assertEqual(posting_age({'date_posted': '2026-09-12'}, self.now), '2026-09-12 · 1 day ago')
        self.assertEqual(posting_age({'date_posted': '2026-09-13'}, self.now), '2026-09-13 · today')

    def test_missing_dates_do_not_use_tracker_or_source_age(self):
        self.assertEqual(posting_age({'first_seen': '2026-09-01', 'age': '12d'}, self.now), 'Unknown')
        self.assertEqual(posting_age({'date_posted': 'invalid'}, self.now), 'Unknown')
        self.assertIn('future date reported', posting_age({'date_posted': '2026-09-14'}, self.now))

    def test_date_survives_dedup_and_partial_refresh(self):
        job = {'company': 'A', 'title': 'Intern', 'location': 'MA', 'url': 'https://example.com/1',
               'source': 'workday', 'source_id': 'company:a', 'source_name': 'A Careers',
               'source_ids': ['company:a'], 'sources': ['A Careers'], 'first_seen': '2026-09-13',
               'date_posted': '2026-09-01', 'season_confidence': 'high'}
        imported = dict(job, source='github', source_id='github:Other', source_name='Other', date_posted=None)
        self.assertEqual(deduplicate([imported, job])[0]['date_posted'], '2026-09-01')
        self.assertEqual(deduplicate([job, imported])[0]['date_posted'], '2026-09-01')
        self.assertEqual(reconcile([job], [imported], {'github:Other'}, self.now)[0]['date_posted'], '2026-09-01')
