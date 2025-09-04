import logging
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock
from aiohttp import ClientSession, ClientError, ClientResponseError

from crawley.web_requests.clients.client import WEBPAGE_CONTENT_TYPE
from crawley.web_requests.clients.static import StaticRequestClient, logger


def set_attributes(obj: object, dictionary: dict):
    """Sets the attributes of an object to the key values of a dictionary."""
    for key, value in dictionary.items():
        setattr(obj, key, value)


class TestStaticRequestClient(IsolatedAsyncioTestCase):
    async def assert_fetch_error(self):
        """Asserts that an invalid fetch raises the correct error and is logged."""
        session = Mock()
        session.get.side_effect = ClientError()
        with self.assertRaises(ClientError):
            with self.assertLogs(logger.name, logging.ERROR):
                await StaticRequestClient(session).fetch("")

    async def assert_fetch_http_error(self):
        """Asserts that an unsuccessful fetch raises the correct error and is logged."""
        session = Mock()
        session.get.side_effect = ClientResponseError(Mock(), ())
        with self.assertLogs(logger.name, logging.WARNING):
            res = await StaticRequestClient(session).fetch("")
        self.assertIsNone(res.web_resource)

    async def test_fetch(self):
        """Tests that webpages and files can be fetched with proper error handling."""
        webpage_response = {
            "content_type": WEBPAGE_CONTENT_TYPE,
            "text": AsyncMock(return_value="content"),
        }
        file_response = {
            "content_type": "application/pdf",
            "read": AsyncMock(return_value=b"content"),
        }

        session, response = Mock(), AsyncMock()
        response.__aenter__.return_value = response
        session.get.return_value = response
        client = StaticRequestClient(session)

        with self.subTest("Fetching webpage"):
            set_attributes(response, webpage_response)
            with self.assertLogs(logger.name, logging.INFO):
                res = await client.fetch("")
            webpage_response["text"].assert_called()
            self.assertIsInstance(
                res.web_resource.content, str, "Expected to fetch webpage as string"
            )

        with self.subTest("Fetching file"):
            set_attributes(response, file_response)
            with self.assertLogs(logger.name, logging.INFO):
                res = await client.fetch("")
            file_response["read"].assert_called()
            self.assertIsInstance(
                res.web_resource.content, bytes, "Expected to fetch file as binary"
            )

        with self.subTest("Fetching errors are handled"):
            await self.assert_fetch_error()

        with self.subTest("HTTP error codes are handled"):
            await self.assert_fetch_http_error()

    async def test_user_agent(self):
        """Tests the setting of the user agent for requests."""
        with self.subTest("No User Agent by default"):
            async with StaticRequestClient() as client:
                self.assertIsNone(await client.user_agent())
        with self.subTest("User Agent specified by ClientSession"):
            user_agent = "Client Session Specified User Agent"
            async with StaticRequestClient(
                ClientSession(headers={"User-Agent": user_agent})
            ) as client:
                self.assertEqual(await client.user_agent(), user_agent)

    async def test_close(self):
        """Tests that closing the request client also closes the session."""
        session = Mock()
        session.close = AsyncMock()
        await StaticRequestClient(session).close()
        session.close.assert_called_once()
