import asyncio
import time
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from crawley.web_requests.clients.decorators.delay import DelayedRequestClient


class TestDelayedRequestClient(IsolatedAsyncioTestCase):
    async def test_fetch(self):
        delay = 0.05
        delay_client = DelayedRequestClient(AsyncMock(), delay)

        start_time = time.time()
        await asyncio.gather(delay_client.fetch(""), delay_client.fetch(""))
        self.assertGreaterEqual(time.time() - start_time, delay)
