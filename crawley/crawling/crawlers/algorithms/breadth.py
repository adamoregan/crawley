import asyncio
from collections import deque
from collections.abc import Callable
from enum import Enum
from typing import Iterable

from crawley.crawling import SitemapCache
from crawley.web_requests import WebRequestClient, Response
from crawley.crawling.util import (
    get_absolute_urls,
    get_internal_urls,
)


def is_parsable(response: Response) -> bool:
    """Checks if a response can be parsed."""
    return not isinstance(response, Exception) and response.is_parsable


def dequeue_all(q: deque) -> list:
    """Gets all the items in a deque (FIFO)."""
    return [q.popleft() for _ in range(len(q))]


class BreadthCrawlType(Enum):
    """Defines breadth crawl types."""

    URLS = "urls"
    PAGES = "pages"


class BreadthCrawl:
    """Defines a breadth-first crawling algorithm that gets webpage urls."""

    def __init__(
        self,
        request_client: WebRequestClient,
        visited_urls: set[str] = None,
        sitemap_cache: SitemapCache = None,
    ):
        """
        Creates an instance of BreadthCrawl.
        :param request_client: The client that is used to make requests for webpages.
        :param visited_urls: The urls that have already been visited. These urls will not be revisited.
        :param sitemap_cache: The cache of domain sitemaps.
        """
        self._request_client = request_client
        self.visited_urls = visited_urls or set()
        self.sitemap_cache = sitemap_cache or SitemapCache()

    async def execute(
        self,
        seed_urls: Iterable[str],
        limit: int = None,
        target: BreadthCrawlType = BreadthCrawlType.URLS,
        internal_only: bool = False,
    ) -> set[str]:
        """
        Crawls webpages to discover urls.
        :param seed_urls: The urls that the crawl starts at.
        :param limit: The maximum amount of targets to crawl/discover.
        :param target: The intended unit to measure the limit of the crawling.
        :param internal_only: If only webpages that are in the same domain as seed_urls should be discovered.
        :return: The discovered urls.
        """
        urls_to_scrape, visited_urls = deque(seed_urls), set()
        url_filter = get_internal_urls if internal_only else get_absolute_urls
        try:
            if target == BreadthCrawlType.PAGES:
                return await self._crawl_pages(
                    urls_to_scrape, visited_urls, limit, url_filter
                )
            return await self._crawl_urls(
                urls_to_scrape, visited_urls, limit, url_filter
            )
        except asyncio.CancelledError:
            return visited_urls

    def _track_new_url(self, url, urls_to_scrape: deque[str], visited_urls: set):
        """
        Tracks a newly discovered url. Ensures it will not be revisited.
        :param url: The url to track.
        :param urls_to_scrape: The queue used to track the urls that need to be scraped.
        :param visited_urls: The urls that have already been discovered.
        """
        self.visited_urls.add(url)
        urls_to_scrape.append(url)
        visited_urls.add(url)

    def _get_sitemap_urls(
        self, url: str, urls_to_scrape: deque[str], visited_urls: set, url_limit: int
    ) -> set[str]:
        """
        Gets the urls of a domain's sitemap.
        :param url: Any url belonging to a certain domain.
        :param urls_to_scrape: The queue used to track the urls that need to be scraped.
        :param visited_urls: The urls that have already been discovered.
        :param url_limit: The maximum amount of urls to get from the sitemap.
        :return: An updated visited_urls with sitemap urls.
        """
        for sitemap_url in self.sitemap_cache.get_urls(
            self.sitemap_cache[url], url_limit
        ):
            if sitemap_url in self.visited_urls:
                continue
            self._track_new_url(sitemap_url, urls_to_scrape, visited_urls)
            if url_limit and len(visited_urls) == url_limit:
                return visited_urls

    async def _crawl_urls(
        self,
        urls_to_scrape: deque[str],
        visited_urls: set,
        limit: int,
        url_filter: Callable[[str, str | bytes], set[str]],
    ) -> set[str]:
        """Crawls until a certain amount of urls are discovered, if specified."""
        while urls_to_scrape:
            urls = dequeue_all(urls_to_scrape)
            for url in urls:
                if self._get_sitemap_urls(url, urls_to_scrape, visited_urls, limit):
                    return visited_urls
            fetch_generator = self._request_client.fetch_multiple(urls)
            async for response in fetch_generator:
                if not is_parsable(response):
                    continue
                for url in url_filter(
                    response.fetch.url, response.web_resource.content
                ):
                    if url in self.visited_urls:
                        continue
                    self._track_new_url(url, urls_to_scrape, visited_urls)
                    if limit and len(visited_urls) == limit:
                        await fetch_generator.aclose()
                        return visited_urls
        return visited_urls

    async def _crawl_pages(
        self, urls_to_scrape: deque[str], visited_urls: set, limit: int, url_filter
    ) -> set[str]:
        """Crawls until a certain amount of pages has been crawled, if specified."""
        pages_crawled = 0
        while urls_to_scrape:
            fetch_generator = self._request_client.fetch_multiple(
                dequeue_all(urls_to_scrape)
            )
            async for response in fetch_generator:
                if not is_parsable(response):
                    continue
                for url in url_filter(
                    response.fetch.url, response.web_resource.content
                ):
                    if url in self.visited_urls:
                        continue
                    self._track_new_url(url, urls_to_scrape, visited_urls)
                pages_crawled += 1
                if limit and pages_crawled == limit:
                    await fetch_generator.aclose()
                    return visited_urls
        return visited_urls
