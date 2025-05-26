from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.models.models import User
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Секретный ключ для подписи JWT токенов
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")

# Алгоритм шифрования JWT
ALGORITHM = "HS256"

# Срок действия токена доступа (в минутах)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Создаем контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Создаем схему OAuth2 для проверки токенов в запросах
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


class TokenData:
    """Данные токена"""
    def __init__(self, username: Optional[str] = None):
        self.username = username


def verify_password(plain_password, hashed_password):
    """Проверяет соответствие хешированного пароля и обычного пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Хеширует пароль"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    """Аутентифицирует пользователя по имени пользователя и паролю"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT токен доступа"""
    to_encode = data.copy()
    
    # Устанавливаем срок действия токена
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Создаем и подписываем токен
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Получает текущего пользователя по токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username)
    
    except JWTError:
        raise credentials_exception
    
    # Получаем пользователя из базы данных
    user = db.query(User).filter(User.username == token_data.username).first()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)):
    """Проверяет, что текущий пользователь - администратор"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуются права администратора."
        )
    
    return current_user