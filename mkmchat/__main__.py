"""Entry point for running mkmchat as a module"""

from mkmchat.server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
