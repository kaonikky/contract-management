import os
import json
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
import logging
from dotenv import load_dotenv

# Импортируем модели и сервисы
from app.database.base import SessionLocal, engine, Base
from app.models.models import User, Contract
from app.core.auth import get_password_hash

# Google API клиенты
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Константы
DEFAULT_PASSWORD = "password123"  # Пароль по умолчанию для импортированных пользователей


def get_db():
    """Получение сессии базы данных для скрипта миграции"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


class GoogleSheetsMigrator:
    def __init__(self, credentials_path, spreadsheet_id):
        """
        Инициализация мигратора Google Sheets
        :param credentials_path: Путь к файлу учетных данных Google API
        :param spreadsheet_id: ID таблицы Google Sheets
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        
        logger.info(f"Инициализация мигратора с ID таблицы: {spreadsheet_id}")

    def initialize(self):
        """Инициализация сервиса Google Sheets API"""
        try:
            # Создаем учетные данные из файла credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
            
            # Создаем сервис
            self.service = build("sheets", "v4", credentials=credentials)
            logger.info("Google Sheets API успешно инициализирован")
            return True
        
        except Exception as e:
            logger.error(f"Ошибка при инициализации Google Sheets API: {e}")
            return False

    def fetch_users(self):
        """Получает данные пользователей из Google Sheets"""
        try:
            # Получаем данные из листа "Users"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Users!A2:D100"  # Диапазон ячеек с данными пользователей
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("Данные о пользователях не найдены")
                return []
            
            users = []
            for row in values:
                if len(row) >= 3:  # Проверяем, что в строке есть минимум 3 столбца
                    user = {
                        "id": int(row[0]) if row[0].isdigit() else None,
                        "username": row[1],
                        "role": row[2],
                        "created_at": datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S") if len(row) > 3 else datetime.now()
                    }
                    users.append(user)
            
            logger.info(f"Получено {len(users)} пользователей из Google Sheets")
            return users
        
        except Exception as e:
            logger.error(f"Ошибка при получении данных пользователей: {e}")
            return []

    def fetch_contracts(self):
        """Получает данные контрактов из Google Sheets"""
        try:
            # Получаем данные из листа "Contracts"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range="Contracts!A2:K100"  # Диапазон ячеек с данными контрактов
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("Данные о контрактах не найдены")
                return []
            
            contracts = []
            for row in values:
                if len(row) >= 7:  # Проверяем, что в строке есть минимум 7 столбцов
                    # Обработка и конвертация данных
                    contract = {
                        "id": int(row[0]) if row[0].isdigit() else None,
                        "company_name": row[1],
                        "inn": row[2],
                        "director": row[3],
                        "address": row[4],
                        "end_date": datetime.strptime(row[5], "%Y-%m-%d") if row[5] else None,
                        "lawyer_id": int(row[6]) if row[6].isdigit() else None,
                        "status": row[7] if len(row) > 7 else "active",
                        "comments": row[8] if len(row) > 8 else None,
                        "has_nd": row[9].lower() in ["true", "1", "yes"] if len(row) > 9 else False,
                        "created_at": datetime.strptime(row[10], "%Y-%m-%d %H:%M:%S") if len(row) > 10 else datetime.now(),
                        "history": []  # Пустая история изменений по умолчанию
                    }
                    contracts.append(contract)
            
            logger.info(f"Получено {len(contracts)} контрактов из Google Sheets")
            return contracts
        
        except Exception as e:
            logger.error(f"Ошибка при получении данных контрактов: {e}")
            return []


def migrate_users(migrator, db):
    """Миграция пользователей из Google Sheets в PostgreSQL"""
    users = migrator.fetch_users()
    
    if not users:
        logger.warning("Нет пользователей для миграции")
        return
    
    count = 0
    for user_data in users:
        # Проверяем, существует ли пользователь уже в базе
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        
        if existing_user:
            logger.info(f"Пользователь {user_data['username']} уже существует в базе")
            continue
        
        # Создаем нового пользователя
        try:
            new_user = User(
                username=user_data["username"],
                password=get_password_hash(DEFAULT_PASSWORD),  # Устанавливаем пароль по умолчанию
                role=user_data["role"],
                created_at=user_data["created_at"]
            )
            
            db.add(new_user)
            db.commit()
            count += 1
            logger.info(f"Создан пользователь {user_data['username']}")
        
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при создании пользователя {user_data['username']}: {e}")
    
    logger.info(f"Миграция пользователей завершена. Создано {count} новых пользователей")


def migrate_contracts(migrator, db):
    """Миграция контрактов из Google Sheets в PostgreSQL"""
    contracts = migrator.fetch_contracts()
    
    if not contracts:
        logger.warning("Нет контрактов для миграции")
        return
    
    count = 0
    for contract_data in contracts:
        # Проверяем, существует ли контракт уже в базе
        existing_contract = db.query(Contract).filter(Contract.inn == contract_data["inn"]).first()
        
        if existing_contract:
            logger.info(f"Контракт с ИНН {contract_data['inn']} уже существует в базе")
            continue
        
        # Проверяем, существует ли юрист
        lawyer = db.query(User).filter(User.id == contract_data["lawyer_id"]).first()
        
        if not lawyer:
            logger.warning(f"Юрист с ID {contract_data['lawyer_id']} не найден. Пропускаем контракт {contract_data['company_name']}")
            continue
        
        # Создаем новый контракт
        try:
            history_entry = {
                "userId": lawyer.id,
                "username": lawyer.username,
                "action": "create",
                "changes": {},
                "timestamp": datetime.now().isoformat()
            }
            
            new_contract = Contract(
                company_name=contract_data["company_name"],
                inn=contract_data["inn"],
                director=contract_data["director"],
                address=contract_data["address"],
                end_date=contract_data["end_date"],
                status=contract_data["status"],
                comments=contract_data["comments"],
                has_nd=contract_data["has_nd"],
                lawyer_id=lawyer.id,
                created_at=contract_data["created_at"],
                history=[history_entry]
            )
            
            db.add(new_contract)
            db.commit()
            count += 1
            logger.info(f"Создан контракт для компании {contract_data['company_name']}")
        
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при создании контракта {contract_data['company_name']}: {e}")
    
    logger.info(f"Миграция контрактов завершена. Создано {count} новых контрактов")


def main():
    """Основная функция для запуска миграции"""
    # Загружаем параметры миграции из переменных окружения
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    
    if not credentials_path or not spreadsheet_id:
        logger.error("Отсутствуют необходимые переменные окружения для миграции")
        print("Ошибка: Установите переменные окружения GOOGLE_CREDENTIALS_PATH и GOOGLE_SPREADSHEET_ID")
        return
    
    # Создаем таблицы в базе данных, если они еще не созданы
    Base.metadata.create_all(bind=engine)
    
    # Инициализируем мигратор
    migrator = GoogleSheetsMigrator(credentials_path, spreadsheet_id)
    
    if not migrator.initialize():
        logger.error("Не удалось инициализировать мигратор. Миграция прервана.")
        return
    
    # Получаем сессию базы данных
    db = get_db()
    
    try:
        # Выполняем миграцию пользователей
        logger.info("Начало миграции пользователей")
        migrate_users(migrator, db)
        
        # Выполняем миграцию контрактов
        logger.info("Начало миграции контрактов")
        migrate_contracts(migrator, db)
        
        logger.info("Миграция успешно завершена")
    
    except Exception as e:
        logger.error(f"Ошибка во время миграции: {e}")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()