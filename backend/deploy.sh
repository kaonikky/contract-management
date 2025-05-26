#!/bin/bash

# Скрипт для простого развертывания приложения на сервере
# Используйте: ./deploy.sh [production|staging]

# Проверяем переданный аргумент
ENV=${1:-production}
echo "Развертывание в среде: $ENV"

# Функция для вывода сообщений
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Функция для обработки ошибок
handle_error() {
    log "ОШИБКА: $1"
    exit 1
}

# Проверяем, существует ли Python и pip
command -v python3 >/dev/null 2>&1 || handle_error "Python3 не найден. Установите Python 3.10+"
command -v pip3 >/dev/null 2>&1 || handle_error "pip3 не найден. Установите pip"

# Путь установки
APP_DIR="$(pwd)"
log "Директория приложения: $APP_DIR"

# Создание и активация виртуального окружения
if [ ! -d "venv" ]; then
    log "Создание виртуального окружения..."
    python3 -m venv venv || handle_error "Не удалось создать виртуальное окружение"
fi

# Активация виртуальной среды
log "Активация виртуального окружения..."
source venv/bin/activate || handle_error "Не удалось активировать виртуальное окружение"

# Обновление pip и установка зависимостей
log "Установка зависимостей..."
pip install --upgrade pip || handle_error "Не удалось обновить pip"
pip install -r requirements.txt || handle_error "Не удалось установить зависимости"

# Настройка переменных окружения
if [ ! -f ".env" ]; then
    log "Файл .env не найден, копируем из примера..."
    cp .env.example .env || handle_error "Не удалось создать файл .env"
    log "Внимание: требуется настроить файл .env вручную!"
else
    log "Файл .env уже существует"
fi

# Применение миграций Alembic (если используются)
if command -v alembic >/dev/null 2>&1; then
    log "Применение миграций базы данных..."
    alembic upgrade head || log "Внимание: не удалось применить миграции"
else
    log "Alembic не установлен, миграции не применяются"
fi

# Запуск сервера в зависимости от окружения
if [ "$ENV" = "production" ]; then
    log "Запуск сервера в режиме production..."
    # При наличии systemd-службы не запускаем сервер здесь
    log "Для запуска через systemd выполните: sudo systemctl restart contract-api"
    log "Для проверки статуса: sudo systemctl status contract-api"
else
    log "Запуск сервера в режиме разработки..."
    python run.py
fi

log "Развертывание завершено успешно!"