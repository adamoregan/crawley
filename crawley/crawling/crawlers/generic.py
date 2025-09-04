import asyncio
from typing import Iterable, Coroutine, Any

from crawley.crawling.crawlers import BaseCrawler
from crawley.crawling.crawlers.algorithms.breadth import BreadthCrawlType, BreadthCrawl
from crawley.web_requests import WebRequestClient


async def run_timeout(
    coro: Coroutine,
    timeout: float = None,
) -> Any:
    """
    Runs a coroutine for a specified amount of hours.
    :param coro: The coroutine to cancel after a certain duration.
    :param timeout: The duration of the function (in hours). It either finishes, or is cancelled if
    the specified duration has been reached.
    :return: The result of the function or function cancellation.
    """
    task = asyncio.create_task(coro)
    try:
        result = await asyncio.wait_for(task, timeout * 3600 if timeout else timeout)
        return result
    except asyncio.TimeoutError:
        return await task


class Crawler(BaseCrawler):
    """Defines a crawler that discovers urls."""

    def __init__(self, request_client: WebRequestClient = None):
        """
        Creates an instance of Crawler.
        :param request_client: The client that is used to request web resources.
        """
        super().__init__(request_client)
        self.visited_urls = set()

    async def crawl(
        self,
        seed_urls: Iterable[str],
        limit: int = None,
        timeout: float = None,
        target: BreadthCrawlType = BreadthCrawlType.URLS,
        internal_only: bool = True,
    ):
        """
        Crawls webpages.
        :param seed_urls: The urls to start crawling at.
        :param limit: The maximum amount of targets to crawl/discover.
        :param timeout: The duration of the crawl (in hours).
        :param target: The intended unit to measure the limit of the crawling.
        :param internal_only: If only webpages that are in the same domain as seed_urls should be discovered.
        :return: The discovered urls.
        """
        return await run_timeout(
            BreadthCrawl(
                self._request_client, self.visited_urls, self.sitemap_cache
            ).execute(seed_urls, limit, target, internal_only),
            timeout,
        )
