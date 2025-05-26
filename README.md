# Система управления корпоративными контрактами

Веб-приложение для управления корпоративными контрактами российских предприятий с интеллектуальной обработкой данных.

## Технологии

- **Бэкенд**: Python 3.11, FastAPI, SQLAlchemy
- **База данных**: PostgreSQL
- **Фронтенд**: Vue.js 3, Tailwind CSS
- **Веб-сервер**: Nginx
- **Деплой**: PM2, Ubuntu 24.04

## Структура проекта

```
contract-management/
├── backend/           # Python FastAPI бэкенд
├── vue-client/        # Vue.js фронтенд
├── client/           # React фронтенд (альтернативный)
├── shared/           # Общие типы данных
├── server/           # Express.js сервер
└── drizzle_migration_tool.js  # Скрипт миграции данных
```

## Установка и запуск

### Требования
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Nginx

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/YOUR_USERNAME/contract-management.git
cd contract-management
```

2. Настройте бэкенд:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл
```

4. Настройте фронтенд:
```bash
cd vue-client
npm install
npm run build
```

5. Запустите приложение:
```bash
pm2 start ecosystem.config.cjs
```

## Конфигурация

Создайте файл `.env` в директории `backend/` со следующими переменными:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Развертывание

Подробные инструкции по развертыванию см. в файле `DEPLOYMENT.md`.

## Миграция данных

Для миграции данных из Google Sheets используйте:

```bash
export GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
export GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
export DATABASE_URL=your_database_url
node drizzle_migration_tool.js
```

## API Документация

После запуска сервера, документация API доступна по адресу:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Поддержка

Для получения поддержки или сообщения об ошибках создайте issue в репозитории.