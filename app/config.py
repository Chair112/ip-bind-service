import os

# Время жизни привязки "имя - IP" в секундах
TTL_SECONDS = int(os.getenv("TTL_SECONDS", "300"))
