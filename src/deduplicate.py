import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_url(url):
    parts = urlsplit(url.strip())
    host = (parts.hostname or '').lower()
    if host == 'boards.greenhouse.io':
        host = 'job-boards.greenhouse.io'
    query = [(key, value) for key, value in parse_qsl(parts.query)
             if not key.lower().startswith('utm_') and key.lower() not in
             {'ref', 'referral', 'source', 'gh_src', 'lever-source', 'lever-origin', 'iis', 'iisn', 'trackingid'}]
    path = parts.path.rstrip('/')
    if host.endswith('.myworkdayjobs.com'):
        path = re.sub(r'^/[a-z]{2}-[A-Z]{2}/', '/', path)
    if host in ('jobs.lever.co', 'jobs.eu.lever.co') and path.endswith('/apply'):
        path = path[:-6]
    if host == 'jobs.ashbyhq.com' and path.endswith('/application'):
        path = path[:-12]
    return urlunsplit(('https', host, path, urlencode(sorted(query)), ''))


def clean(value):
    return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()


def identity(job):
    company = re.sub(r'\b(?:inc|llc|corporation|corp)\b', '', clean(job['company'])).strip()
    title = clean(job['title'])
    location = clean(job['location'])
    for state, code in [('massachusetts', 'ma'), ('rhode island', 'ri'), ('connecticut', 'ct'),
                        ('new hampshire', 'nh'), ('vermont', 'vt'), ('maine', 'me')]:
        location = re.sub(r'\b' + state + r'\b', code, location)
    return company, title, location


def same_job(left, right):
    return normalize_url(left['url']) == normalize_url(right['url']) or identity(left) == identity(right)


def deduplicate(jobs):
    result = []
    for original in jobs:
        job = dict(original)
        job['url'] = normalize_url(job['url'])
        job['sources'] = job.get('sources', [job['source_name']])
        job['source_ids'] = job.get('source_ids', [job['source_id']])
        job['in_simplify'] = job.get('in_simplify', job.get('is_simplify', False))
        match = next((row for row in result if same_job(row, job)), None)
        if match is None:
            result.append(job)
            continue
        sources = sorted(set(match['sources'] + job['sources']))
        sourceIds = sorted(set(match['source_ids'] + job['source_ids']))
        inSimplify = match['in_simplify'] or job['in_simplify']
        confidence = 'high' if 'high' in (match['season_confidence'], job['season_confidence']) else 'medium'
        posted = match.get('date_posted') or job.get('date_posted')
        if match['source'] == 'github' and job['source'] != 'github':
            posted = job.get('date_posted') or posted
            match.update(job)
        match['date_posted'] = posted
        match.update(sources=sources, source_ids=sourceIds, in_simplify=inSimplify, season_confidence=confidence)
    return result
