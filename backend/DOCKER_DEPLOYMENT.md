# Руководство по развертыванию с использованием Docker

Это руководство описывает процесс развертывания приложения с использованием Docker и Docker Compose на Timeweb VDS с Ubuntu 24.04.

## Преимущества использования Docker

- **Изоляция**: Каждый компонент (API, база данных, фронтенд) работает в отдельном контейнере
- **Воспроизводимость**: Одинаковая среда разработки и продакшена
- **Простота масштабирования**: Легко добавлять новые экземпляры контейнеров
- **Удобное управление зависимостями**: Все зависимости упакованы в контейнер
- **Упрощенное обновление**: Простая процедура обновления приложения

## Часть 1: Подготовка сервера

### 1.1. Базовая настройка сервера

Подключитесь к серверу через SSH:
```bash
ssh root@IP_ВАШЕГО_СЕРВЕРА
```

Обновите систему и установите базовые пакеты:
```bash
apt update && apt upgrade -y
apt install -y curl git ufw nano
```

Настройте firewall (UFW):
```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 1.2. Установка Docker и Docker Compose

Установите Docker:
```bash
# Удалите старые версии, если они установлены
apt remove docker docker-engine docker.io containerd runc

# Установите необходимые пакеты
apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Добавьте официальный GPG ключ Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавьте репозиторий Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Обновите индекс пакетов и установите Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Установите Docker Compose
apt install -y docker-compose-plugin
```

Проверьте установку Docker:
```bash
docker --version
docker compose version
```

Создайте пользователя для управления Docker (необязательно, но рекомендуется):
```bash
# Создайте нового пользователя
adduser deployer
usermod -aG sudo deployer

# Добавьте пользователя в группу docker для запуска без sudo
usermod -aG docker deployer

# Переключитесь на нового пользователя
su - deployer
```

## Часть 2: Подготовка файлов Docker

### 2.1. Создание структуры проекта

Создайте директорию для проекта:
```bash
mkdir -p ~/contract-management
cd ~/contract-management
```

Клонируйте репозиторий (или загрузите через SFTP):
```bash
git clone https://github.com/ваш_репозиторий/contract-management.git .
```

### 2.2. Создание Dockerfile для бэкенда

Создайте файл `backend/Dockerfile`:
```bash
nano backend/Dockerfile
```

Содержимое `backend/Dockerfile`:
```Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Копирование файлов приложения
COPY . .

# Запуск приложения
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2.3. Создание Dockerfile для фронтенда (Vue.js)

Создайте файл `frontend/Dockerfile`:
```bash
nano frontend/Dockerfile
```

Содержимое `frontend/Dockerfile`:
```Dockerfile
# Stage 1: Сборка
FROM node:18-alpine as build-stage

WORKDIR /app

# Установка зависимостей
COPY package*.json ./
RUN npm install

# Копирование кода и сборка
COPY . .
RUN npm run build

# Stage 2: Запуск с Nginx
FROM nginx:stable-alpine as production-stage

# Копирование собранных файлов из первого этапа
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Копирование конфигурации Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Создайте файл `frontend/nginx.conf`:
```bash
nano frontend/nginx.conf
```

Содержимое `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Поддержка SPA (Single Page Application)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Кэширование статических файлов
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
```

### 2.4. Создание Docker Compose файла

Создайте файл `docker-compose.yml` в корне проекта:
```bash
nano docker-compose.yml
```

Содержимое `docker-compose.yml`:
```yaml
version: '3.8'

