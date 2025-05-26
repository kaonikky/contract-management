from sqlalchemy.orm import Session
from app.models.models import User
from app.schemas.user import UserCreate, UserUpdate, UserUpdatePassword
from app.core.auth import get_password_hash, verify_password
from fastapi import HTTPException, status


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Получение списка всех пользователей"""
    return db.query(User).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int):
    """Получение пользователя по ID"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    
    return user


def get_user_by_username(db: Session, username: str):
    """Получение пользователя по имени пользователя"""
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: UserCreate):
    """Создание нового пользователя"""
    # Проверяем, что пользователь с таким именем еще не существует
    existing_user = get_user_by_username(db, user.username)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь с именем {user.username} уже существует"
        )
    
    # Хешируем пароль и создаем пользователя
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        password=hashed_password,
        role=user.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate):
    """Обновление данных пользователя"""
    db_user = get_user(db, user_id)
    
    # Если имя пользователя изменилось, проверяем, что новое имя не занято
    if user_update.username and user_update.username != db_user.username:
        existing_user = get_user_by_username(db, user_update.username)
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Пользователь с именем {user_update.username} уже существует"
            )
    
    # Обновляем поля пользователя
    update_data = user_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user


def update_password(db: Session, user_id: int, password_update: UserUpdatePassword, current_user_id: int):
    """Обновление пароля пользователя"""
    db_user = get_user(db, user_id)
    
    # Проверяем, имеет ли текущий пользователь право менять пароль
    # Обычный пользователь может менять только свой пароль, администратор может менять любой пароль
    if current_user_id != user_id and db.query(User).filter(User.id == current_user_id).first().role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете изменить пароль другого пользователя"
        )
    
    # Проверяем текущий пароль
    if not verify_password(password_update.current_password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )
    
    # Обновляем пароль
    db_user.password = get_password_hash(password_update.new_password)
    
    db.commit()
    
    return {"message": "Пароль успешно обновлен"}


def delete_user(db: Session, user_id: int):
    """Удаление пользователя"""
    db_user = get_user(db, user_id)
    
    db.delete(db_user)
    db.commit()
    
    return {"message": f"Пользователь с ID {user_id} успешно удален"}


def get_user_with_stats(db: Session, user_id: int):
    """Получение пользователя со статистикой по контрактам"""
    db_user = get_user(db, user_id)
    
    # Получаем статистику по контрактам пользователя
    total_contracts = len(db_user.contracts)
    active_contracts = sum(1 for contract in db_user.contracts if contract.status == "active")
    expiring_contracts = sum(1 for contract in db_user.contracts if contract.status == "expiring_soon")
    expired_contracts = sum(1 for contract in db_user.contracts if contract.status == "expired")
    
    # Создаем словарь с данными пользователя и статистикой
    user_with_stats = {
        "id": db_user.id,
        "username": db_user.username,
        "role": db_user.role,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at,
        "total_contracts": total_contracts,
        "active_contracts": active_contracts,
        "expiring_contracts": expiring_contracts,
        "expired_contracts": expired_contracts
    }
    
    return user_with_stats