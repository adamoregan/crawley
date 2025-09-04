import asyncio
import logging
from playwright.async_api import (
    Page,
    Browser,
    Error,
    Response as PlaywrightResponse,
    BrowserContext,
)

from crawley.web_requests.clients.client import (
    WebRequestClient,
    FetchResult,
    Response,
    WebResource,
    _is_webpage,
)

logger = logging.getLogger(__name__)


class PagePool(asyncio.Queue):
    """Defines a reusable pool of pages. Useful when a window is not needed for each request."""

    def __init__(self, browser: Browser | BrowserContext, maxsize: int = 0):
        super().__init__(maxsize)
        self._browser = browser

    async def get(self) -> Page:
        """
        Remove and return a Page from the queue.

        If the queue is empty, a Page is created.
        """
        if not self.empty():
            return await super().get()
        # put the Page into the queue so tasks can be properly managed with .task_done()
        self.put_nowait(await self._browser.new_page())
        return self.get_nowait()

    def clear(self):
        """Clears the queue of all items."""
        while not self.empty():
            self.get_nowait()
            self.task_done()


class DynamicRequestClient(WebRequestClient):
    """Defines a WebRequestClient that automates a browser to render dynamic pages and gets web resources."""

    def __init__(
        self, browser: Browser | BrowserContext, max_concurrent_requests: int = 2
    ):
        """
        Creates an instance of DynamicRequestClient.
        :param browser: The browser that is automated to dynamically load webpages.
        :param max_concurrent_requests: The maximum amount of concurrent requests that the browser will make.
        """
        if max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests must be greater than 0")
        self._browser = browser
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._pool = PagePool(browser, max_concurrent_requests)

        self._user_agent = None
        self._agent_lock = asyncio.Lock()

    async def fetch(self, url: str) -> Response:
        async with self._semaphore:
            return await self._get_web_resource(url)

    async def _get_web_resource(self, url: str) -> Response:
        """
        Gets a web resource using an available page from the page pool.
        :param url: The url of the web resource.
        :return: The response from the request for the web resource.
        """
        page = await self._pool.get()
        try:
            response = await page.goto(url)
            fetch_result = FetchResult(response.request.method, url, response.status)
            logger.info(fetch_result)
            return Response(
                fetch_result, await DynamicRequestClient._get_content(response, page)
            )
        except Error as e:
            logger.error(e)
            raise e
        finally:
            self._pool.task_done()
            self._pool.put_nowait(page)

    @staticmethod
    async def _get_content(response: PlaywrightResponse, page: Page) -> WebResource:
        content_type = response.headers.get("content-type")
        if _is_webpage(content_type):
            return WebResource(
                content_type, await DynamicRequestClient._get_content_with_retry(page)
            )
        return WebResource(content_type, await response.body())

    @staticmethod
    async def _get_content_with_retry(page: Page) -> str:
        """Occasionally getting the content of the page fails, so a retry is necessary."""
        for attempt in range(1):
            try:
                return await page.content()
            except Error:
                pass

    async def user_agent(self) -> str:
        async with self._agent_lock:
            if self._user_agent:
                return self._user_agent
            return await self._get_user_agent()

    async def _get_user_agent(self) -> str:
        """Gets the user agent of the browser."""
        async with await self._browser.new_page() as page:
            self._user_agent = await page.evaluate("navigator.userAgent")
            return self._user_agent

    async def close(self) -> None:
        self._pool.clear()
        return await self._browser.close()
