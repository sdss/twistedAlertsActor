import asyncio
from functools import partial


async def wrapBlocking(func, *args, **kwargs):
    loop = asyncio.get_event_loop()

    wrapped = partial(func, *args, **kwargs)

    return await loop.run_in_executor(None, wrapped)


class Timer:
    """An asynchronous timer."""

    def __init__(self):
        self._timeout = None
        self._callback = None

        self._loop = asyncio.get_event_loop()
        self._task = None

    def start(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback

        self.reset()

    async def _job(self):
        await asyncio.sleep(self._timeout)
        try:
            await self._callback()
        except TypeError:  # Happens when the callback becomes None during an error.
            pass

    def cancel(self):
        """Cancel the timer."""

        if self._task:
            self._task.cancel()

    def reset(self):
        """Reset the count."""

        self.cancel()
        self._task = self._loop.create_task(self._job())
