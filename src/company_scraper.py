import json
import requests
from datetime import date
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from .ats import COLLECTORS, normalized
from .workday import get_workday_jobs


def jsonld_jobs(data):
    if isinstance(data, list):
        for value in data:
            yield from jsonld_jobs(value)
    elif isinstance(data, dict):
        types = data.get('@type', [])
        if 'JobPosting' in ([types] if isinstance(types, str) else types):
            yield data
        for key in ('@graph', 'itemListElement', 'item'):
            if key in data:
                yield from jsonld_jobs(data[key])


def parse_jobposting(row, company):
    locations = row.get('jobLocation', [])
    if isinstance(locations, dict):
        locations = [locations]
    names = []
    for place in locations:
        address = place.get('address', {})
        if isinstance(address, str):
            names.append(address)
        else:
            names.append(', '.join(address[key] for key in ('addressLocality', 'addressRegion', 'addressCountry') if isinstance(address.get(key), str)))
    eligible = row.get('applicantLocationRequirements', [])
    if isinstance(eligible, dict):
        eligible = [eligible]
    names += [place.get('name', '') for place in eligible]
    kind = row.get('employmentType', '')
    if isinstance(kind, list):
        kind = ' '.join(kind)
    return normalized(company, row['title'], '; '.join(names), row.get('url') or company['careers_url'],
                      row.get('description', ''), row.get('datePosted'), kind)


def parse_generic_page(company, soup):
    postings = []
    for script in soup.find_all('script', type='application/ld+json'):
        postings.extend(jsonld_jobs(json.loads(script.string or script.get_text())))
    if postings:
        return [parse_jobposting(row, company) for row in postings
                if not row.get('validThrough') or row['validThrough'][:10] >= date.today().isoformat()]
    selectors = company.get('selectors')
    if not selectors:
        raise ValueError('No JobPosting JSON-LD; configure HTML selectors or a public ATS board')
    cards = soup.select(selectors['job'])
    if not cards:
        raise ValueError('Configured HTML cards not found; page may require JavaScript')
    jobs = []
    for card in cards:
        title = card.select_one(selectors['title'])
        link = card.select_one(selectors['link'])
        location = card.select_one(selectors['location'])
        if title is None or link is None or location is None:
            raise ValueError('Incomplete HTML job card; refusing partial results')
        jobs.append(normalized(company, title.get_text(' ', strip=True), location.get_text(' ', strip=True),
                               urljoin(company['careers_url'], link['href']), card.get_text(' ', strip=True)))
    return jobs



def get_generic_jobs(company, client):
    url = company['careers_url']
    seenPages, jobs = set(), []
    while True:
        if url in seenPages or len(seenPages) >= 30:
            raise ValueError('Repeated page or pagination cap; refusing partial HTML results')
        seenPages.add(url)
        soup = BeautifulSoup(client.page(url), 'html.parser')
        jobs.extend(parse_generic_page(dict(company, careers_url=url), soup))
        selector = company.get('selectors', {}).get('next')
        nextPage = soup.select_one(selector) if selector else None
        if not nextPage:
            return jobs
        nextUrl = urljoin(url, nextPage['href'])
        if urlsplit(nextUrl).netloc != urlsplit(url).netloc:
            raise ValueError('Pagination unexpectedly left the employer board')
        url = nextUrl


def scrape_company(company, client):
    collectors = {**COLLECTORS, 'generic': get_generic_jobs, 'workday': get_workday_jobs}
    if company['ats'] not in collectors:
        raise ValueError('Unsupported ATS: ' + company['ats'])
    return collectors[company['ats']](company, client)


def scrape_web_posting(posting, client):
    try:
        return get_generic_jobs(posting, client)
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code in (404, 410):
            return []
        raise
