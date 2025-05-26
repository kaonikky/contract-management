# Подробное руководство по развертыванию на Timeweb VDS (Ubuntu 24.04)

Это пошаговая инструкция по развертыванию Python/FastAPI бэкенда и Vue.js фронтенда на VDS сервере Timeweb с Ubuntu 24.04.

## Часть 1: Подготовка сервера

### 1.1. Базовая настройка сервера

Подключитесь к серверу через SSH:
```bash
ssh root@IP_ВАШЕГО_СЕРВЕРА
```

Обновите систему и установите базовые пакеты:
```bash
apt update && apt upgrade -y
apt install -y build-essential git curl wget unzip htop nano ufw python3 python3-pip python3-venv
```

Создайте нового пользователя с правами sudo (не используйте root для повседневных операций):
```bash
adduser deployer
usermod -aG sudo deployer
```

Настройте firewall (UFW):
```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

Переключитесь на нового пользователя:
```bash
su - deployer
```

### 1.2. Настройка PostgreSQL

Установите PostgreSQL:
```bash
sudo apt install -y postgresql postgresql-contrib
```

Настройте базу данных:
```bash
sudo -u postgres psql

# В консоли PostgreSQL выполните:
CREATE DATABASE contract_db;
CREATE USER contract_user WITH ENCRYPTED PASSWORD 'сложный_пароль';
GRANT ALL PRIVILEGES ON DATABASE contract_db TO contract_user;

# Дополнительные права для Alembic миграций
ALTER USER contract_user WITH CREATEDB;
\q
```

Проверьте подключение:
```bash
psql -U contract_user -h localhost -d contract_db -W
# Введите пароль и проверьте, что соединение установлено
\q
```

### 1.3. Настройка Nginx

Установите и настройте Nginx:
```bash
sudo apt install -y nginx

