import logging
from aiohttp import ClientSession, ClientResponseError, ClientError, ClientResponse

from crawley.web_requests.clients.client import (
    WebRequestClient,
    FetchResult,
    WebResource,
    Response,
    _is_webpage,
)

logger = logging.getLogger(__name__)


class StaticRequestClient(WebRequestClient):
    """Defines a WebRequestClient that gets static webpages and web resources."""

    def __init__(self, session: ClientSession = None):
        self._session = session or ClientSession()

    async def fetch(self, url: str) -> Response:
        try:
            async with self._session.get(url, raise_for_status=True) as response:
                fetch_result = FetchResult(response.method, url, response.status)
                logger.info(fetch_result)
                return Response(
                    fetch_result, await StaticRequestClient._get_content(response)
                )
        except ClientResponseError as e:
            fetch_result = FetchResult(e.request_info.method, url, e.status)
            logger.warning(fetch_result)
            return Response(fetch_result, None)
        except (ClientError, UnicodeDecodeError) as e:
            logger.error(e)
            raise e

    @staticmethod
    async def _get_content(response: ClientResponse) -> WebResource:
        content_type = response.content_type
        return WebResource(
            content_type,
            (
                await response.text()
                if _is_webpage(content_type)
                else await response.read()
            ),
        )

    async def user_agent(self) -> str | None:
        return self._session.headers.get("User-Agent")

    async def close(self) -> None:
        return await self._session.close()
