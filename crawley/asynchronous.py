from abc import ABC, abstractmethod


class AsyncContextManager(ABC):
    """Defines an object that can be used in 'async with' statements."""

    async def __aenter__(self):
        """Allows an instance of the class to be used in an async with statement."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Closes any active connections or sessions when used in an async with statement."""
        await self.close()
        return None

    @abstractmethod
    async def close(self) -> None:
        """Closes any active connections or sessions."""
        pass