services:
  # PostgreSQL база данных
  db:
    image: postgres:15
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-contract_db}
      POSTGRES_USER: ${POSTGRES_USER:-contract_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-contract_password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-contract_user}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI бэкенд
  backend:
    build: ./backend
    restart: always
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-contract_user}:${POSTGRES_PASSWORD:-contract_password}@db/${POSTGRES_DB:-contract_db}
      - SECRET_KEY=${SECRET_KEY:-your_default_secret_key_change_it}
      - ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-60}
      - ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin_password}
      - CORS_ORIGINS=${CORS_ORIGINS:-https://your-domain.ru}
    volumes:
      - ./backend/app:/app/app
      - ./backend/migrations:/app/migrations
      - ${GOOGLE_CREDENTIALS_PATH:-./credentials.json}:/app/credentials.json:ro

  # Vue.js фронтенд
  frontend:
    build: ./frontend
    restart: always
    depends_on:
      - backend

  # Nginx прокси-сервер
  nginx:
    image: nginx:stable-alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
      - frontend
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/letsencrypt:/var/www/letsencrypt:ro
      - letsencrypt_data:/etc/letsencrypt

volumes:
  postgres_data:
  letsencrypt_data:
```

### 2.5. Настройка Nginx как обратного прокси

Создайте директорию для конфигурации Nginx:
```bash
mkdir -p ~/contract-management/nginx/conf.d
mkdir -p ~/contract-management/nginx/ssl
mkdir -p ~/contract-management/nginx/letsencrypt
```

Создайте файл основной конфигурации Nginx:
```bash
nano ~/contract-management/nginx/nginx.conf
```

Содержимое `nginx.conf`:
```nginx
user  nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                     '$status $body_bytes_sent "$http_referer" '
                     '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    
    keepalive_timeout  65;
    types_hash_max_size 2048;
    
    gzip  on;
    gzip_disable "msie6";
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    include /etc/nginx/conf.d/*.conf;
}
```

Создайте файл конфигурации сайта:
```bash
nano ~/contract-management/nginx/conf.d/app.conf
```

Содержимое `app.conf` (HTTP версия без SSL):
```nginx
server {
    listen 80;
    server_name ваш_домен.ru;  # Замените на ваш домен

    # Для Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }

    # API запросы
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API документация
    location /docs {
        proxy_pass http://backend:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://backend:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://backend:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend (Vue.js)
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2.6. Настройка переменных окружения

Создайте файл `.env` в корне проекта:
```bash
nano ~/contract-management/.env
```

Содержимое `.env`:
```
# PostgreSQL
POSTGRES_DB=contract_db
POSTGRES_USER=contract_user
POSTGRES_PASSWORD=сгенерируйте_сложный_пароль

# Backend
SECRET_KEY=сгенерируйте_сложный_секретный_ключ
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_USERNAME=admin
ADMIN_PASSWORD=сгенерируйте_сложный_пароль_администратора
CORS_ORIGINS=https://ваш_домен.ru

# DaData API (обязательно для работы с данными компаний)
DADATA_TOKEN=ваш_токен_dadata
DADATA_SECRET=ваш_секретный_ключ_dadata

# Google API (если используется миграция из Google Sheets)
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_SPREADSHEET_ID=id_вашей_google_таблицы
```

#### Получение ключей DaData API

API-ключи для DaData необходимы для функциональности автозаполнения данных о компаниях. Чтобы получить эти ключи:

1. Зарегистрируйтесь или войдите на сайте [dadata.ru](https://dadata.ru/)
2. Перейдите в раздел [Кабинет -> API-ключи](https://dadata.ru/profile/#info)
3. Скопируйте значения "API-ключ" и "Секретный ключ"
4. Добавьте эти ключи в файл `.env` как показано выше

Подробные инструкции по настройке и использованию DaData API содержатся в файле [DADATA_SETUP.md](./DADATA_SETUP.md).

## Часть 3: Запуск с Docker Compose

### 3.1. Запуск контейнеров

Запустите контейнеры в фоновом режиме:
```bash
cd ~/contract-management
docker compose up -d
```

Проверьте статус контейнеров:
```bash
docker compose ps
```

Проверьте логи:
```bash
# Все контейнеры
docker compose logs

# Конкретный контейнер (например, backend)
docker compose logs backend
```

### 3.2. Применение миграций к базе данных

Запустите миграции Alembic:
```bash
docker compose exec backend alembic upgrade head
```

### 3.3. Настройка SSL с Let's Encrypt

Установите Certbot:
```bash
apt install -y certbot
```

Получите SSL сертификат:
```bash
# Остановите Nginx для освобождения порта 80
docker compose stop nginx

# Получите сертификат
certbot certonly --standalone -d ваш_домен.ru --email ваш_email@пример.com --agree-tos -n

# Запустите Nginx снова
docker compose start nginx
```

Обновите конфигурацию Nginx для HTTPS:
```bash
nano ~/contract-management/nginx/conf.d/app.conf
```

Замените содержимое на:
```nginx
server {
    listen 80;
    server_name ваш_домен.ru;  # Замените на ваш домен
    
    # Редирект на HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
    
    # Для Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
}

server {
    listen 443 ssl http2;
    server_name ваш_домен.ru;  # Замените на ваш домен

    # SSL настройки
    ssl_certificate /etc/letsencrypt/live/ваш_домен.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ваш_домен.ru/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Другие заголовки безопасности
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # API запросы
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API документация
    location /docs {
        proxy_pass http://backend:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://backend:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://backend:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend (Vue.js)
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Обновите `docker-compose.yml`, добавив монтирование сертификатов:
```yaml
  nginx:
    # ... существующие строки ...
    volumes:
      # ... существующие строки ...
      - /etc/letsencrypt:/etc/letsencrypt:ro
```

Перезапустите Nginx для применения изменений:
```bash
docker compose restart nginx
```

### 3.4. Настройка автоматического обновления сертификатов

Создайте скрипт для обновления сертификатов:
```bash
nano ~/contract-management/renew_certs.sh
```

Содержимое `renew_certs.sh`:
```bash
#!/bin/bash

# Остановить Nginx
cd ~/contract-management
docker compose stop nginx

# Обновить сертификаты
certbot renew --quiet

# Запустить Nginx снова
docker compose start nginx
```

Сделайте скрипт исполняемым:
```bash
chmod +x ~/contract-management/renew_certs.sh
```

Добавьте задачу в планировщик cron для автоматического обновления:
```bash
crontab -e
```

Добавьте строку для запуска скрипта раз в месяц:
```
0 0 1 * * ~/contract-management/renew_certs.sh >> ~/contract-management/renew_certs.log 2>&1
```

## Часть 4: Ручная миграция данных из Google Sheets в PostgreSQL

Для однократного переноса данных из Google Sheets в PostgreSQL без автоматической синхронизации выполните следующие шаги:

### 4.1. Экспорт данных из Google Sheets

1. Откройте вашу Google таблицу в браузере
2. Экспортируйте данные в CSV:
   - Выберите меню **Файл** > **Скачать** > **CSV (.csv)** для каждого листа
   - Сохраните файлы с понятными именами (например, `users.csv`, `contracts.csv`)

### 4.2. Создание директории для файлов миграции

```bash
# На сервере
cd ~/contract-management
mkdir -p ./backend/migration
chmod 700 ./backend/migration
```

### 4.3. Загрузка файлов на сервер

```bash
# С локального компьютера
scp путь/к/users.csv deployer@IP_ВАШЕГО_СЕРВЕРА:~/contract-management/backend/migration/users.csv
scp путь/к/contracts.csv deployer@IP_ВАШЕГО_СЕРВЕРА:~/contract-management/backend/migration/contracts.csv
```

### 4.4. Создание скрипта для импорта данных

Создайте файл `~/contract-management/backend/migration/import_data.py`:

```python
import pandas as pd
import os
from sqlalchemy import create_engine
import psycopg2
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Подключение к базе данных
db_url = os.environ["DATABASE_URL"]
engine = create_engine(db_url)

try:
    # Загрузка данных из CSV
    users_file = '/app/migration/users.csv'
    contracts_file = '/app/migration/contracts.csv'

    if os.path.exists(users_file):
        logging.info(f"Начинаю импорт пользователей из {users_file}")
        users_df = pd.read_csv(users_file)
        # Преобразование данных при необходимости
        if 'created_at' in users_df.columns:
            users_df['created_at'] = pd.to_datetime(users_df['created_at'])
        # Импорт в базу данных
        users_df.to_sql('users', engine, if_exists='append', index=False)
        logging.info(f"Импортировано {len(users_df)} пользователей")

    if os.path.exists(contracts_file):
        logging.info(f"Начинаю импорт контрактов из {contracts_file}")
        contracts_df = pd.read_csv(contracts_file)
        # Преобразование данных при необходимости
        if 'end_date' in contracts_df.columns:
            contracts_df['end_date'] = pd.to_datetime(contracts_df['end_date'])
        if 'created_at' in contracts_df.columns:
            contracts_df['created_at'] = pd.to_datetime(contracts_df['created_at'])
        # Импорт в базу данных
        contracts_df.to_sql('contracts', engine, if_exists='append', index=False)
        logging.info(f"Импортировано {len(contracts_df)} контрактов")

    # Обновление последовательностей
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
    cur.execute("SELECT setval('contracts_id_seq', (SELECT MAX(id) FROM contracts))")
    conn.commit()
    logging.info("Последовательности автоинкремента обновлены")
    cur.close()
    conn.close()

except Exception as e:
    logging.error(f"Ошибка при импорте данных: {str(e)}")
    raise
```

### 4.5. Запуск импорта в контейнере

```bash
# Копирование CSV файлов в контейнер
docker compose cp ./backend/migration/users.csv backend:/app/migration/users.csv
docker compose cp ./backend/migration/contracts.csv backend:/app/migration/contracts.csv

# Создание директории в контейнере 
docker compose exec backend mkdir -p /app/migration

# Запуск скрипта импорта
docker compose exec backend python /app/migration/import_data.py
```

### 4.6. Проверка импортированных данных

```bash
# Проверка количества записей
docker compose exec db psql -U ${POSTGRES_USER:-contract_user} -d ${POSTGRES_DB:-contract_db} -c "SELECT COUNT(*) FROM users;"
docker compose exec db psql -U ${POSTGRES_USER:-contract_user} -d ${POSTGRES_DB:-contract_db} -c "SELECT COUNT(*) FROM contracts;"
```

Более подробные инструкции о ручной миграции данных доступны в файле [MANUAL_DATA_MIGRATION.md](./MANUAL_DATA_MIGRATION.md).

## Часть 5: Обновление приложения

### 5.1. Обновление кода

Создайте скрипт для обновления:
```bash
nano ~/contract-management/update.sh
```

Содержимое `update.sh`:
```bash
#!/bin/bash

cd ~/contract-management

# Получение последних изменений из репозитория
git pull

# Перезапуск контейнеров с пересборкой
docker compose down
docker compose build --no-cache
docker compose up -d

# Применение миграций
docker compose exec backend alembic upgrade head

echo "Обновление завершено успешно!"
```

Сделайте скрипт исполняемым:
```bash
chmod +x ~/contract-management/update.sh
```

### 5.2. Процесс обновления

Для обновления приложения выполните:
```bash
~/contract-management/update.sh
```

## Часть 6: Резервное копирование

### 6.1. Резервное копирование базы данных

Создайте скрипт для резервного копирования:
```bash
nano ~/contract-management/backup.sh
```

Содержимое `backup.sh`:
```bash
#!/bin/bash

BACKUP_DIR=~/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE=$BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Создаем директорию для резервных копий
mkdir -p $BACKUP_DIR

# Делаем резервную копию базы данных
docker compose exec db pg_dump -U ${POSTGRES_USER:-contract_user} -d ${POSTGRES_DB:-contract_db} > $BACKUP_FILE

# Сжимаем резервную копию
gzip $BACKUP_FILE

# Удаляем резервные копии старше 30 дней
find $BACKUP_DIR -name "db_backup_*.sql.gz" -type f -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

Сделайте скрипт исполняемым:
```bash
chmod +x ~/contract-management/backup.sh
```

Добавьте задачу в планировщик cron для регулярных резервных копий:
```bash
crontab -e
```

Добавьте строку для ежедневного резервного копирования:
```
0 3 * * * ~/contract-management/backup.sh >> ~/backups/backup.log 2>&1
```

### 6.2. Восстановление из резервной копии

В случае необходимости восстановления:
```bash
# Распакуйте архив
gunzip ~/backups/db_backup_YYYYMMDD_HHMMSS.sql.gz

# Восстановите базу данных
docker compose exec -T db psql -U ${POSTGRES_USER:-contract_user} -d ${POSTGRES_DB:-contract_db} < ~/backups/db_backup_YYYYMMDD_HHMMSS.sql
```

## Часть 7: Мониторинг и тестирование

### 7.1. Мониторинг системы

Просмотр логов контейнеров:
```bash
# Все контейнеры
docker compose logs --tail=100 -f

# Конкретный контейнер
docker compose logs --tail=100 -f backend
```

Проверка статуса контейнеров:
```bash
docker compose ps
```

### 7.2. Проверка работоспособности

Тестирование API:
```bash
curl -X GET https://ваш_домен.ru/api
curl -X GET https://ваш_домен.ru/docs
```

### 7.3. Просмотр логов в режиме реального времени

```bash
# Включить логирование в контейнерах
docker compose logs -f
```

## Часть 8: Устранение неполадок

### 8.1. Контейнер не запускается

Проверьте логи:
```bash
docker compose logs имя_контейнера
```

Проверьте состояние контейнера:
```bash
docker compose ps
```

Перезапустите контейнер:
```bash
docker compose restart имя_контейнера
```

### 8.2. Проблемы с базой данных

Проверьте логи контейнера базы данных:
```bash
docker compose logs db
```

Войдите в контейнер PostgreSQL:
```bash
docker compose exec db psql -U ${POSTGRES_USER:-contract_user} -d ${POSTGRES_DB:-contract_db}
```

### 8.3. Проблемы с доступом к API

Проверьте логи контейнера backend:
```bash
docker compose logs backend
```

Перезапустите контейнер:
```bash
docker compose restart backend
```

## Заключение

Использование Docker для развертывания обеспечивает гибкость и изоляцию компонентов приложения. Этот подход позволяет легко масштабировать и обновлять отдельные части системы.

Приложение будет доступно по адресу:
- Frontend: https://ваш_домен.ru
- API: https://ваш_домен.ru/api
- API документация: https://ваш_домен.ru/docs

После успешного развертывания:
1. Регулярно обновляйте Docker и образы контейнеров
2. Следите за логами и резервными копиями
3. При необходимости масштабируйте приложение, добавляя новые контейнеры или используя Docker Swarm
4. Следите за использованием ресурсов на сервере (CPU, RAM, дисковое пространство)