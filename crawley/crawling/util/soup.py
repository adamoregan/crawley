from urllib.parse import urlparse
from bs4 import BeautifulSoup

from crawley.crawling.util.url import remove_fragment, get_absolute

try:
    from lxml import etree

    _PARSER = "lxml"
except ImportError:
    _PARSER = "html.parser"


def get_urls(content: str, parser: str = _PARSER) -> list[str]:
    """
    Parses html/xml content for urls.
    :param content: The html/xml content to parse.
    :param parser: The parser for the content. 'lxml' by default, 'html.parser' if etree module is not available.
    :return: The urls in the content
    """
    soup = BeautifulSoup(content, parser)
    return [a.get("href") for a in soup.find_all("a")]


def get_absolute_urls(base_url: str, content: str) -> set[str]:
    """Gets absolute urls (with no fragments) from webpage content."""
    return set(
        [remove_fragment(url) for url in get_absolute(base_url, get_urls(content))]
    )


def get_internal_urls(base_url: str, content: str) -> set[str]:
    """Gets absolute, internal urls (with no fragments) from webpage content."""
    base_netloc, urls = urlparse(base_url).netloc, set()
    for url in get_absolute(base_url, get_urls(content)):
        url = remove_fragment(url)
        if urlparse(url).netloc == base_netloc:
            urls.add(url)
    return urls
