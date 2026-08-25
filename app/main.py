"""Главный модуль FastAPI-приложения."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request

from .config import TTL_SECONDS
from .ip import get_client_ip
from .storage import BindingStorage

storage = BindingStorage()


async def _cleanup_loop() -> None:
    """Фоновая задача: раз в минуту чистит записи ttl которых закончился."""
    while True:
        await asyncio.sleep(60)
        storage.cleanup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения:
    - при старте запускаем фоновую задачу очистки
    - при остановке — отменяем её
    """
    task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        task.cancel()


# Создаём само приложение
app = FastAPI(title="IP Bind Service", lifespan=lifespan)


@app.get("/")
async def root(request: Request, name: str | None = Query(default=None)):
    """
    Главный эндпоинт.
    
    GET /                - возвращает IP клиента
    GET /?name=my-laptop - возвращает IP + сохраняет привязку "my-laptop - IP"
    """
    ip = get_client_ip(request)
    bound = False
    if name:
        storage.set(name, ip)
        bound = True
    return {"ip": ip, "name": name, "bound": bound}


@app.get("/bindings/{name}")
async def get_binding(name: str):
    """
    Получить сохранённый IP по имени.
    Вернёт 404, если имя не найдено или TTL истёк.
    """
    ip = storage.get(name)
    if ip is None:
        raise HTTPException(status_code=404, detail="Binding not found or expired")
    return {"name": name, "ip": ip}
