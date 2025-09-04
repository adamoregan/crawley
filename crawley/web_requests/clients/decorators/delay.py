from aiolimiter import AsyncLimiter

from crawley.web_requests import WebRequestClient, Response
from crawley.web_requests.clients.decorators.decorator import WebRequestClientDecorator


class DelayedRequestClient(WebRequestClientDecorator):
    """Defines a WebRequestClient with a delay between requests."""

    def __init__(self, client: WebRequestClient, request_delay: float):
        """
        Creates an instance of DelayedRequestClient.
        :param client: The client that is used to make the requests.
        :param request_delay: The desired delay between requests,
        """
        super().__init__(client)
        self._request_limiter = AsyncLimiter(1, request_delay)

    async def fetch(self, url: str) -> Response:
        async with self._request_limiter:
            return await self.client.fetch(url)
