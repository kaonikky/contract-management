"""
Сервис для работы с API DaData
"""
import os
from typing import Optional, Dict, Any, List

from dadata import Dadata
from dotenv import load_dotenv

load_dotenv()

# Получаем API-ключи из переменных окружения
TOKEN = os.getenv("DADATA_TOKEN")
SECRET = os.getenv("DADATA_SECRET")


class DadataService:
    """Сервис для работы с API DaData"""

    def __init__(self, token: Optional[str] = None, secret: Optional[str] = None):
        """
        Инициализация сервиса DaData
        :param token: API-ключ DaData
        :param secret: Секретный ключ DaData
        """
        self.token = token or TOKEN
        self.secret = secret or SECRET
        self.dadata = Dadata(self.token, self.secret)

    def get_company_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о компании по ИНН
        :param inn: ИНН компании
        :return: Информация о компании или None, если компания не найдена
        """
        if not inn:
            return None
        
        try:
            result = self.dadata.find_by_id("party", inn)
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Ошибка при получении данных из DaData: {str(e)}")
            return None

    def get_company_address(self, inn: str) -> Optional[str]:
        """
        Получение адреса компании по ИНН
        :param inn: ИНН компании
        :return: Юридический адрес компании или None, если адрес не найден
        """
        company = self.get_company_by_inn(inn)
        if company and 'data' in company and 'address' in company['data']:
            return company['data']['address'].get('value')
        return None

    def get_company_name(self, inn: str) -> Optional[str]:
        """
        Получение наименования компании по ИНН
        :param inn: ИНН компании
        :return: Наименование компании или None, если компания не найдена
        """
        company = self.get_company_by_inn(inn)
        if company and 'value' in company:
            return company['value']
        return None

    def get_company_director(self, inn: str) -> Optional[str]:
        """
        Получение ФИО руководителя компании по ИНН
        :param inn: ИНН компании
        :return: ФИО руководителя или None, если информация не найдена
        """
        company = self.get_company_by_inn(inn)
        if company and 'data' in company and 'management' in company['data']:
            management = company['data']['management']
            if management and 'name' in management:
                return management['name']
        return None

    def suggest_companies(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск компаний по части наименования или ИНН
        :param query: Часть наименования или ИНН
        :param count: Количество результатов (по умолчанию 5)
        :return: Список найденных компаний
        """
        try:
            result = self.dadata.suggest("party", query, count=count)
            return result
        except Exception as e:
            print(f"Ошибка при поиске компаний в DaData: {str(e)}")
            return []

    def get_company_full_info(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Получение полной информации о компании по ИНН
        :param inn: ИНН компании
        :return: Полная информация о компании
        """
        company = self.get_company_by_inn(inn)
        if not company:
            return None
            
        # Формируем структурированный ответ
        result = {
            "name": company.get('value'),
            "inn": company.get('data', {}).get('inn'),
            "kpp": company.get('data', {}).get('kpp'),
            "ogrn": company.get('data', {}).get('ogrn'),
            "address": company.get('data', {}).get('address', {}).get('value'),
            "status": company.get('data', {}).get('state', {}).get('status'),
            "registration_date": company.get('data', {}).get('state', {}).get('registration_date'),
            "director": company.get('data', {}).get('management', {}).get('name'),
            "director_position": company.get('data', {}).get('management', {}).get('post'),
            "okved": company.get('data', {}).get('okved'),
            "okved_name": company.get('data', {}).get('okved_type') 
        }
        
        return result


# Создаем экземпляр сервиса
dadata_service = DadataService()