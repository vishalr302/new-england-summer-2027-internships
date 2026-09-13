import unittest
from datetime import datetime, timezone
from src.storage import reconcile


class StorageTests(unittest.TestCase):
    def test_outages_and_three_misses(self):
        old = {'company': 'A', 'title': 'Intern', 'location': 'Boston, MA', 'url': 'https://example.com/1',
               'first_seen': '2026-09-01', 'last_seen': '2026-09-01', 'source_ids': ['a', 'b'], 'active': True}
        rows = reconcile([old], [], {'a'})
        self.assertTrue(rows[0]['active'])
        self.assertNotIn('missing_runs', rows[0])
        for _ in range(3):
            rows = reconcile(rows, [], {'a', 'b'})
        self.assertFalse(rows[0]['active'])
        self.assertEqual(rows[0]['last_seen'], '2026-09-01')

    def test_reactivation_keeps_first_seen(self):
        current = {'company': 'A', 'title': 'Intern', 'location': 'Boston, MA', 'url': 'https://example.com/1', 'source_ids': ['a'], 'sources': ['A']}
        old = dict(current, first_seen='2026-09-01', active=False)
        result = reconcile([old], [current], {'a'}, datetime(2026, 9, 13, tzinfo=timezone.utc))[0]
        self.assertTrue(result['active'])
        self.assertEqual(result['first_seen'], '2026-09-01')
        self.assertEqual(result['missing_runs'], 0)

    def test_direct_url_survives_partial_run(self):
        old = {'company': 'A', 'title': 'Intern', 'location': 'MA', 'url': 'https://example.com/1',
               'source': 'greenhouse', 'source_id': 'company:a', 'source_name': 'A Careers',
               'source_ids': ['company:a'], 'sources': ['A Careers'], 'first_seen': '2026-09-01'}
        current = dict(old, source='github', source_id='github:Other', source_name='Other',
                       source_ids=['github:Other'], sources=['Other'])
        result = reconcile([old], [current], {'github:Other'})[0]
        self.assertEqual(result['source'], 'greenhouse')
        self.assertEqual(result['source_ids'], ['company:a', 'github:Other'])
