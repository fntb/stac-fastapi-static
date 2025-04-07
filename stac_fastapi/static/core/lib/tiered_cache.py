from __future__ import annotations

from typing import (
    Optional,
    TypeVar,
    Generic,
    Dict,
    List
)


T = TypeVar("T")


class TieredCache(Generic[T]):

    _cache: tuple[Dict[str, T]]
    _cache_size: int
    _max_cache_size: int | None

    def __init__(self, max_size: Optional[int] = None):
        self._cache = tuple({} for _ in range(40))
        self._cache_size = 0
        self._max_cache_size = max_size

    def _delete_lowest_priority(self, max_priority: Optional[int] = None):
        for priority in range(20, max_priority - 1, -1):
            try:
                self._cache[priority + 19].popitem()
                self._cache_size -= 1
                return True
            except KeyError:
                continue

        return False

    def set(self, key: str, value: T, priority: int = 0):
        priority = min(20, max(priority, -19))

        if self._max_cache_size is not None and self._cache_size > self._max_cache_size:
            if not self._delete_lowest_priority(priority + 1):
                return

        self._cache_size += 1

        self._cache[priority + 19][key] = value

    def get(self, key: str, priority: Optional[int | List[int]] = None) -> T | None:
        if priority is None:
            if (cached_value := self._cache[19].get(key, None)) is not None:
                return cached_value

            for cache in self._cache:
                if (cached_value := cache.get(key, None)) is not None:
                    return cached_value

            return None
        else:
            priorities = [priority] if isinstance(priority, int) else priority

            for priority in priorities:
                priority = min(20, max(priority, -19))
                if (cached_value := self._cache[priority + 19].get(key, None)) is not None:
                    return cached_value

            return None

    def delete(self, key: str, priority: Optional[int | List[int]] = None):
        if priority is None:
            if self._cache[19].get(key, None) is not None:
                self._cache[19].pop(key)
                self._cache_size -= 1
                return

            for cache in self._cache:
                if cache.get(key, None) is not None:
                    cache.pop(key)
                    self._cache_size -= 1
                    return

            return None
        else:
            priorities = [priority] if isinstance(priority, int) else priority

            for priority in priorities:
                priority = min(20, max(priority, -19))
                try:
                    self._cache[priority + 19].pop(key)
                    self._cache_size -= 1
                    return
                except KeyError:
                    pass
