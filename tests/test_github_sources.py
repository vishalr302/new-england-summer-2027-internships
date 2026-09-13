import unittest
from src.github_sources import parse_readme


class GithubTests(unittest.TestCase):
    source = {'name': 'Test', 'url': 'https://example.com/readme', 'season': 'summer-2027'}

    def test_html_continuation_and_closed(self):
        html = '<table><tr><td>A</td><td>Summer Intern</td><td>Boston, MA<br>NYC</td><td><a href="https://example.com/1">Apply</a></td></tr><tr><td>↳</td><td>Data Intern</td><td>MA</td><td><a href="https://example.com/2">Apply</a></td></tr><tr><td>B</td><td>Intern</td><td>MA</td><td>🔒</td></tr></table>'
        jobs = parse_readme(html, self.source)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[1]['company'], 'A')
        self.assertEqual(jobs[0]['location'], 'Boston, MA; NYC')

    def test_markdown(self):
        text = '| Company | Role | Location | Application |\n| --- | --- | --- | --- |\n| A | Intern | Boston, MA | [Apply](https://example.com/1) |'
        self.assertEqual(len(parse_readme(text, self.source)), 1)

    def test_changed_format_fails(self):
        with self.assertRaises(ValueError):
            parse_readme('Service unavailable', self.source)
