import unittest
from src.deduplicate import deduplicate, normalize_url


def job(**changes):
    return dict({'company': 'Example Company', 'title': 'Machine Learning Intern', 'location': 'Boston, MA',
                 'url': 'https://example.com/jobs/1', 'source': 'github', 'source_name': 'SimplifyJobs',
                 'source_id': 'github:SimplifyJobs', 'is_simplify': True, 'season_confidence': 'medium'}, **changes)


class DedupTests(unittest.TestCase):
    def test_sources_merge_and_direct_wins(self):
        result = deduplicate([job(), job(url='https://example.com/job/1?utm_source=test', source='greenhouse', source_name='Company', source_id='company:example', is_simplify=False, season_confidence='high')])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['source'], 'greenhouse')
        self.assertTrue(result[0]['in_simplify'])
        self.assertEqual(result[0]['season_confidence'], 'high')
        self.assertEqual(len(result[0]['sources']), 2)

    def test_tracking_and_real_ids(self):
        self.assertEqual(normalize_url('https://example.com/job?id=1&utm_source=x&ref=z'), 'https://example.com/job?id=1')
        self.assertNotEqual(normalize_url('https://example.com/job?id=1'), normalize_url('https://example.com/job?id=2'))
        self.assertEqual(normalize_url('https://jobs.lever.co/x/123/apply'), 'https://jobs.lever.co/x/123')

    def test_distinct_locations(self):
        self.assertEqual(len(deduplicate([job(), job(location='Portland, ME', url='https://example.com/jobs/2')])), 2)
