import argparse
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from .categories import categorize
from .deduplicate import deduplicate
from .filters import is_internship, is_new_england, season_confidence
from .github_sources import get_github_jobs
from .http_client import HttpClient
from .make_readme import make_readme
from .storage import export_jobs, read_json, reconcile, write_json

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description='Refresh New England Summer 2027 internships')
    parser.add_argument('--github-only', action='store_true', help='Run Phase 1 sources only')
    parser.add_argument('--company', help='Run only matching company names (partial run preserves other history)')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    client = HttpClient()
    now = datetime.now(timezone.utc)
    previous = read_json(ROOT / 'data/jobs.json', [])
    sources = read_json(ROOT / 'data/sources.json', {})['github_sources']
    companies = read_json(ROOT / 'data/companies.json', [])
    tasks = []
    if not args.company:
        tasks += [('github:' + source['name'], source['name'], source, get_github_jobs) for source in sources]
    if not args.github_only:
        from .company_scraper import scrape_company
        tasks += [('company:' + company.get('id', company['company']), company['company'], company, scrape_company)
                  for company in companies if not args.company or args.company.lower() in company['company'].lower()]
    current, statuses, successful = [], [], set()
    for sourceId, name, config, collector in tasks:
        status = {'source_id': sourceId, 'name': name, 'checked_at': now.date().isoformat()}
        if not config.get('enabled', True):
            status.update(status='disabled', error=config.get('notes', 'Not configured'))
            statuses.append(status)
            continue
        logging.info('Checking %s', name)
        try:
            jobs = collector(config, client)
            regional = [job for job in jobs if is_new_england(job)]
            internships = [job for job in regional if is_internship(job)]
            matches = []
            for job in internships:
                job['season_confidence'] = season_confidence(job, now.date())
                if job['season_confidence'] == 'low':
                    continue
                job['category'], job['tags'] = categorize(job['title'])
                job['source_id'] = sourceId
                job['simplify_comparison'] = 'pending'
                matches.append(job)
            current.extend(matches)
            successful.add(sourceId)
            status.update(status='ok', checked=len(jobs), regional=len(regional), internships=len(internships), matching=len(matches))
            logging.info('%s: %s checked, %s regional, %s internships, %s Summer 2027', name, len(jobs), len(regional), len(internships), len(matches))
        except Exception as error:
            status.update(status='error', error=re.sub(r'0x[0-9A-Fa-f]+', '0x…', f'{type(error).__name__}: {error}'))
            logging.warning('%s: %s', name, status['error'])
        statuses.append(status)
    if not successful:
        write_json(ROOT / 'data/source_status.json', statuses)
        logging.error('No source completed. Preserving listings and README.')
        return 1
    current = deduplicate(current)
    for job in current:
        job['simplify_comparison'] = ('matched' if job['in_simplify'] else
                                      'no_exact_match' if 'github:SimplifyJobs' in successful else 'unavailable')
        job.pop('description', None)
        job.pop('employment_type', None)
    jobs = reconcile(previous, current, successful, now)
    export_jobs(ROOT, jobs)
    oldStatuses = read_json(ROOT / 'data/source_status.json', [])
    checkedIds = {row['source_id'] for row in statuses}
    statuses += [row for row in oldStatuses if row['source_id'] not in checkedIds]
    write_json(ROOT / 'data/source_status.json', statuses)
    make_readme(ROOT, jobs, statuses, now)
    logging.info('Active: %s; newly discovered: %s; errors: %s', sum(job['active'] for job in jobs),
                 sum(job['first_seen_at'] == now.isoformat() for job in jobs), sum(row['status'] == 'error' for row in statuses))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
