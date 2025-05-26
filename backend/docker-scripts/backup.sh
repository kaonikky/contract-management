#!/bin/bash

# Скрипт для создания резервной копии базы данных

BACKUP_DIR=/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE=$BACKUP_DIR/db_backup_$TIMESTAMP.sql

# Создаем директорию для резервных копий, если ее нет
mkdir -p $BACKUP_DIR

# Получаем переменные окружения
DB_NAME=${POSTGRES_DB:-contract_db}
DB_USER=${POSTGRES_USER:-contract_user}
DB_PASSWORD=${POSTGRES_PASSWORD:-contract_password}
DB_HOST=${POSTGRES_HOST:-db}

# Делаем резервную копию базы данных
echo "Creating database backup..."
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F p > $BACKUP_FILE

# Сжимаем резервную копию
echo "Compressing backup file..."
gzip $BACKUP_FILE

# Удаляем резервные копии старше 30 дней
echo "Removing backups older than 30 days..."
find $BACKUP_DIR -name "db_backup_*.sql.gz" -type f -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"