from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date


class ContractBase(BaseModel):
    """Базовая схема контракта"""
    company_name: str = Field(..., min_length=2, max_length=100)
    inn: str = Field(..., min_length=10, max_length=12)
    director: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=5)
    end_date: datetime = Field(...)
    comments: Optional[str] = None
    has_nd: bool = Field(default=False)


class ContractCreate(ContractBase):
    """Схема для создания контракта"""
    # При создании контракта lawyer_id определяется из токена аутентификации
    # или передается явно если администратор создает контракт для другого юриста
    lawyer_id: Optional[int] = None


class ContractUpdate(BaseModel):
    """Схема для обновления контракта"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=100)
    inn: Optional[str] = Field(None, min_length=10, max_length=12)
    director: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = Field(None, min_length=5)
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    comments: Optional[str] = None
    has_nd: Optional[bool] = None
    lawyer_id: Optional[int] = None

    @validator("status")
    def validate_status(cls, v):
        """Проверяет, что статус имеет допустимое значение"""
        if v is None:
            return v
        allowed_statuses = ["active", "expiring_soon", "expired"]
        if v not in allowed_statuses:
            raise ValueError(f"Статус должен быть одним из: {', '.join(allowed_statuses)}")
        return v


class ContractHistoryEntry(BaseModel):
    """Схема для записи в истории изменений контракта"""
    userId: int
    username: str
    action: str  # create, update, etc.
    changes: Dict[str, Dict[str, Any]]  # field: {old: value, new: value}
    timestamp: str


class ContractInDB(ContractBase):
    """Схема контракта в базе данных"""
    id: int
    status: str
    lawyer_id: int
    history: List[ContractHistoryEntry] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class Contract(ContractInDB):
    """Полная схема контракта с дополнительной информацией"""
    days_left: int  # Количество дней до истечения срока


class ContractStats(BaseModel):
    """Схема для статистики по контрактам"""
    total: int
    active: int
    expiring_soon: int
    expired: int
    per_lawyer: Optional[Dict[str, Dict[str, int]]] = None