from bs4 import BeautifulSoup
from .filters import is_internship, is_new_england


def plain(text):
    return BeautifulSoup('<div>' + (text or '') + '</div>', 'html.parser').get_text(' ', strip=True)


def location_text(location):
    if isinstance(location, str):
        return location
    location = location or {}
    return location.get('location_str') or ', '.join(str(location[key]) for key in
        ('city', 'region', 'state', 'country') if location.get(key))


def normalized(company, title, location, url, description='', date_posted=None, employment_type=''):
    if not title or not url or not url.startswith('https://'):
        raise ValueError('A public job is missing its title or HTTPS application URL')
    return {'company': company['company'], 'title': title, 'location': location,
            'url': url, 'description': plain(description), 'date_posted': (date_posted or '')[:10] or None,
            'employment_type': employment_type or '', 'source': company['ats'],
            'source_name': company['company'] + ' Careers', 'is_simplify': False}


def get_greenhouse_jobs(company, client):
    data = client.get_json(f"https://boards-api.greenhouse.io/v1/boards/{company['identifier']}/jobs", params={'content': 'true'})
    return [normalized(company, row['title'], row['location']['name'], row['absolute_url'], row.get('content', ''))
            for row in data['jobs']]


def get_lever_jobs(company, client):
    host = 'api.eu.lever.co' if company.get('region') == 'eu' else 'api.lever.co'
    jobs, offset = [], 0
    while True:
        rows = client.get_json(f"https://{host}/v0/postings/{company['identifier']}", params={'mode': 'json', 'skip': offset, 'limit': 100})
        if not isinstance(rows, list):
            raise ValueError('Unexpected Lever response')
        for row in rows:
            categories = row.get('categories', {})
            locations = categories.get('allLocations') or [categories.get('location', '')]
            description = row.get('descriptionPlain', '') + ' ' + ' '.join(part.get('content', '') for part in row.get('lists', [])) + ' ' + row.get('additionalPlain', '')
            jobs.append(normalized(company, row['text'], '; '.join(locations), row['hostedUrl'], description, employment_type=categories.get('commitment', '')))
        if len(rows) < 100:
            return jobs
        offset += len(rows)
        if offset >= 10000:
            raise ValueError('Lever pagination limit reached; refusing partial results')


def get_ashby_jobs(company, client):
    data = client.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{company['identifier']}")
    jobs = []
    for row in data['jobs']:
        if row.get('isListed') is False:
            continue
        locations = [row.get('location', '')] + [item.get('location', '') for item in row.get('secondaryLocations', [])]
        jobs.append(normalized(company, row['title'], '; '.join(filter(None, locations)), row['jobUrl'],
                               row.get('descriptionPlain', ''), row.get('publishedAt'), row.get('employmentType', '')))
    return jobs


def get_smartrecruiters_jobs(company, client):
    base = f"https://api.smartrecruiters.com/v1/companies/{company['identifier']}/postings"
    jobs, offset = [], 0
    while True:
        data = client.get_json(base, params={'limit': 100, 'offset': offset})
        rows = data['content']
        for row in rows:
            description = ''
            location = location_text(row.get('location'))
            employmentType = row.get('typeOfEmployment', {}).get('label', '')
            if is_new_england(location) and is_internship({'title': row['name'], 'employment_type': employmentType}):
                detail = client.get_json(base + '/' + row['id'])
                description = ' '.join(section.get('text', '') for section in detail.get('jobAd', {}).get('sections', {}).values())
            jobs.append(normalized(company, row['name'], location,
                                   f"https://jobs.smartrecruiters.com/{company['identifier']}/{row['id']}",
                                   description, row.get('releasedDate'), employmentType))
        offset += len(rows)
        if offset >= data['totalFound']:
            return jobs
        if not rows or offset >= 20000:
            raise ValueError('Incomplete SmartRecruiters pagination')


def get_workable_jobs(company, client):
    data = client.get_json(f"https://www.workable.com/api/accounts/{company['identifier']}", params={'details': 'true'})
    return [normalized(company, row['title'], location_text(row.get('location')), row.get('url') or row['application_url'],
                       row.get('description', ''), row.get('published_on'), row.get('employment_type', '')) for row in data['jobs']]


def get_recruitee_jobs(company, client):
    data = client.get_json(f"https://{company['identifier']}.recruitee.com/api/offers/")
    return [normalized(company, row['title'], location_text(row.get('location')), row['careers_url'],
                       row.get('description', '') + ' ' + row.get('requirements', ''), row.get('published_at'), row.get('employment_type_code', ''))
            for row in data['offers']]


COLLECTORS = {'greenhouse': get_greenhouse_jobs, 'lever': get_lever_jobs, 'ashby': get_ashby_jobs,
              'smartrecruiters': get_smartrecruiters_jobs, 'workable': get_workable_jobs, 'recruitee': get_recruitee_jobs}
