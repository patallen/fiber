import asyncio


async def standard_sleep():
    await asyncio.sleep(0.01)


async def aenumerate(async_iterable, start=0):

    pos = start
    async for item in async_iterable:
        yield pos, item
        pos += 1
