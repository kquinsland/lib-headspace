#!/usr/bin/env -S uv run
"""
Quick and dirty showcase for the library.
Objective is to get the user stats from the API.
"""

import asyncio
from os import getenv

import structlog

from src.lib_headspace.api.client import HeadSpace

log = structlog.get_logger(__name__)


def get_credentials() -> tuple[str, str] | tuple[None, None]:
    """Returns user/password from the environment

    Returns:
        tuple[str, str] | tuple[None, None]: _description_
    """
    user = getenv("LIB_HEADSPACE_USERNAME", None)
    password = getenv("LIB_HEADSPACE_PASSWORD", None)
    if user is None or password is None:
        log.error("Missing credentials")
        return None, None
    return user, password


async def main():
    """Does the needful"""
    log.info("Lib-headspace PoC!")
    user, password = get_credentials()
    if user is None or password is None:
        log.error("Missing credentials")
        exit(1)
    log.info("Got credentials", user=user)
    async with HeadSpace() as client:
        client.user_name = user
        client.password = password
        log.info("Client created and credentials set. Attempting to get auth0 token...")
        await client.get_auth0_token()
        # Assuming nothing bad happened, we should have a token now
        log.info("Attempting to log in...")
        await client.get_headspace_auth_token()
        log.info("Logged in successfully!")
        log.info("Fetching user stats...")
        stats = await client.get_user_stats()
        log.info("Stats fetched", count=len(stats))
        for stat in stats:
            log.info(
                "Stat",
                label=stat["label"],
                current=stat["currentValue"],
                previous=stat["previousValue"],
                as_of=stat["updatedAt"],
            )
        exit()


if __name__ == "__main__":
    asyncio.run(main())
