from urllib.parse import urlparse, urljoin


def is_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_homepage(url: str) -> str:
    """Gets the homepage of a website."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def get_robots(url: str) -> str:
    """Gets the robots.txt file of a website."""
    return f"{get_homepage(url)}/robots.txt"


def get_absolute(origin_url: str, relative_urls: list[str]) -> list[str]:
    absolute_urls = []
    for url in relative_urls:
        url = urljoin(origin_url, url)
        if is_url(url):
            absolute_urls.append(url)
    return absolute_urls


def remove_fragment(url: str) -> str:
    return url.split("#")[0]
