FROM python:3.12.4-alpine3.20

ENV PYTHONUNBUFFERED=1 \
    COLUMNS=200

WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt /app/

# Устанавливаем зависимости и необходимые пакеты
RUN apk update \
    && apk add --no-cache gcc musl-dev libffi-dev postgresql-dev \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем всё содержимое проекта
COPY . /app

# Ожидание готовности базы данных и запуск приложения
CMD ["sh", "-c", "until nc -z $DB_HOST $DB_PORT; do echo 'Waiting for database...'; sleep 1; done; uvicorn core.main:app --host 0.0.0.0 --port 8000 --reload"]
