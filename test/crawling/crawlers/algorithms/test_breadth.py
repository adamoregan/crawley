from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch, MagicMock

from crawley.crawling.crawlers.algorithms.breadth import BreadthCrawl, BreadthCrawlType
from crawley.web_requests import Response, FetchResult, WebResource


async def mock_fetch_generator(urls):
    yield Response(
        FetchResult("", "", 200), WebResource("", "content") if urls[0] else None
    )


class TestBreadthCrawl(IsolatedAsyncioTestCase):
    @patch(
        "crawley.crawling.crawlers.algorithms.breadth.get_absolute_urls"
    )  # mock where used, not where defined
    async def test_crawl(self, absolute_urls: MagicMock):
        client = AsyncMock()
        client.fetch_multiple = mock_fetch_generator

        with self.subTest("Should return an empty set if no urls are found"):
            self.assertFalse(
                await BreadthCrawl(client).execute(
                    [""], 1, target=BreadthCrawlType.PAGES
                )
            )

        with self.subTest("Should get the urls in each page"):
            absolute_urls.return_value = ["1", "2"]
            urls = await BreadthCrawl(client).execute(
                ["url"], 3, target=BreadthCrawlType.PAGES
            )
            self.assertEqual(len(urls), len(absolute_urls.return_value))

        with self.subTest("Should not revisit the same url"):
            absolute_urls.return_value = ["2", "url"]
            urls = await BreadthCrawl(client).execute(
                ["url"], 3, target=BreadthCrawlType.PAGES
            )
            self.assertEqual(len(urls), len(absolute_urls.return_value))

        with self.subTest("Should not revisit a url already found in a previous crawl"):
            crawl = BreadthCrawl(client)
            absolute_urls.return_value = ["2", "url"]
            await crawl.execute(["url"], 3, target=BreadthCrawlType.PAGES)
            self.assertFalse(
                await crawl.execute(["url"], 3, target=BreadthCrawlType.PAGES)
            )
