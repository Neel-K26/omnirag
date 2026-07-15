from functools import lru_cache

import cohere

from config import get_settings


@lru_cache
def get_cohere_client() -> cohere.ClientV2:
    settings = get_settings()
    return cohere.ClientV2(api_key=settings.cohere_api_key)
