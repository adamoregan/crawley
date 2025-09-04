from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock

from crawley.crawling.crawlers.base import BaseCrawler


class TestBaseCrawler(IsolatedAsyncioTestCase):
    async def test_close(self):
        request_client, close = Mock(), AsyncMock()
        request_client.close = close
        crawler = BaseCrawler(request_client)
        await crawler.close()
        close.assert_called_once()
