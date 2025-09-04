from abc import ABC

from crawley.web_requests.clients import WebRequestClient


class WebRequestClientDecorator(WebRequestClient, ABC):
    """Defines a decorator for WebRequestClient objects."""

    def __init__(self, client: WebRequestClient):
        self.client = client

    async def user_agent(self):
        return await self.client.user_agent()

    async def close(self) -> None:
        await self.client.close()
