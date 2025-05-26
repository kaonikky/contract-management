from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.base import get_db
from app.models.models import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate, UserUpdatePassword, UserWithStats
from app.core.auth import get_current_user, get_current_admin
from app.services import user_service

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/", response_model=List[UserSchema])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Только администраторы могут получать список всех пользователей
):
    """Получение списка всех пользователей (только для администраторов)"""
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение информации о пользователе по ID"""
    # Проверяем права доступа
    # Обычные пользователи могут получать информацию только о себе
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете просматривать информацию о других пользователях"
        )
    
    user = user_service.get_user(db, user_id=user_id)
    return user


@router.get("/{user_id}/stats", response_model=UserWithStats)
async def read_user_stats(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получение информации о пользователе со статистикой по контрактам"""
    # Проверяем права доступа
    # Обычные пользователи могут получать информацию только о себе
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете просматривать информацию о других пользователях"
        )
    
    user_with_stats = user_service.get_user_with_stats(db, user_id=user_id)
    return user_with_stats


@router.post("/", response_model=UserSchema)
async def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Только администраторы могут создавать пользователей
):
    """Создание нового пользователя (только для администраторов)"""
    return user_service.create_user(db, user)


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление данных пользователя"""
    # Проверяем права доступа
    # Обычные пользователи могут обновлять только свои данные
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете обновлять данные других пользователей"
        )
    
    # Если обычный пользователь пытается изменить роль, запрещаем
    if current_user.role != "admin" and user_update.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете изменить свою роль"
        )
    
    return user_service.update_user(db, user_id, user_update)


@router.put("/{user_id}/password", response_model=dict)
async def update_password(
    user_id: int,
    password_update: UserUpdatePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновление пароля пользователя"""
    return user_service.update_password(db, user_id, password_update, current_user.id)


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Только администраторы могут удалять пользователей
):
    """Удаление пользователя (только для администраторов)"""
    return user_service.delete_user(db, user_id)