import logging
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock
from playwright.async_api import Response, Error

from crawley.web_requests.clients.client import WEBPAGE_CONTENT_TYPE
from crawley.web_requests.clients.dynamic import DynamicRequestClient, logger


class TestDynamicRequestClient(IsolatedAsyncioTestCase):
    async def assert_fetch_error(self):
        """Asserts that an invalid fetch raises the correct error and is logged."""
        browser, page = AsyncMock(), Mock()
        page.goto.side_effect = Error("")
        browser.new_page.return_value = page
        with self.assertRaises(Error):
            with self.assertLogs(logger.name, logging.ERROR):
                await DynamicRequestClient(browser).fetch("")

    async def test_fetch(self):
        browser, page, response = AsyncMock(), AsyncMock(), AsyncMock(spec=Response)
        page.goto.return_value = response
        browser.new_page.return_value = page

        client = DynamicRequestClient(browser)

        with self.subTest("Fetching webpage"):
            response.headers.get.return_value = WEBPAGE_CONTENT_TYPE
            page.content.return_value = "content"
            with self.assertLogs(logger.name, logging.INFO):
                res = await client.fetch("")
            self.assertIsInstance(
                res.web_resource.content, str, "Expected to fetch webpage as string"
            )

        with self.subTest("Fetching file"):
            response.headers.get.return_value = "application/pdf"
            response.body.return_value = b""
            with self.assertLogs(logger.name, logging.INFO):
                res = await client.fetch("")
            self.assertIsInstance(
                res.web_resource.content, bytes, "Expected to fetch file as binary"
            )

        with self.subTest("Fetching errors are handled"):
            await self.assert_fetch_error()

    async def test_user_agent(self):
        browser, page = AsyncMock(), AsyncMock()
        page.__aenter__.return_value, browser.new_page.return_value = page, page
        page.evaluate = AsyncMock(return_value="user_agent")
        self.assertEqual(
            await DynamicRequestClient(browser).user_agent(), page.evaluate.return_value
        )

    async def test_close(self):
        browser = Mock()
        browser.close = AsyncMock()
        await DynamicRequestClient(browser).close()
        browser.close.assert_called_once()
