import os
import pickle
import asyncio
from typing import List

from loguru import logger
import httpx

PROFANITY_LIST_URL: str = "https://raw.githubusercontent.com/coffee-and-fun/google-profanity-words/refs/heads/main/data/en.txt"
CACHE_FILE = "profanity_cache.pkl"


async def get_profanity_list(url: str = PROFANITY_LIST_URL) -> List[str]:
    """Fetch the profanity list from the remote URL asynchronously and cache it."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "rb") as f:
                cached_list = pickle.load(f)
                logger.debug(f"Loaded cached profanity list from {CACHE_FILE}.")
                return cached_list
        except Exception:
            pass  # Ignore cache errors and refetch

    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Fetching profanity list from {url}...")
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            lines = response.text.splitlines()
            logger.success(f"Fetched profanity list ({len(lines)} words) from {url}.")
            # Check if expected profanity is in list
            if "shit" in lines and "fuck" in lines:
                profanity_list = lines
                # Cache the list as pickle so we don't have to keep sus human-readable lists on disk
                with open(CACHE_FILE, "wb") as f:
                    pickle.dump(profanity_list, f)
                    logger.debug(f"Profanity list cached successfully as {CACHE_FILE}.")
                return profanity_list
            else:
                logger.error("Returned text is not a valid list of words.")
                return []
    except httpx.RequestError as e:
        logger.error(f"Error fetching profanity list: {e}")
        return []


# Fetch global profanity list on module import
nonowords: List[str] = asyncio.run(get_profanity_list())