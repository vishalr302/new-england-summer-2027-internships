import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests


class HttpClient:
    def __init__(self, delay=0.8):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'NewEnglandSummer2027Tracker/1.0 (public internship research; low-rate collector)'
        self.delay = delay
        self.lastRequest = 0
        self.robots = {}

    def request(self, method, url, **kwargs):
        if urlsplit(url).scheme != 'https':
            raise ValueError('Only public HTTPS endpoints are supported')
        for attempt in range(3):
            time.sleep(max(0, self.delay - (time.monotonic() - self.lastRequest)))
            self.lastRequest = time.monotonic()
            try:
                response = self.session.request(method, url, timeout=(10, 30), **kwargs)
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 2:
                    raise
                time.sleep(2 ** (attempt + 1))
                continue
            if response.status_code not in (429, 500, 502, 503, 504) or attempt == 2:
                response.raise_for_status()
                return response
            wait = response.headers.get('Retry-After', '')
            if wait and (not wait.isdigit() or int(wait) > 60):
                response.raise_for_status()
            time.sleep(max(2 ** (attempt + 1), int(wait or 0)))
        raise RuntimeError('Request retries exhausted')

    def get_json(self, url, **kwargs):
        return self.request('GET', url, **kwargs).json()

    def page(self, url, redirects=0):
        if redirects > 5:
            raise RuntimeError("Too many career-page redirects")
        parts = urlsplit(url)
        origin = f'{parts.scheme}://{parts.netloc}'
        if origin not in self.robots:
            parser = RobotFileParser()
            try:
                response = self.request('GET', origin + '/robots.txt')
                parser.parse(response.text.splitlines())
            except requests.HTTPError as error:
                if error.response.status_code != 404:
                    raise
                parser.parse([])
            self.robots[origin] = parser
        parser = self.robots[origin]
        if not parser.can_fetch(self.session.headers['User-Agent'], url):
            raise RuntimeError('robots.txt disallows this page')
        crawlDelay = parser.crawl_delay(self.session.headers['User-Agent'])
        if crawlDelay:
            time.sleep(max(0, crawlDelay - (time.monotonic() - self.lastRequest)))
        response = self.request('GET', url, allow_redirects=False)
        if response.is_redirect:
            from urllib.parse import urljoin
            return self.page(urljoin(url, response.headers['Location']), redirects + 1)
        if any(marker in response.text.lower() for marker in ['verify you are human', 'cf-chl-', 'g-recaptcha']):
            raise RuntimeError('Anti-bot challenge detected; no bypass attempted')
        return response.text
