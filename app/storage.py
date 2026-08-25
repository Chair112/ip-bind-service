"""In-memory хранилище привязок name - ip с TTL."""
from __future__ import annotations

import time
from threading import Lock
from typing import Optional
from .config import TTL_SECONDS


class BindingStorage:
    """
    Простое хранилище в памяти.
    Хранит записи вида: имя -> (IP, время_записи).
    Записи живут TTL секунд, потом удаляются.
    """

    def __init__(self, ttl_seconds: int = TTL_SECONDS) -> None:
        self.ttl = ttl_seconds
        self._data: dict[str, tuple[str, float]] = {}
        self._lock = Lock()

    def set(self, name: str, ip: str) -> None:
        """Сохранить привязку имени к IP."""
        with self._lock:
            self._data[name] = (ip, time.time())

    def get(self, name: str) -> Optional[str]:
        """Получить IP по имени. Вернёт None, если запись время хранения истекло."""
        with self._lock:
            entry = self._data.get(name)
            if entry is None:
                return None
            ip, ts = entry
            # Проверяем, не прошло ли больше TTL секунд
            if time.time() - ts > self.ttl:
                del self._data[name]
                return None
            return ip

    def cleanup(self) -> int:
        """Удаляет все протухшие записи. Возвращает количество удалённых."""
        now = time.time()
        with self._lock:
            expired = [k for k, (_, ts) in self._data.items() if now - ts > self.ttl]
            for k in expired:
                del self._data[k]
            return len(expired)

    def clear(self) -> None:
        """Очистить всё хранилище (используется в тестах)."""
        with self._lock:
            self._data.clear()
