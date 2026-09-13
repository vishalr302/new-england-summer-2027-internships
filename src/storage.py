import csv
import json
from datetime import datetime, timezone

from .deduplicate import same_job

CSV_FIELDS = ['company', 'title', 'location', 'category', 'url', 'source', 'first_seen',
              'last_seen', 'date_posted', 'season_confidence', 'in_simplify', 'active']


def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def write_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def reconcile(previous, current, successful, now=None):
    now = now or datetime.now(timezone.utc)
    today = now.date().isoformat()
    remaining = list(previous)
    result = []
    for job in current:
        matches = [old for old in remaining if same_job(old, job)]
        for old in matches:
            remaining.remove(old)
        direct = next((old for old in matches if old.get('source') != 'github' and old.get('source')), None)
        if direct and job.get('source') == 'github' and direct.get('source_id') not in successful:
            for key in ('url', 'source', 'source_name', 'source_id'):
                if key in direct:
                    job[key] = direct[key]
        job['first_seen'] = min([old['first_seen'] for old in matches] or [today])
        job['first_seen_at'] = min([old.get('first_seen_at', old['first_seen'] + 'T00:00:00+00:00') for old in matches] or [now.isoformat()])
        job['last_seen'] = today
        job['missing_runs'] = 0
        job['active'] = True
        job['date_posted'] = job.get('date_posted') or next((old['date_posted'] for old in matches if old.get('date_posted')), None)
        job['source_ids'] = sorted(set(job['source_ids'] + [sid for old in matches for sid in old.get('source_ids', [])]))
        job['sources'] = sorted(set(job['sources'] + [name for old in matches for name in old.get('sources', [])]))
        if any(old.get('in_simplify') for old in matches) and 'github:SimplifyJobs' not in successful:
            job['in_simplify'] = True
        result.append(job)
    for old in remaining:
        old = dict(old)
        # Every known source must succeed before absence counts. Outages freeze history.
        sourceIds = set(old.get('source_ids', []))
        if sourceIds and sourceIds <= successful:
            old['missing_runs'] = old.get('missing_runs', 0) + 1
            if old['missing_runs'] >= 3:
                old['active'] = False
        result.append(old)
    return sorted(result, key=lambda job: (job['first_seen'], job['company'], job['title']), reverse=True)


def export_jobs(root, jobs):
    write_json(root / 'data/jobs.json', jobs)
    with (root / 'data/jobs.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction='ignore')
        writer.writeheader()
        for job in jobs:
            # Keep spreadsheet programs from interpreting external titles as formulas.
            row = {key: ("'" + value if isinstance(value, str) and value.startswith(('=', '+', '-', '@')) else value)
                   for key, value in job.items()}
            writer.writerow(row)
