from crawley import AsyncContextManager
from crawley.crawling import SitemapCache
from crawley.web_requests import WebRequestClient, StaticRequestClient


class BaseCrawler(AsyncContextManager):
    """Defines a base structure that all crawlers need."""

    def __init__(self, request_client: WebRequestClient = None):
        self._request_client = request_client or StaticRequestClient()
        self.sitemap_cache = SitemapCache()

    async def close(self) -> None:
        await self._request_client.close()
