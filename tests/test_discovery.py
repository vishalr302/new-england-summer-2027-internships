import unittest
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory
from pathlib import Path
import json
from src import main as runner

import requests
from src.categories import categorize_job
from src.company_scraper import scrape_web_posting
from src.filters import season_confidence


class DiscoveryTests(unittest.TestCase):
    def test_technical_scope(self):
        self.assertNotEqual(categorize_job({'title': 'Software Engineer Intern'})[0], 'Other')
        self.assertNotEqual(categorize_job({'title': 'Summer Intern', 'description': 'Develop software and machine learning systems.'})[0], 'Other')
        self.assertEqual(categorize_job({'title': 'Human Resources Intern', 'description': 'Support software and machine learning teams.'})[0], 'Other')
        self.assertEqual(categorize_job({'title': 'Summer Finance Intern', 'description': 'Work for a software company.'})[0], 'Other')

    def test_cycle_punctuation(self):
        self.assertEqual(season_confidence({'title': 'Software Developer Summer Internship - 2027'}), 'high')
        self.assertEqual(season_confidence({'title': 'Summer Intern', 'description': 'Internship for the summer of 2027.'}), 'high')
        self.assertEqual(season_confidence({'title': 'Software Intern - Summer 2026'}), 'low')

    def test_title_season_overrides_description(self):
        self.assertEqual(season_confidence({'title': 'Software Co-op - Spring 2027', 'description': 'Other opportunities available for Summer 2027.'}), 'low')
        self.assertEqual(season_confidence({'title': 'Software Co-op - Summer & Fall 2027', 'description': 'Summer 2027 program.'}), 'high')
        self.assertEqual(season_confidence({'title': '2027 Technology, Cyber & Data Internship Program', 'description': 'A ten-week summer experience.'}), 'medium')
        self.assertEqual(season_confidence({'title': 'Technology Intern', 'description': 'Summer experience for students graduating in 2027.'}), 'low')

    def test_closed_page_and_outage_are_different(self):
        config = {'company': 'Example', 'ats': 'generic', 'careers_url': 'https://example.com/job/1'}
        client = Mock()
        for status in (404, 410):
            response = requests.Response()
            response.status_code = status
            client.page.side_effect = requests.HTTPError(response=response)
            self.assertEqual(scrape_web_posting(config, client), [])
        response.status_code = 403
        client.page.side_effect = requests.HTTPError(response=response)
        with self.assertRaises(requests.HTTPError):
            scrape_web_posting(config, client)

    def test_disabled_partial_run_preserves_other_statuses(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            fixtures = {
                'sources.json': {'github_sources': []},
                'companies.json': [{'id': 'disabled', 'company': 'Disabled', 'enabled': False}],
                'source_status.json': [{'source_id': 'company:other', 'name': 'Other', 'status': 'ok'}],
            }
            for name, value in fixtures.items():
                (root / 'data' / name).write_text(json.dumps(value), encoding='utf-8')
            with patch.object(runner, 'ROOT', root), patch('sys.argv', ['tracker', '--company', 'Disabled']):
                self.assertEqual(runner.main(), 1)
            statuses = json.loads((root / 'data/source_status.json').read_text())
            self.assertEqual({row['source_id'] for row in statuses}, {'company:other', 'company:disabled'})
