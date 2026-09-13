from urllib.parse import urlsplit
from .ats import normalized
from .filters import is_internship, is_new_england


def get_workday_jobs(company, client):
    origin = 'https://' + urlsplit(company['careers_url']).netloc
    tenant, site = company['tenant'], company['site']
    base = f'{origin}/wday/cxs/{tenant}/{site}'
    jobs, seenPaths, offset = [], set(), 0
    total = None
    while True:
        data = client.request('POST', base + '/jobs', json={
            'appliedFacets': company.get('facets', {}), 'limit': 20, 'offset': offset, 'searchText': company.get('search_text', 'intern')}).json()
        if total is None:
            total = data['total']
        rows = data['jobPostings']
        for row in rows:
            path = row['externalPath']
            if path in seenPaths:
                raise ValueError('Workday repeated a page; refusing incomplete results')
            seenPaths.add(path)
            location = row.get('locationsText', '')
            title = row['title']
            description, posted = '', None
            if is_internship(title) and (is_new_england(location) or 'location' in location.lower()):
                detail = client.get_json(base + path)['jobPostingInfo']
                description = detail.get('jobDescription', '')
                location = '; '.join(filter(None, [detail.get('location', location), *detail.get('additionalLocations', [])]))
                posted = detail.get('startDate')
            jobs.append(normalized(company, title, location, f'{origin}/en-US/{site}{path}', description, posted))
        offset += len(rows)
        if offset >= total:
            return jobs
        if not rows or offset >= company.get('max_jobs', 3000):
            raise ValueError('Incomplete Workday pagination')
