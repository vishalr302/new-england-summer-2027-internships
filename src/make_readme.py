from datetime import date, datetime, timezone
from html import escape
from urllib.parse import quote

from .categories import CATEGORY_RULES
from .filters import is_new_england


def safe(text):
    return escape(str(text)).replace('|', '&#124;').replace('\n', ' ').replace('[', '&#91;').replace(']', '&#93;')


def is_new(job, now):
    first = datetime.fromisoformat(job.get('first_seen_at', job['first_seen'] + 'T00:00:00+00:00'))
    return 0 <= (now - first).total_seconds() < 86400



def posting_age(job, now):
    try:
        posted = date.fromisoformat(job.get('date_posted') or '')
    except (TypeError, ValueError):
        return 'Unknown'
    days = (now.date() - posted).days
    if days < 0:
        age = 'future date reported'
    elif days == 0:
        age = 'today'
    else:
        age = f"{days} {'day' if days == 1 else 'days'} ago"
    return f'{posted.isoformat()} · {age}'


def make_readme(root, jobs, status, now=None):
    now = now or datetime.now(timezone.utc)
    active = [job for job in jobs if job['active'] and job['season_confidence'] in ('high', 'medium')]
    direct = [job for job in active if job['source'] != 'github' and not job['in_simplify'] and job.get('simplify_comparison') == 'no_exact_match']
    lines = ['# New England Summer 2027 Internships', '',
             'Automatically collected student opportunities across **Massachusetts · Rhode Island · Connecticut · New Hampshire · Vermont · Maine**.', '',
             f'Last updated: **{now.date().isoformat()} (UTC)** · Scheduled every six hours', '',
             f'**Active internships: {len(active)}** · **Added in last 24 hours: {sum(is_new(job, now) for job in active)}** · **Direct company finds: {len(direct)}**', '',
             '[Download CSV](data/jobs.csv) · [Full JSON & history](data/jobs.json) · [Source health](data/source_status.json) · [Contribute](CONTRIBUTING.md)', '',
             '> 🆕 Found in the last 24 hours. 🔎 Direct find = collected from a company board with no current confirmed Simplify match; matching is conservative, not proof of an omission. ◇ = inferred Summer 2027 cycle.', '',
             'Listings are observations, not guarantees of availability. Confirm dates, eligibility, location, and application status with the employer.', '']
    dated = sum(posting_age(job, now) != 'Unknown' for job in active)
    lines += ['## Posting dates', '',
              f'Employer posting dates are available for **{dated} of {len(active)} active listings**. The **Posted / age** column shows the employer-reported date and its age as of the last update (UTC). **First tracked** is when this tracker discovered the role.', '',
              'Unknown means the employer posting date is unavailable. We do not substitute the age of an entry on Simplify or another list. Employers may repost or reset dates, so these dates may not reflect the first-ever advertisement.', '']
    if not active:
        lines += ['No matching active listings were confirmed on this run.', '']
    for category in [*CATEGORY_RULES, 'Other']:
        rows = [job for job in active if job['category'] == category]
        if not rows:
            continue
        lines += ['## ' + category, '', '| Company | Role | Location | Source | Posted / age | First tracked |', '| --- | --- | --- | --- | --- | --- |']
        for job in sorted(rows, key=lambda row: row.get('first_seen_at', row['first_seen']), reverse=True):
            marker = '🆕 ' if is_new(job, now) else ''
            marker += '◇ ' if job['season_confidence'] == 'medium' else ''
            source = '🔎 Direct find' if job in direct else safe(', '.join(job['sources']))
            location = '; '.join(part.strip().split(' ~ ')[0] for part in job['location'].split(';') if is_new_england(part))
            url = quote(job['url'], safe=':/?=&%#@+;,~!$*\'-._')
            lines.append(f"| {safe(job['company'])} | {marker}[{safe(job['title'])}]({url}) | {safe(location)} | {source} | {posting_age(job, now)} | {job['first_seen']} |")
        lines.append('')
    lines += ['## Source health', '', f"{sum(row['status'] == 'ok' for row in status)} sources completed · {sum(row['status'] == 'error' for row in status)} coverage gaps · {sum(row['status'] == 'disabled' for row in status)} shared-board aliases", '', '<details>', '<summary>View all monitored sources</summary>', '', '| Source | Status | Checked | Matching |', '| --- | --- | --- | --- |']
    for row in status:
        lines.append(f"| {safe(row['name'])} | {safe(row['status'])} | {row.get('checked', '—')} | {row.get('matching', '—')} |")
    lines += ['', '</details>', '', 'A successful source can return zero matching internships. Failed, incomplete, or disabled sources do not count as job disappearances. Error details are in the source-health JSON.', '',
              (root / 'docs/readme_footer.md').read_text(encoding='utf-8')]
    (root / 'README.md').write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
