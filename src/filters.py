import re
from datetime import date

STATE_NAMES = ['Massachusetts', 'Rhode Island', 'Connecticut', 'New Hampshire', 'Vermont', 'Maine']
STATE_CODES = ['MA', 'RI', 'CT', 'NH', 'VT', 'ME']
CITIES = ['Boston', 'Cambridge', 'Somerville', 'Waltham', 'Watertown', 'Burlington',
          'Lexington', 'Newton', 'Quincy', 'Framingham', 'Worcester', 'Lowell',
          'Tewksbury', 'Providence', 'Warwick', 'Cranston', 'Hartford', 'New Haven',
          'Stamford', 'Bridgeport', 'Manchester', 'Nashua', 'Portsmouth', 'Portland', 'Bangor']
OTHER_CODES = 'AL AK AZ AR CA CO DE FL GA HI ID IL IN IA KS KY LA MD MI MN MS MO MT NE NV NJ NM NY NC ND OH OK OR PA SC SD TN TX UT VA WA WV WI WY DC'.split()
OTHER_NAMES = 'Alabama|Alaska|Arizona|Arkansas|California|Colorado|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maryland|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|South Carolina|South Dakota|Tennessee|Texas|Utah|Virginia|Washington|West Virginia|Wisconsin|Wyoming|United Kingdom|Canada|Australia|Ontario|England'
INTERN = re.compile(r'\b(intern(?:ship)?s?|co[ -]?op|summer analyst|summer associate)\b', re.I)


def is_new_england(job):
    location = job if isinstance(job, str) else job.get('location', '')
    # Check each location independently so an out-of-region city cannot borrow a state.
    for part in re.split(r';|\||\n', location):
        if re.search(r'\b(exclud\w*|except|not eligible|not available)\b', part, re.I):
            continue
        if re.search(r'\b(' + '|'.join(STATE_NAMES) + r')\b', part, re.I):
            return True
        if re.search(r'\b(' + '|'.join(STATE_CODES) + r')\b', part):
            return True
        if re.search(r'(?:,\s*|remote\s*[-:]\s*)(' + '|'.join(STATE_CODES) + r')\b', part, re.I):
            return True
        if re.search(r'\b(' + '|'.join(OTHER_CODES) + r')\b', part):
            continue
        if re.search(r'\b(' + OTHER_NAMES + r')\b', part, re.I):
            continue
        if re.search(r'\b(' + '|'.join(CITIES) + r')\b', part, re.I):
            return True
    return False


def is_internship(job):
    if isinstance(job, str):
        return bool(INTERN.search(job))
    if INTERN.search(job['title']):
        return True
    if re.search(r'\b(senior|staff|principal|manager|director)\b', job['title'], re.I):
        return False
    if re.search(r'\b(intern|internship|co[ -]?op)\b', job.get('employment_type', ''), re.I):
        return True
    # Mentoring interns or generic benefits text is not evidence of an internship.
    return bool(re.search(r'\b(?:this|the) (?:position|role|opportunity) is (?:an?|a paid) (?:internship|co-op)\b',
                          job.get('description', ''), re.I))


def is_other_season(title):
    return bool(re.search(r"\b(spring|fall|autumn|winter)\b", title, re.I) and not re.search(r"\bsummer\b", title, re.I))


def season_confidence(job, today=None):
    if is_other_season(job['title']):
        return 'low'
    today = today or date.today()
    text = job['title'] + ' ' + job.get('description', '')
    text = re.sub(r'[-–—]', ' ', text)
    summer = r'(?:summer(?:\s+\w+){0,3}\s+2027|2027\s+summer|(?:may|june)\s*[-–/ ]\s*august\s+2027)'
    if re.search(summer, text, re.I):
        return 'high'
    if re.search(r'\b(?:spring|fall|autumn|winter)\b|\b(?:summer\s+202[0-689]|202[0-689]\s+summer)\b', text, re.I):
        return 'low'
    if re.search(r'\b2027\b', job['title']) and INTERN.search(job['title']) and re.search(r'\bsummer\b', text, re.I):
        return 'medium'
    if re.search(r'\b2027\s+(?:\w+\s+){0,2}intern|\bintern(?:ship)?\s+2027\b', job['title'], re.I):
        return 'medium'
    if re.search(r'\b202[0-689]\b', job['title']):
        return 'low'
    if job.get('season') == 'summer-2027':
        return 'medium'
    # Graduation dates alone are not recruiting-cycle evidence.
    posted = job.get('date_posted') or ''
    if 'summer' in text.lower() and '2027' not in text and '2026-08-01' <= posted[:10] <= '2027-06-30' and date(2026, 8, 1) <= today <= date(2027, 6, 30):
        return 'medium'
    return 'low'
