import json
import unittest
from src.ats import (get_greenhouse_jobs, get_lever_jobs, get_ashby_jobs,
                     get_smartrecruiters_jobs, get_workable_jobs, get_recruitee_jobs)
from src.company_scraper import get_generic_jobs
from src.workday import get_workday_jobs


class FakeClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def get_json(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)

    def request(self, method, url, **kwargs):
        value = self.get_json(url, **kwargs)
        return type('Response', (), {'json': lambda self: value})()

    def page(self, url):
        return self.responses.pop(0)


def company(ats):
    return {'company': 'Example', 'ats': ats, 'identifier': 'example', 'tenant': 'example',
            'site': 'External', 'careers_url': 'https://example.wd1.myworkdayjobs.com/External'}


class CollectorTests(unittest.TestCase):
    def test_greenhouse(self):
        client = FakeClient({'jobs': [{'title': 'Summer 2027 Intern', 'location': {'name': 'Boston, MA'}, 'absolute_url': 'https://example.com/1', 'content': '<p>Data science</p>'}]})
        jobs = get_greenhouse_jobs(company('greenhouse'), client)
        self.assertEqual(jobs[0]['description'], 'Data science')
        self.assertEqual(jobs[0]['source'], 'greenhouse')

    def test_lever_pagination(self):
        row = {'text': 'Intern', 'categories': {'allLocations': ['Boston, MA', 'NYC'], 'commitment': 'Intern'}, 'hostedUrl': 'https://example.com/1'}
        client = FakeClient([row] * 100, [row])
        jobs = get_lever_jobs(company('lever'), client)
        self.assertEqual(len(jobs), 101)
        self.assertEqual(client.calls[1][1]['params']['skip'], 100)
        self.assertEqual(jobs[0]['location'], 'Boston, MA; NYC')

    def test_ashby_locations(self):
        row = {'title': 'Intern', 'location': 'NYC', 'secondaryLocations': [{'location': 'Boston, MA'}], 'jobUrl': 'https://example.com/1', 'publishedAt': '2026-09-01T00:00:00Z', 'employmentType': 'Intern'}
        jobs = get_ashby_jobs(company('ashby'), FakeClient({'jobs': [row, dict(row, isListed=False)]}))
        self.assertEqual(len(jobs), 1)
        self.assertIn('Boston, MA', jobs[0]['location'])
        self.assertEqual(jobs[0]['date_posted'], '2026-09-01')

    def test_smartrecruiters_details(self):
        row = {'id': '123', 'name': 'Data Intern', 'location': {'city': 'Boston', 'region': 'MA'}, 'typeOfEmployment': {'label': 'Intern'}}
        client = FakeClient({'content': [row], 'totalFound': 1}, {'jobAd': {'sections': {'jobDescription': {'text': 'Summer 2027'}}}})
        jobs = get_smartrecruiters_jobs(company('smartrecruiters'), client)
        self.assertEqual(jobs[0]['description'], 'Summer 2027')

    def test_workable(self):
        row = {'title': 'Intern', 'location': {'city': 'Portland', 'region': 'ME'}, 'url': 'https://example.com/1'}
        self.assertEqual(get_workable_jobs(company('workable'), FakeClient({'jobs': [row]}))[0]['location'], 'Portland, ME')

    def test_recruitee(self):
        row = {'title': 'Intern', 'location': 'Cambridge, MA', 'careers_url': 'https://example.com/1'}
        self.assertEqual(get_recruitee_jobs(company('recruitee'), FakeClient({'offers': [row]}))[0]['title'], 'Intern')

    def test_workday_details_and_partial_failure(self):
        row = {'title': 'Intern', 'locationsText': '2 Locations', 'externalPath': '/job/1'}
        client = FakeClient({'jobPostings': [row], 'total': 1}, {'jobPostingInfo': {'location': 'Boston, MA', 'jobDescription': 'Summer 2027'}})
        self.assertEqual(get_workday_jobs(company('workday'), client)[0]['location'], 'Boston, MA')
        with self.assertRaises(ValueError):
            get_workday_jobs(company('workday'), FakeClient({'jobPostings': [], 'total': 2}))

    def test_generic_jsonld_and_remote(self):
        row = {'@type': 'JobPosting', 'title': 'Summer 2027 Intern', 'url': 'https://example.com/1', 'applicantLocationRequirements': {'@type': 'State', 'name': 'Massachusetts'}}
        html = '<script type="application/ld+json">' + json.dumps({'@graph': [row]}) + '</script>'
        self.assertEqual(get_generic_jobs(company('generic'), FakeClient(html))[0]['location'], 'Massachusetts')

    def test_generic_selectors_and_no_data(self):
        config = dict(company('generic'), selectors={'job': '.job', 'title': 'h2', 'link': 'a', 'location': 'span'})
        html = '<div class="job"><h2>Summer 2027 Intern</h2><a href="/job/1">Apply</a><span>Boston, MA</span></div>'
        self.assertEqual(len(get_generic_jobs(config, FakeClient(html))), 1)
        with self.assertRaises(ValueError):
            get_generic_jobs(config, FakeClient('<p>No data</p>'))

    def test_workday_total_only_present_on_first_page(self):
        def row(number):
            return {'title': 'Engineer', 'locationsText': 'New York, NY', 'externalPath': '/job/' + str(number)}
        client = FakeClient({'jobPostings': [row(1)], 'total': 3},
                            {'jobPostings': [row(2)], 'total': 0},
                            {'jobPostings': [row(3)], 'total': 0})
        self.assertEqual(len(get_workday_jobs(company('workday'), client)), 3)

    def test_generic_pagination(self):
        config = dict(company('generic'), selectors={'job': '.job', 'title': 'h2', 'link': 'a', 'location': 'span', 'next': 'a.next'})
        card = '<div class="job"><h2>Summer 2027 Intern</h2><a href="/job/1">Apply</a><span>Boston, MA</span></div>'
        first = card + '<a class="next" href="?page=2">Next</a>'
        second = card.replace('/job/1', '/job/2')
        self.assertEqual(len(get_generic_jobs(config, FakeClient(first, second))), 2)
        with self.assertRaises(ValueError):
            get_generic_jobs(config, FakeClient(first, first))
