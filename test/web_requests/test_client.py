import asyncio
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch, AsyncMock

from crawley.web_requests.clients.client import WebRequestClient


async def mock_fetch(fetch_time: str):
    return fetch_time if not fetch_time else await asyncio.sleep(float(fetch_time))


class TestWebRequestClient(IsolatedAsyncioTestCase):
    @patch.multiple(WebRequestClient, __abstractmethods__=set())
    @patch("crawley.web_requests.client.cancel_tasks")
    async def test_fetch_multiple(self, cancel_tasks: AsyncMock):
        client = WebRequestClient()
        with self.subTest(
            "Should cancel uncompleted fetches when the generator is exited"
        ):
            fetch_generator = client.fetch_multiple(["10", ""])
            async for _ in fetch_generator:
                await fetch_generator.aclose()
                break
            cancel_tasks.assert_called()
        with self.subTest("Should yield responses as soon as they finish"):
            fetch = AsyncMock(side_effect=mock_fetch)
            client.fetch = fetch
            async for response in client.fetch_multiple(["10", ""]):
                self.assertEqual(response, "")
                break
        with self.subTest(
            "Exceptions should be yielded instead of crashing the generator"
        ):
            client.fetch = AsyncMock(side_effect=Exception)
            responses = []
            async for response in client.fetch_multiple(["", ""]):
                responses.append(response)
            self.assertEqual(len(responses), 2)
            for response in responses:
                self.assertIsInstance(response, Exception)
            cancel_tasks.assert_called()
