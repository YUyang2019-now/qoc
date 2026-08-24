import threading

_cache: dict[str, object] = {}
_lock = threading.Lock()


def cache_get(key: str):
    with _lock:
        return _cache.get(key)


def cache_set(key: str, value: object):
    with _lock:
        _cache[key] = value


def cache_invalidate(*keys: str):
    with _lock:
        for key in keys:
            _cache.pop(key, None)
