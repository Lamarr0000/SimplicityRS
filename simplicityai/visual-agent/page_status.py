"""Known verification pages are blockers, not search-result evidence."""
from urllib.parse import urlsplit


def blocker(url):
    parsed=urlsplit(url)
    host=(parsed.hostname or '').lower()
    if host in {'google.com','www.google.com'} and (parsed.path=='/sorry' or parsed.path.startswith('/sorry/')):
        return {'kind':'human_verification','provider':'Google'}
    return None
