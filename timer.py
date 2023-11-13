import asyncio


class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.create_task(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        self._callback()

    def cancel(self):
        self._task.cancel()

    def reset(self, timeout=None):
        if timeout is not None:
            self._timeout = timeout
        self.cancel()
        self._task = asyncio.create_task(self._job())
