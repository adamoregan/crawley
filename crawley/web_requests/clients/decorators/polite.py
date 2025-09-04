from typing import Dict
from urllib.robotparser import RobotFileParser
from aiolimiter import AsyncLimiter

from crawley.crawling.util import get_robots, get_homepage
from crawley.web_requests import WebRequestClient, Response
from crawley.web_requests.clients.decorators.decorator import WebRequestClientDecorator


def _init_parser(url: str) -> RobotFileParser:
    parser = RobotFileParser(url)
    parser.set_url(get_robots(url))
    parser.read()
    return parser


class DisallowedRequest(Exception):
    def __init__(self, url: str, user_agent: str):
        self.url = url
        self.user_agent = user_agent

    def __str__(self):
        return f"The request to {self.url} with User-Agent '{self.user_agent}' is not allowed"


class PoliteRequestClient(WebRequestClientDecorator):
    """Defines a request client that enforces robots.txt delays and permissions for each domain independently."""

    def __init__(self, client: WebRequestClient):
        """
        Creates an instance of PoliteRequestClient.
        :param client: The client that is used to make the requests.
        """
        super().__init__(client)
        self._limiters: Dict[str, AsyncLimiter] = {}

    async def fetch(self, url: str) -> Response:
        robots_parser = _init_parser(url)
        user_agent = await self.user_agent()

        if not robots_parser.can_fetch(user_agent, url):
            raise DisallowedRequest(url, user_agent)

        request_limiter = self._limiters.get(get_homepage(url))
        if request_limiter:
            async with request_limiter:
                return await self.client.fetch(url)

        crawl_delay = robots_parser.crawl_delay(user_agent)
        if not crawl_delay:
            return await self.client.fetch(url)

        request_limiter = AsyncLimiter(1, float(crawl_delay))
        self._limiters[get_homepage(url)] = request_limiter
        async with request_limiter:
            return await self.client.fetch(url)

    async def user_agent(self) -> str:
        return await super().user_agent() or "*"
