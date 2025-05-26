#!/bin/bash
set -e

# Скрипт для инициализации приложения в Docker-контейнере
echo "Initializing application..."

# Применение миграций Alembic
echo "Applying database migrations..."
alembic upgrade head

# Запуск приложения
echo "Starting application..."
exec "$@"