import asyncio
from abc import abstractmethod
from asyncio import Task
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Iterable

from crawley import AsyncContextManager

WEBPAGE_CONTENT_TYPE = "text/html"


@dataclass
class FetchResult:
    """The result of an HTTP request."""

    method: str
    url: str
    status: int

    def __str__(self):
        return f"{self.method} request to {self.url} returned {self.status}"


@dataclass
class WebResource:
    """The metadata and content of a web resource."""

    content_type: str
    content: str | bytes


@dataclass
class Response:
    """The result of an HTTP request and its associated data."""

    fetch: FetchResult
    web_resource: WebResource | None

    @property
    def is_parsable(self):
        """Checks if the response has parsable content."""
        return bool(self.web_resource and self.web_resource.content)


def _is_webpage(content_type: str) -> bool:
    return content_type == WEBPAGE_CONTENT_TYPE


async def cancel_tasks(tasks: Iterable[Task]):
    """Cancels tasks and handles returned exceptions."""
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


class WebRequestClient(AsyncContextManager):
    """Defines a client that makes requests to web resources."""

    @abstractmethod
    async def fetch(self, url: str) -> Response:
        """
        Fetches the content of a web resource.
        :param url: The url of the web resource to fetch content from.
        :return: The result of fetching content from the url.
        """
        pass

    async def fetch_multiple(self, urls: Iterable[str]) -> AsyncGenerator[Response]:
        """
        Fetches the content of multiple web resources.

        When the generator is closed with .aclose(), fetches that have not yet yielded are cancelled.
        :param urls: The urls of the web resources to fetch content from.
        :return: The results of fetching content from the urls.
        """
        tasks = [asyncio.create_task(self.fetch(url)) for url in urls]
        try:
            for fetch in asyncio.as_completed(tasks):
                try:
                    response = await fetch
                    yield response
                except Exception as e:
                    yield e
        finally:
            await cancel_tasks(tasks)

    @abstractmethod
    async def user_agent(self) -> str | None:
        """Gets the user agent of the client."""
        pass
