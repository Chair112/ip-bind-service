IP Bind Service

FastAPI-сервис, который:
- возвращает IP-адрес клиента (корректно работает за прокси — учитывает `X-Forwarded-For` и `Forwarded`);
- принимает необязательный query-параметр `name` и сохраняет привязку `name -> ip` на время TTL (по умолчанию 5 минут).

Эндпоинты

- `GET /` — возвращает `{"ip": "...", "name": "...", "bound": bool}`
- `GET /?name=my-laptop` — то же, но ещё сохраняет привязку
- `GET /bindings/{name}` — возвращает сохранённый IP по имени (404, если истёк TTL)

Запуск

```bash
docker compose up --build
```

Сервис будет доступен на `http://localhost:8000`.

## Тесты

```bash
pip install -r requirements.txt
pytest -v
```

## Конфигурация

`TTL_SECONDS` время жизни привязки в секундах (по умолчанию 300)
