# Руководство по развертыванию приложения

Данное руководство описывает процесс развертывания API-сервера на базе FastAPI на хостинге Timeweb VDS с Ubuntu 24.04.

## Предварительные требования

- VDS/VPS с установленной Ubuntu 24.04
- Доступ по SSH к серверу с правами суперпользователя
- Установленный PostgreSQL (или возможность его установить)
- Доменное имя (опционально)

## Шаг 1: Подготовка сервера

### Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
```

### Установка необходимых пакетов

```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git
```

## Шаг 2: Настройка PostgreSQL

### Вход в PostgreSQL

```bash
sudo -u postgres psql
```

### Создание пользователя и базы данных

```sql
CREATE USER contract_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE contract_db OWNER contract_user;
GRANT ALL PRIVILEGES ON DATABASE contract_db TO contract_user;
\q
```

## Шаг 3: Клонирование репозитория

```bash
cd /opt
sudo mkdir contracts
sudo chown $USER:$USER contracts
cd contracts
git clone https://github.com/yourusername/contract-management.git .
# Или загрузите файлы через SFTP
```

## Шаг 4: Настройка Python-окружения

```bash
cd /opt/contracts
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

## Шаг 5: Настройка переменных окружения

```bash
cd backend
cp .env.example .env
nano .env
```

Отредактируйте файл `.env`, указав правильные настройки для вашего окружения:

```
DATABASE_URL=postgresql://contract_user:your_secure_password@localhost/contract_db
SECRET_KEY=your-very-secure-random-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
PORT=8000
DEBUG=False
CORS_ORIGINS=https://your-frontend-domain.ru
```

## Шаг 6: Инициализация базы данных и миграции

Для инициализации схемы базы данных при первом запуске:

```bash
cd /opt/contracts
source venv/bin/activate
cd backend
# База данных будет автоматически инициализирована при первом запуске
```

### Дополнительно: Миграция данных из Google Sheets (если необходимо)

Если у вас есть данные в Google Sheets, вы можете выполнить миграцию:

```bash
# Сначала настройте параметры в .env:
# GOOGLE_CREDENTIALS_PATH=/path/to/your/google-credentials.json
# GOOGLE_SPREADSHEET_ID=your-spreadsheet-id

# Затем выполните скрипт миграции:
python migration_tool.py
```

## Шаг 7: Настройка Systemd для автозапуска

Создайте файл службы systemd:

```bash
sudo nano /etc/systemd/system/contract-api.service
```

Добавьте следующее содержимое:

```
[Unit]
Description=Contract Management API
After=network.target postgresql.service

[Service]
User=your_username
Group=your_group
WorkingDirectory=/opt/contracts/backend
Environment="PATH=/opt/contracts/venv/bin"
ExecStart=/opt/contracts/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Включите и запустите службу:

```bash
sudo systemctl daemon-reload
sudo systemctl enable contract-api
sudo systemctl start contract-api
```

## Шаг 8: Настройка Nginx

Создайте файл конфигурации Nginx:

```bash
sudo nano /etc/nginx/sites-available/contract-api
```

Добавьте следующее содержимое:

```
server {
    listen 80;
    server_name api.your-domain.ru; # Замените на ваш домен для API

    access_log /var/log/nginx/contract-api-access.log;
    error_log /var/log/nginx/contract-api-error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/contract-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Шаг 9: Настройка SSL (опционально, но рекомендуется)

Установите Certbot для Let's Encrypt:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.your-domain.ru
```

Следуйте инструкциям Certbot для настройки SSL.

## Шаг 10: Проверка работоспособности

API должен быть доступен по адресу `https://api.your-domain.ru` (или `http://your-server-ip:8000`).

Документация API доступна по адресу `https://api.your-domain.ru/docs`.

## Обслуживание и обновление приложения

### Просмотр логов

```bash
sudo journalctl -u contract-api -f
```

### Перезапуск сервиса

```bash
sudo systemctl restart contract-api
```

### Обновление приложения

```bash
cd /opt/contracts
git pull  # Если вы используете git
source venv/bin/activate
pip install -r backend/requirements.txt  # Обновите зависимости, если они изменились
sudo systemctl restart contract-api
```

## Устранение неполадок

### Проблемы с подключением к базе данных

Проверьте настройки подключения в файле `.env` и убедитесь, что PostgreSQL запущен:

```bash
sudo systemctl status postgresql
```

### Проблемы с запуском API

Проверьте логи:

```bash
sudo journalctl -u contract-api -e
```

### Проблемы с Nginx

Проверьте конфигурацию и логи:

```bash
sudo nginx -t
sudo cat /var/log/nginx/error.log
```

## Заключение

Ваш API-сервер должен быть успешно развернут и готов к использованию. Для обеспечения безопасности регулярно обновляйте программное обеспечение и следите за состоянием системы.