# Руководство по тестированию API перед деплоем

Данное руководство поможет вам проверить работоспособность API перед переносом на боевой сервер.

## 1. Подготовка тестовой среды

### 1.1. Настройка локальной базы данных PostgreSQL

1. Установите PostgreSQL, если он еще не установлен:

   ```bash
   # Для Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib

   # Для macOS с Homebrew
   brew install postgresql
   ```

2. Создайте базу данных и пользователя:

   ```bash
   sudo -u postgres psql
   ```

   Выполните в PostgreSQL:

   ```sql
   CREATE DATABASE contract_db;
   CREATE USER contract_user WITH ENCRYPTED PASSWORD 'ваш_пароль';
   GRANT ALL PRIVILEGES ON DATABASE contract_db TO contract_user;
   \q
   ```

3. Проверьте подключение к базе данных:

   ```bash
   psql -U contract_user -h localhost -d contract_db
   ```

### 1.2. Настройка виртуального окружения Python и установка зависимостей

1. Создайте и активируйте виртуальное окружение:

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # или
   venv\Scripts\activate     # Windows
   ```

2. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

### 1.3. Настройка переменных окружения

1. Создайте файл `.env` на основе примера:

   ```bash
   cp .env.example .env
   ```

2. Отредактируйте файл `.env`, указав настройки подключения к вашей локальной БД:

   ```
   DATABASE_URL=postgresql://contract_user:ваш_пароль@localhost/contract_db
   SECRET_KEY=секретный_ключ_для_jwt_токенов
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

## 2. Инициализация базы данных и миграции

1. Проверьте и установите Alembic, если необходимо:

   ```bash
   pip install alembic
   ```

2. Создайте файл конфигурации Alembic, если его еще нет:

   ```bash
   alembic init migrations
   ```

3. Примените миграции для создания схемы базы данных:

   ```bash
   alembic upgrade head
   ```

   При отсутствии миграций создайте их:

   ```bash
   alembic revision --autogenerate -m "initial"
   alembic upgrade head
   ```

## 3. Запуск API сервера для тестирования

1. Запустите сервер:

   ```bash
   cd backend
   python run.py
   ```

   Или используйте uvicorn напрямую:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Проверьте доступность API, открыв в браузере: [http://localhost:8000](http://localhost:8000)

3. Откройте документацию API Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

## 4. Тестирование основных функций API

Для тестирования API можно использовать Swagger UI, Postman или curl.

### 4.1. Создание администратора

API должен автоматически создать администратора при первом запуске, проверьте это через эндпоинт `/api/login`:

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

Вы должны получить токен доступа.

### 4.2. Работа с пользователями

1. Получение токена аутентификации (сохраните полученный токен):

   ```bash
   curl -X POST http://localhost:8000/api/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin"}'
   ```

2. Создание нового пользователя:

   ```bash
   curl -X POST http://localhost:8000/api/users \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ВАШ_ТОКЕН" \
     -d '{"username":"test_user","password":"password123","role":"lawyer"}'
   ```

3. Получение списка пользователей:

   ```bash
   curl -X GET http://localhost:8000/api/users \
     -H "Authorization: Bearer ВАШ_ТОКЕН"
   ```

### 4.3. Работа с контрактами

1. Создание контракта:

   ```bash
   curl -X POST http://localhost:8000/api/contracts \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ВАШ_ТОКЕН" \
     -d '{
       "company_name": "ООО Тест",
       "inn": "1234567890",
       "director": "Иванов И.И.",
       "address": "г. Москва, ул. Тестовая, 1",
       "end_date": "2025-12-31T00:00:00Z",
       "comments": "Тестовый контракт",
       "has_nd": false
     }'
   ```

2. Получение списка контрактов:

   ```bash
   curl -X GET http://localhost:8000/api/contracts \
     -H "Authorization: Bearer ВАШ_ТОКЕН"
   ```

3. Получение статистики по контрактам:

   ```bash
   curl -X GET http://localhost:8000/api/contracts/stats \
     -H "Authorization: Bearer ВАШ_ТОКЕН"
   ```

## 5. Настройка и проверка интеграции с DaData API

DaData API используется для получения информации о компаниях по ИНН. Для настройки и использования DaData:

1. Получите API-ключи DaData:
   - Зарегистрируйтесь или войдите на сайте [dadata.ru](https://dadata.ru/)
   - Перейдите в [Кабинет -> API-ключи](https://dadata.ru/profile/#info)
   - Скопируйте значения "API-ключ" и "Секретный ключ"

2. Обновите файл `.env`, добавив:
   ```
   DADATA_TOKEN=ваш_апи_ключ_dadata
   DADATA_SECRET=ваш_секретный_ключ_dadata
   ```

3. Запустите приложение и проверьте работу DaData API:
   - Получите токен аутентификации:
     ```bash
     curl -X POST http://localhost:8000/api/login \
       -H "Content-Type: application/json" \
       -d '{"username":"admin","password":"admin"}'
     ```
   - Выполните тестовый запрос к API DaData:
     ```bash
     curl -X GET "http://localhost:8000/api/dadata/suggest?query=сбербанк" \
       -H "Authorization: Bearer ВАШ_ТОКЕН"
     ```

4. Более подробная информация о настройке и использовании DaData API находится в файле [DADATA_SETUP.md](DADATA_SETUP.md).

## 6. Ручная миграция данных из Google Sheets

Поскольку мы планируем однократный перенос данных из Google Sheets в PostgreSQL без автоматической синхронизации, рекомендуется выполнить ручную миграцию:

1. Экспортируйте данные из Google Sheets:
   - Для каждого листа с данными выберите **Файл** > **Скачать** > **CSV (.csv)**
   - Сохраните файлы с понятными именами (например, `users.csv`, `contracts.csv`)

2. Импортируйте данные в PostgreSQL одним из следующих способов:
   - Используя команду `\COPY` в psql
   - Через интерфейс pgAdmin
   - С помощью скрипта на Python с использованием pandas

3. Проверьте корректность импортированных данных:
   ```sql
   SELECT COUNT(*) FROM users;
   SELECT COUNT(*) FROM contracts;
   ```

4. При необходимости скорректируйте данные с помощью SQL-запросов.

Подробные инструкции доступны в файле [MANUAL_DATA_MIGRATION.md](MANUAL_DATA_MIGRATION.md).

## 6. Обнаружение и решение проблем

### 6.1. Проблемы с подключением к базе данных

Если возникают ошибки подключения к БД:

1. Проверьте настройки в файле `.env`
2. Убедитесь, что PostgreSQL запущен:
   ```bash
   sudo systemctl status postgresql
   ```
3. Проверьте логи PostgreSQL:
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

### 6.2. Ошибки в API

1. Проверьте логи сервера в консоли
2. Активируйте подробное логирование в `app/main.py`, добавив:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### 6.3. Проблемы с аутентификацией

1. Проверьте, что SECRET_KEY настроен правильно
2. Проверьте срок действия токенов (ACCESS_TOKEN_EXPIRE_MINUTES)
3. Убедитесь, что запросы отправляются с правильным форматом заголовка Authorization

## 7. Заключение

После успешного прохождения всех тестов, приложение готово к деплою на боевой сервер. Используйте инструкции из файла DEPLOYMENT.md для развертывания.

Если возникают проблемы с аутентификацией, контрактами или другими аспектами API, обратитесь к документации FastAPI и DEPLOYMENT.md для дополнительной информации о настройке и конфигурации.

При необходимости настройте дополнительные аспекты системы, такие как CORS, логирование или производительность базы данных, перед запуском в продакшен.