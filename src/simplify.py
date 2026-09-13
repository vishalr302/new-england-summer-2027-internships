from .github_sources import get_github_jobs


def get_simplify_jobs(source, client):
    return get_github_jobs({**source, 'is_simplify': True}, client)
