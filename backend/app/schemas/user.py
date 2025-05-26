from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str = Field(..., min_length=6)
    role: str = Field(default="lawyer")

    @validator("role")
    def validate_role(cls, v):
        """Проверяет, что роль имеет допустимое значение"""
        allowed_roles = ["admin", "lawyer"]
        if v not in allowed_roles:
            raise ValueError(f"Роль должна быть одной из: {', '.join(allowed_roles)}")
        return v


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    role: Optional[str] = None

    @validator("role")
    def validate_role(cls, v):
        """Проверяет, что роль имеет допустимое значение"""
        if v is None:
            return v
        allowed_roles = ["admin", "lawyer"]
        if v not in allowed_roles:
            raise ValueError(f"Роль должна быть одной из: {', '.join(allowed_roles)}")
        return v


class UserUpdatePassword(BaseModel):
    """Схема для обновления пароля пользователя"""
    current_password: str
    new_password: str = Field(..., min_length=6)


class UserInDB(UserBase):
    """Схема пользователя в базе данных"""
    id: int
    role: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class User(UserInDB):
    """Полная схема пользователя (без пароля)"""
    pass


class UserWithStats(User):
    """Схема пользователя со статистикой по контрактам"""
    total_contracts: int
    active_contracts: int
    expiring_contracts: int
    expired_contracts: int