# Создайте конфигурационный файл
sudo nano /etc/nginx/sites-available/contract-management
```

Выберите одну из следующих конфигураций в зависимости от ваших потребностей:

### Вариант 1: Конфигурация для IP-адреса (без SSL)

Для использования IP-адреса 217.198.5.205:

```nginx
server {
    listen 80;
    
    # Указываем IP-адрес вместо доменного имени
    server_name 217.198.5.205;

    # API запросы
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API документация
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://localhost:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend
    location / {
        root /home/deployer/contract-management/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

### Вариант 2: Конфигурация для домена с SSL (для будущего использования)

Если позже вы настроите доменное имя:

```nginx
server {
    listen 80;
    server_name ваш_домен.ru;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name ваш_домен.ru;

    ssl_certificate /etc/letsencrypt/live/ваш_домен.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ваш_домен.ru/privkey.pem;
    
    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API документация
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://localhost:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend
    location / {
        root /home/deployer/contract-management/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```
```

Активируйте конфигурацию:
```bash
sudo ln -s /etc/nginx/sites-available/contract-management /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Удалите конфигурацию по умолчанию, если она есть
sudo nginx -t  # Проверьте конфигурацию
sudo systemctl restart nginx
```

### 1.4. Установка SSL сертификата (опционально, только при наличии домена)

> **Примечание**: Если вы используете только IP-адрес (217.198.5.205), можете пропустить этот раздел, так как получение SSL-сертификата для IP-адреса невозможно.

Установите Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
```

Получите сертификат (только когда у вас будет настроен домен):
```bash
sudo certbot --nginx -d ваш_домен.ru
```

Следуйте инструкциям Certbot. Он автоматически обновит конфигурацию Nginx для использования HTTPS.

## Часть 2: Развертывание бэкенда (Python/FastAPI)

### 2.1. Клонирование репозитория

Создайте директорию для проекта:
```bash
mkdir -p ~/contract-management
cd ~/contract-management
```

Клонируйте репозиторий:
```bash
git clone https://github.com/ваш_репозиторий/contract-management.git .
# Или загрузите код через SFTP
```

### 2.2. Настройка виртуального окружения Python

Создайте и активируйте виртуальное окружение:
```bash
cd ~/contract-management/backend
python3 -m venv venv
source venv/bin/activate
```

Установите зависимости:
```bash
pip install -r requirements.txt
pip install gunicorn  # Для запуска FastAPI в production
```

### 2.3. Настройка переменных окружения

Создайте файл `.env`:
```bash
nano .env
```

Добавьте следующее содержимое:
```
DATABASE_URL=postgresql://contract_user:сложный_пароль@localhost/contract_db
SECRET_KEY=ваш_сложный_секретный_ключ_для_jwt_токенов
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_USERNAME=admin
ADMIN_PASSWORD=initial_admin_password  # Начальный пароль для администратора, смените его после первого входа

# DaData API ключи
DADATA_TOKEN=ваш_токен_dadata
DADATA_SECRET=ваш_секретный_ключ_dadata

# Google Sheets API (если используется миграция из Google Sheets)
GOOGLE_CREDENTIALS_PATH=/home/deployer/contract-management/backend/credentials.json
GOOGLE_SPREADSHEET_ID=ID_вашей_google_таблицы

# Настройки CORS (используйте IP-адрес, если домен не настроен)
CORS_ORIGINS=http://217.198.5.205
```

> **Примечание по IP-адресу**: Если вы используете IP-адрес вместо домена, убедитесь, что в CORS_ORIGINS указан полный URL с протоколом (например, `http://217.198.5.205`). Замените на ваш фактический IP-адрес.

#### Получение ключей DaData API

Для работы с DaData API (автозаполнение данных компаний по ИНН) необходимо получить API-ключи:

1. Зарегистрируйтесь или войдите на сайте [dadata.ru](https://dadata.ru/)
2. Перейдите в раздел [Кабинет -> API-ключи](https://dadata.ru/profile/#info)
3. Скопируйте значения "API-ключ" и "Секретный ключ"
4. Вставьте их в файл `.env` как показано выше

Более подробная информация о настройке и использовании DaData API доступна в файле `DADATA_SETUP.md`.

### 2.4. Применение миграций к базе данных

Выполните миграции Alembic:
```bash
alembic upgrade head
```

Если миграции еще не созданы, выполните:
```bash
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

### 2.5. Создание systemd сервиса для автозапуска

Создайте файл службы systemd:
```bash
sudo nano /etc/systemd/system/contract-api.service
```

Добавьте следующее содержимое:
```ini
[Unit]
Description=Contract Management FastAPI Application
After=network.target postgresql.service

[Service]
User=deployer
Group=deployer
WorkingDirectory=/home/deployer/contract-management/backend
ExecStart=/home/deployer/contract-management/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
Restart=always
RestartSec=5
SyslogIdentifier=contract-api

[Install]
WantedBy=multi-user.target
```

Активируйте и запустите службу:
```bash
sudo systemctl daemon-reload
sudo systemctl enable contract-api
sudo systemctl start contract-api
```

Проверьте статус:
```bash
sudo systemctl status contract-api
```

## Часть 3: Развертывание фронтенда (Vue.js)

### 3.1. Установка Node.js

Установите Node.js и npm:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node -v  # Проверьте версию (должна быть 18.x или новее)
npm -v   # Проверьте версию npm
```

### 3.2. Сборка фронтенда

Перейдите в директорию фронтенда и установите зависимости:
```bash
cd ~/contract-management/frontend
npm install
```

Создайте файл с переменными окружения:
```bash
nano .env.production
```

Добавьте следующее содержимое:
```
# Если используете IP-адрес вместо домена
VITE_API_BASE_URL=http://217.198.5.205/api

# Если используете доменное имя с SSL
# VITE_API_BASE_URL=https://ваш_домен.ru/api
```

Соберите фронтенд:
```bash
npm run build
```

Проверьте, что в директории `dist` созданы файлы сборки.

### 3.3. Настройка автоматических обновлений

Создайте скрипт для обновления:
```bash
nano ~/contract-management/update.sh
```

Добавьте следующее содержимое:
```bash
#!/bin/bash

cd ~/contract-management

# Получаем последние изменения из репозитория
git pull

# Обновляем бэкенд
cd ~/contract-management/backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart contract-api

# Обновляем фронтенд
cd ~/contract-management/frontend
npm install
npm run build

# Перезапускаем Nginx
sudo systemctl restart nginx

echo "Обновление завершено успешно!"
```

Сделайте скрипт исполняемым:
```bash
chmod +x ~/contract-management/update.sh
```

## Часть 4: Ручная миграция данных из Google Sheets в PostgreSQL

Вместо автоматической синхронизации или миграции с использованием API, данные из Google Sheets будут перенесены вручную в PostgreSQL. Это обеспечит полный контроль над процессом миграции и позволит отказаться от зависимости от Google Sheets API в дальнейшем.

### 4.1. Экспорт данных из Google Sheets

1. Откройте вашу Google таблицу в браузере
2. Для каждого листа с данными выполните:
   - Выберите меню **Файл** > **Скачать** > **CSV (.csv)**
   - Сохраните файл с понятным именем (например, `users.csv`, `contracts.csv`)

### 4.2. Загрузка CSV файлов на сервер

Загрузите CSV файлы на сервер через SFTP или scp:
```bash
# На локальном компьютере выполните:
scp путь/к/users.csv deployer@IP_ВАШЕГО_СЕРВЕРА:~/contract-management/backend/migration/users.csv
scp путь/к/contracts.csv deployer@IP_ВАШЕГО_СЕРВЕРА:~/contract-management/backend/migration/contracts.csv
```

Создайте директорию для файлов миграции:
```bash
mkdir -p ~/contract-management/backend/migration
chmod 700 ~/contract-management/backend/migration
```

### 4.3. Импорт данных в PostgreSQL

#### Вариант 1: Использование psql и команды COPY

```bash
cd ~/contract-management/backend
source venv/bin/activate

# Подключение к базе данных
psql -U contract_user -d contract_db

# Внутри psql выполните:
\COPY users(username, password, role, created_at) FROM '~/contract-management/backend/migration/users.csv' DELIMITER ',' CSV HEADER;
\COPY contracts(company_name, inn, director, address, end_date, status, comments, has_nd, lawyer_id, created_at) FROM '~/contract-management/backend/migration/contracts.csv' DELIMITER ',' CSV HEADER;

# Выход из psql
\q
```

#### Вариант 2: Использование Python скрипта

Создайте файл `~/contract-management/backend/import_data.py`:

```python
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import psycopg2

# Загрузить переменные окружения
load_dotenv()

# Подключение к базе данных
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

# Директория с файлами миграции
migration_dir = os.path.join(os.path.dirname(__file__), 'migration')

# Загрузка данных из CSV
users_file = os.path.join(migration_dir, 'users.csv')
contracts_file = os.path.join(migration_dir, 'contracts.csv')

if os.path.exists(users_file):
    users_df = pd.read_csv(users_file)
    # Опционально: преобразование данных
    users_df['created_at'] = pd.to_datetime(users_df['created_at'])
    # Импорт в базу данных
    users_df.to_sql('users', engine, if_exists='append', index=False)
    print(f"Импортировано {len(users_df)} пользователей")

if os.path.exists(contracts_file):
    contracts_df = pd.read_csv(contracts_file)
    # Опционально: преобразование данных
    contracts_df['end_date'] = pd.to_datetime(contracts_df['end_date'])
    contracts_df['created_at'] = pd.to_datetime(contracts_df['created_at'])
    # Импорт в базу данных
    contracts_df.to_sql('contracts', engine, if_exists='append', index=False)
    print(f"Импортировано {len(contracts_df)} контрактов")

# Обновление последовательностей через прямое подключение
conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
cur.execute("SELECT setval('contracts_id_seq', (SELECT MAX(id) FROM contracts))")
conn.commit()
print("Последовательности автоинкремента обновлены")
cur.close()
conn.close()
```

Запустите скрипт:
```bash
cd ~/contract-management/backend
source venv/bin/activate
python import_data.py
```

### 4.4. Проверка импортированных данных

После импорта данных убедитесь, что все записи перенесены корректно:

```bash
psql -U contract_user -d contract_db -c "SELECT COUNT(*) FROM users;"
psql -U contract_user -d contract_db -c "SELECT COUNT(*) FROM contracts;"
```

Подробные инструкции по ручной миграции данных доступны в файле [MANUAL_DATA_MIGRATION.md](MANUAL_DATA_MIGRATION.md).

## Часть 5: Тестирование и мониторинг

### 5.1. Проверка работоспособности

1. Откройте в браузере документацию API:
   - Если используете IP-адрес: `http://217.198.5.205/docs`
   - Если используете домен с SSL: `https://ваш_домен.ru/docs`
   
2. Проверьте работу API, создав тестового пользователя через Swagger UI

3. Проверьте доступность фронтенда:
   - Если используете IP-адрес: `http://217.198.5.205`
   - Если используете домен с SSL: `https://ваш_домен.ru`

### 5.2. Настройка логирования

Создайте директорию для логов:
```bash
mkdir -p ~/contract-management/logs
```

Настройте логирование в FastAPI:
```bash
nano ~/contract-management/backend/app/main.py
```

Добавьте код для настройки логирования.

### 5.3. Мониторинг системы

Установите инструменты мониторинга:
```bash
sudo apt install -y htop iotop
```

Просмотр логов:
```bash
# Логи API
sudo journalctl -u contract-api -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Мониторинг системы
htop
```

## Часть 6: Регулярное обслуживание

### 6.1. Резервное копирование

Установите PostgreSQL клиент-утилиты:
```bash
sudo apt install -y postgresql-client
```

Создайте скрипт для резервного копирования:
```bash
nano ~/contract-management/backup.sh
```

Добавьте содержимое:
```bash
#!/bin/bash

BACKUP_DIR=~/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME=contract_db
DB_USER=contract_user
BACKUP_FILE=$BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Создаем директорию для резервных копий, если ее нет
mkdir -p $BACKUP_DIR

# Делаем резервную копию базы данных
PGPASSWORD=сложный_пароль pg_dump -U $DB_USER -h localhost -d $DB_NAME -F p > $BACKUP_FILE

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

Настройте запуск по расписанию через cron:
```bash
crontab -e
```

Добавьте строку для запуска резервного копирования каждый день в 2:00 ночи:
```
0 2 * * * ~/contract-management/backup.sh >> ~/backups/backup.log 2>&1
```

### 6.2. Обновление системы

Регулярно обновляйте систему:
```bash
sudo apt update && sudo apt upgrade -y
```

### 6.3. Обновление SSL-сертификатов (опционально)

> **Примечание**: Пропустите этот шаг, если вы используете IP-адрес без SSL.

Certbot настраивает автоматическое обновление сертификатов, проверьте его статус:
```bash
sudo systemctl status certbot.timer
```

## Часть 7: Устранение неполадок

### 7.1. Проблемы с API

Если API не отвечает:
```bash
# Проверьте статус службы
sudo systemctl status contract-api

# Проверьте логи
sudo journalctl -u contract-api -f

# Перезапустите службу
sudo systemctl restart contract-api
```

### 7.2. Проблемы с базой данных

```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Проверьте логи
sudo tail -f /var/log/postgresql/postgresql-*.log

# Проверьте подключение к базе данных
psql -U contract_user -h localhost -d contract_db -W
```

### 7.3. Проблемы с Nginx

```bash
# Проверьте статус Nginx
sudo systemctl status nginx

# Проверьте конфигурацию
sudo nginx -t

# Проверьте логи
sudo tail -f /var/log/nginx/error.log
```

## Заключение

Это подробное руководство поможет вам развернуть приложение на Timeweb VDS с Ubuntu 24.04. При возникновении проблем обращайтесь к соответствующим разделам по устранению неполадок.

После успешного развертывания не забудьте:
1. Регулярно обновлять систему
2. Делать резервные копии данных
3. Мониторить работу приложения
4. Обновлять приложение при выходе новых версий