import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup


def cell_text(cell):
    for br in cell.find_all('br'):
        br.replace_with('; ')
    for summary in cell.find_all('summary'):
        summary.decompose()
    return re.sub(r'\s*;\s*', '; ', cell.get_text(' ', strip=True))


def parse_readme(text, source):
    text = re.sub(r'</br\s*>', '<br>', text, flags=re.I)
    soup = BeautifulSoup('<div>' + text + '</div>', 'html.parser')
    rows = []
    for table in soup.find_all('table'):
        for row in table.find_all('tr'):
            cells = row.find_all('td', recursive=False)
            if len(cells) >= 4:
                rows.append(cells)
    # Also accept conventional Markdown tables, including linked titles.
    for line in text.splitlines():
        if not line.strip().startswith('|'):
            continue
        parts = re.split(r'(?<!\\)\|', line.strip().strip('|'))
        if len(parts) < 4 or parts[0].strip().lower() in ('company', 'name') or re.fullmatch(r'[\s:|-]+', line):
            continue
        cells = []
        for part in parts:
            part = re.sub(r'!?\[([^\]]*)\]\((https?://[^ )]+)(?:[^)]*)\)', r'<a href="\2">\1</a>', part)
            cells.append(BeautifulSoup('<td>' + part + '</td>', 'html.parser').td)
        rows.append(cells)
    if not rows:
        raise ValueError('No recognizable listing rows; source may have changed format')
    jobs = []
    company = ''
    for cells in rows:
        name = cell_text(cells[0]).strip('* ')
        if name and name not in ('↳', '↪', '→', '"', '“', '”'):
            company = name.replace('🔥', '').strip()
        if '🔒' in ''.join(str(cell) for cell in cells):
            continue
        links = cells[3].find_all('a', href=True) or cells[1].find_all('a', href=True)
        urls = [urljoin(source['url'], link['href']) for link in links]
        urls = [url for url in urls if urlsplit(url).scheme == 'https']
        if not urls or not company:
            continue
        url = next((url for url in urls if urlsplit(url).hostname != 'simplify.jobs'), urls[0])
        jobs.append({'company': company, 'title': cell_text(cells[1]), 'location': cell_text(cells[2]),
                     'url': url, 'source': 'github', 'source_name': source['name'],
                     'description': '', 'season': source.get('season'),
                     'age': cell_text(cells[4]) if len(cells) > 4 else None,
                     'is_simplify': source.get('is_simplify', False)})
    return jobs


def get_github_jobs(source, client):
    return parse_readme(client.request('GET', source['url']).text, source)
