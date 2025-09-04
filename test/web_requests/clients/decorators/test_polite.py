import asyncio
import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock, patch

from crawley.web_requests.clients.decorators.polite import (
    PoliteRequestClient,
    DisallowedRequest,
)

MOCK_USER_AGENT = "Mozilla"


class TestPoliteRequestClient(IsolatedAsyncioTestCase):
    @patch("crawley.web_requests.clients.decorators.polite._init_parser")
    async def test_fetch(self, init_parser):
        client = AsyncMock()
        client.user_agent.return_value = MOCK_USER_AGENT
        robots_parser = Mock()
        init_parser.return_value = robots_parser

        polite_client = PoliteRequestClient(client)

        with self.subTest("Should disallow requests based on robots file"):
            robots_parser.can_fetch.return_value = False
            with self.assertRaises(DisallowedRequest):
                await polite_client.fetch("")

        with self.subTest("Should restrict requests based on robots file"):
            delay = 0.05
            with self.subTest("Should not delay requests without specified delay"):
                robots_parser.can_fetch.return_value = True
                robots_parser.crawl_delay.return_value = None
                start_time = time.time()
                await polite_client.fetch("")
                self.assertLess(time.time() - start_time, delay)

            with self.subTest("Should delay requests with specified delay"):
                robots_parser.can_fetch.return_value = True
                robots_parser.crawl_delay.return_value = delay
                start_time = time.time()
                await asyncio.gather(polite_client.fetch(""), polite_client.fetch(""))
                self.assertGreaterEqual(time.time() - start_time, delay)

        await client.close()

    async def test_user_agent(self):
        client = AsyncMock()
        polite_client = PoliteRequestClient(client)
        with self.subTest("User Agent should never be 'None'"):
            client.user_agent.return_value = None
            self.assertIsNotNone(await polite_client.user_agent())

        with self.subTest("Specified User Agent should be returned"):
            client.user_agent.return_value = MOCK_USER_AGENT
            self.assertEqual(await polite_client.user_agent(), MOCK_USER_AGENT)
