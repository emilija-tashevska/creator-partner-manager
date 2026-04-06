"""
ARQ worker launcher compatible with Python 3.14+.

Python 3.14 removed the implicit event loop creation in asyncio.get_event_loop(),
which breaks ARQ's CLI. This script creates the loop explicitly before starting.
"""

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)

from arq.worker import create_worker

from app.workers.settings import WorkerSettings


async def main():
    worker = create_worker(WorkerSettings)
    await worker.main()


if __name__ == "__main__":
    asyncio.run(main())
