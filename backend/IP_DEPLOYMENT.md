# Дополнительные настройки для развертывания по IP-адресу

Это дополнение к основным инструкциям по развертыванию содержит специфические настройки для случая, когда приложение разворачивается с использованием IP-адреса (217.198.5.205) вместо доменного имени.

## Изменения в конфигурации Nginx

### Базовая настройка Nginx для работы по IP-адресу

Замените конфигурацию Nginx, чтобы она использовала IP вместо доменного имени:

```nginx
server {
    listen 80;
    
    # Разрешаем доступ по IP адресу
    # Замените на свой IP
    server_name 217.198.5.205;

    # API запросы
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API документация
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend (Vue.js)
    location / {
        root /home/deployer/contract-management/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### Настройка для Docker (docker-compose) без SSL

Для Docker, создайте файл `nginx/conf.d/app.conf` с таким содержимым:

```nginx
server {
    listen 80;
    
    # Разрешаем доступ по IP адресу
    # Замените на свой IP
    server_name 217.198.5.205;

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

## Настройка CORS в FastAPI

Для правильной работы CORS при использовании IP-адреса вместо домена, обновите файл `.env`:

```
# Обновите значение CORS_ORIGINS для IP-адреса
CORS_ORIGINS=http://217.198.5.205
```

Также внесите изменения в файл `app/main.py`:

```python
# Убедитесь, что CORS настроен правильно
from fastapi.middleware.cors import CORSMiddleware

# Получение значения из переменной окружения
cors_origins = os.getenv("CORS_ORIGINS", "http://217.198.5.205").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Настройка Frontend

### Обновление переменных окружения для Vue.js

Создайте или отредактируйте файл `.env.production` в директории frontend:

```
VITE_API_BASE_URL=http://217.198.5.205/api
```

## SSL и безопасность с использованием IP-адреса

### Самоподписанный SSL сертификат (опционально)

Если вы хотите использовать HTTPS даже с IP-адресом, можно создать самоподписанный сертификат:

```bash
# Создание самоподписанного сертификата
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/private/nginx-selfsigned.key -out /etc/ssl/certs/nginx-selfsigned.crt

# Создание параметров Диффи-Хеллмана
sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
```

Настройка Nginx для HTTPS с самоподписанным сертификатом:

```nginx
server {
    listen 80;
    server_name 217.198.5.205;
    
    # Перенаправление на HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 217.198.5.205;
    
    # SSL настройки
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;
    
    # Остальная конфигурация как описано выше
    # ...
}
```

## Важные замечания по безопасности

1. **Доступность по IP-адресу**: Ваше приложение будет доступно всем, кто знает IP-адрес
2. **Отсутствие валидации SSL**: При использовании самоподписанного сертификата браузеры будут выдавать предупреждение о ненадежном соединении
3. **Рекомендации**: 
   - По возможности используйте доменное имя
   - Настройте фаервол для ограничения доступа к серверу
   - Рассмотрите возможность настройки базовой аутентификации в Nginx до завершения разработки

## Дополнительные советы

### Настройка фаервола (рекомендуется)

```bash
# Разрешаем SSH, HTTP и HTTPS
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Включаем фаервол
sudo ufw enable

# Проверяем статус
sudo ufw status
```

### Проверка доступности

После настройки проверьте доступность приложения:

```bash
# Проверка бэкенда
curl http://217.198.5.205/api

# Проверка фронтенда
curl http://217.198.5.205/
```