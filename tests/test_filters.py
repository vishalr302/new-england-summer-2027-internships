import unittest
from datetime import date
from src.filters import is_new_england, is_internship, season_confidence


class FilterTests(unittest.TestCase):
    def test_geography(self):
        for location in ['Boston, MA', 'Cambridge, Massachusetts', 'Providence, RI', 'Hartford, CT', 'Portland, ME', 'Burlington, VT', 'Manchester, NH', 'Greater Boston Area', 'Boston Metro', 'Cambridge/Boston', 'Massachusetts, United States', 'Remote - Massachusetts', 'Hybrid - Boston']:
            with self.subTest(location=location):
                self.assertTrue(is_new_england(location))
        for location in ['New York, NY', 'San Francisco, CA', 'Austin, TX', 'Seattle, WA', 'Portland, OR', 'Burlington, Ontario, Canada', 'Manchester, United Kingdom', 'Remote - US', 'Contact me']:
            with self.subTest(location=location):
                self.assertFalse(is_new_england(location))

    def test_internship(self):
        for title in ['Machine Learning Intern', 'Data Science Internship', 'Software Engineering Co-op', 'Summer Analyst']:
            self.assertTrue(is_internship(title))
        for title in ['Senior Software Engineer', 'Staff Data Scientist', 'Engineering Manager', 'Internal Auditor']:
            self.assertFalse(is_internship(title))
        self.assertFalse(is_internship({'title': 'Software Engineer', 'description': 'You will mentor interns'}))
        self.assertTrue(is_internship({'title': 'Software Engineer', 'employment_type': 'Intern'}))

    def test_season(self):
        for title in ['Summer 2027 Intern', '2027 Summer Analyst', 'Summer Internship 2027', 'May-August 2027 Intern']:
            self.assertEqual(season_confidence({'title': title}), 'high')
        for title in ['Summer 2026 Intern', 'Spring 2027 Intern', 'Fall 2027 Intern', 'Winter 2027 Intern']:
            self.assertEqual(season_confidence({'title': title, 'season': 'summer-2027'}), 'low')
        self.assertEqual(season_confidence({'title': 'Summer 2027 and Fall 2027 Intern'}), 'high')
        self.assertEqual(season_confidence({'title': 'Intern', 'description': 'Graduating in 2027'}), 'low')
        self.assertEqual(season_confidence({'title': 'Intern', 'season': 'summer-2027'}), 'medium')
        self.assertEqual(season_confidence({'title': 'Summer Intern', 'date_posted': '2026-09-01'}, date(2026, 9, 13)), 'medium')
