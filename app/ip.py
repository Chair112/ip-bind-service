"""Определение IP клиента"""
from __future__ import annotations

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Пытаемся узнать настоящий IP клиента.
    Порядок проверки:
      1. X-Forwarded-For — самый популярный заголовок от прокси
      2. Forwarded — официальный стандарт (RFC 7239)
      3. request.client.host — если соединение прямое, без прокси
    """
    # 1) Пробуем X-Forwarded-For
    # Формат: "клиент, прокси1, прокси2" — берём первого (реальный ip клиента)
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first

    # 2) Пробуем стандартный заголовок Forwarded
    # Формат: "for=185.22.33.44;proto=https;by=10.0.0.1"
    forwarded = request.headers.get("forwarded")
    if forwarded:
        for chain_part in forwarded.split(","):
            for param in chain_part.split(";"):
                param = param.strip()
                if param.lower().startswith("for="):
                    value = param[4:].strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    # IPv6 бывает в скобках: [2001:db8::1]:8080
                    if value.startswith("["):
                        end = value.find("]")
                        if end != -1:
                            return value[1:end]
                    # Убираем порт у IPv4 (185.22.33.44:8080 -> 185.22.33.44)
                    if ":" in value and not value.startswith("["):
                        value = value.rsplit(":", 1)[0]
                    return value

    # 3) Если заголовков нет — берём IP напрямую из соединения
    if request.client and request.client.host:
        return request.client.host

    return "unknown"
