# Руководство по ручной миграции данных из Google Sheets в PostgreSQL

Данное руководство описывает процесс ручного переноса данных из Google Sheets в базу данных PostgreSQL без использования автоматической синхронизации.

## Шаг 1: Экспорт данных из Google Sheets

Первым шагом необходимо экспортировать данные из вашей Google таблицы в формат CSV:

1. Откройте вашу Google таблицу
2. Для каждого листа, содержащего данные, выполните:
   - Выберите меню **Файл** > **Скачать** > **CSV (.csv)**
   - Сохраните файл с понятным именем (например, `users.csv`, `contracts.csv` и т.д.)

## Шаг 2: Подготовка CSV файлов

Возможно, потребуется подготовить CSV файлы к импорту:

1. Проверьте файлы на корректную кодировку (рекомендуется UTF-8)
2. Убедитесь, что заголовки столбцов соответствуют полям в базе данных PostgreSQL
3. При необходимости отредактируйте файлы в текстовом редакторе или Excel/LibreOffice

Пример корректного CSV файла для пользователей:
```
id,username,password,role,created_at
1,admin,$2b$12$qZWGvn7o.cj3I5DwhjrqwObqmrABjiFZB9aFQo9Z3X19Rw83WZ5OO,admin,2023-01-01T00:00:00Z
2,user1,$2b$12$qZWGvn7o.cj3I5DwhjrqwObqmrABjiFZB9aFQo9Z3X19Rw83WZ5OO,lawyer,2023-01-02T00:00:00Z
```

## Шаг 3: Импорт данных в PostgreSQL

### Вариант 1: Использование psql и COPY

1. Подключитесь к серверу PostgreSQL через SSH
2. Загрузите CSV файлы на сервер (используя SCP или SFTP)
3. Выполните импорт через команду `psql`:

```bash
# Подключение к базе данных
psql -U contract_user -d contract_db

# Внутри psql выполните:
\COPY users(id, username, password, role, created_at) FROM '/path/to/users.csv' DELIMITER ',' CSV HEADER;
\COPY contracts(id, company_name, inn, director, address, end_date, status, comments, has_nd, lawyer_id, created_at) FROM '/path/to/contracts.csv' DELIMITER ',' CSV HEADER;

# Обновите последовательности для автоинкремента
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('contracts_id_seq', (SELECT MAX(id) FROM contracts));
```

### Вариант 2: Использование pgAdmin

Если у вас установлен pgAdmin:

1. Запустите pgAdmin и подключитесь к вашей базе данных
2. Выберите таблицу, в которую хотите импортировать данные
3. Кликните правой кнопкой мыши на таблице и выберите **Import/Export**
4. Выберите режим **Import**, укажите путь к CSV файлу
5. Настройте опции (разделитель, наличие заголовка и т.д.)
6. Нажмите **OK** для импорта

### Вариант 3: Использование Python и pandas

Для более сложных преобразований можно использовать скрипт на Python:

```python
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Загрузить переменные окружения
load_dotenv()

# Подключение к базе данных
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

# Загрузка данных из CSV
users_df = pd.read_csv('users.csv')
contracts_df = pd.read_csv('contracts.csv')

# Опционально: преобразование данных
# users_df['created_at'] = pd.to_datetime(users_df['created_at'])
# contracts_df['end_date'] = pd.to_datetime(contracts_df['end_date'])

# Импорт в базу данных
users_df.to_sql('users', engine, if_exists='append', index=False)
contracts_df.to_sql('contracts', engine, if_exists='append', index=False)

# Обновление последовательностей через прямое подключение
conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
cur.execute("SELECT setval('contracts_id_seq', (SELECT MAX(id) FROM contracts))")
conn.commit()
cur.close()
conn.close()
```

Сохраните этот скрипт как `import_data.py` и запустите:

```bash
python import_data.py
```

## Шаг 4: Проверка импортированных данных

После импорта данных, убедитесь, что всё перенесено корректно:

```sql
-- Проверка количества записей
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM contracts;

-- Проверка данных
SELECT * FROM users LIMIT 10;
SELECT * FROM contracts LIMIT 10;
```

## Шаг 5: Корректировка данных (при необходимости)

Если некоторые данные не импортировались корректно, вы можете внести изменения с помощью SQL:

```sql
-- Примеры SQL команд для корректировки данных
UPDATE users SET role = 'lawyer' WHERE role = 'юрист';
UPDATE contracts SET status = 'active' WHERE status = 'активный';
```

## Важные примечания

1. **Резервное копирование**: перед импортом обязательно сделайте резервную копию существующей базы данных
2. **Тестовый запуск**: если возможно, сначала протестируйте импорт на тестовой базе данных
3. **Уникальные ключи**: учтите ограничения по уникальным ключам при импорте
4. **Зашифрованные пароли**: убедитесь, что пароли в CSV уже зашифрованы (хешированы) в том же формате, что использует приложение

## Альтернативный подход: Ручное внесение данных через API

Если объем данных небольшой или вы предпочитаете более контролируемый подход, можно использовать API приложения для внесения данных:

1. Запустите приложение на сервере
2. Используйте Swagger UI (по адресу `/docs`) для создания пользователей и контрактов через API
3. Авторизуйтесь как администратор и используйте соответствующие эндпоинты для создания пользователей и контрактов

## Дополнительная информация

- Для сложных миграций рассмотрите возможность использования ETL-инструментов (Talend, Pentaho и др.)
- При большом объеме данных используйте пакетную обработку для импорта
- Не забудьте проверить консистентность и целостность данных после миграции