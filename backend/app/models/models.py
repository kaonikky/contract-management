from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.base import Base


class User(Base):
    """Модель пользователя (юриста)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), default="lawyer", nullable=False)  # admin или lawyer
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Отношения
    contracts = relationship("Contract", back_populates="lawyer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"


class Contract(Base):
    """Модель контракта"""
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(100), nullable=False)
    inn = Column(String(12), unique=True, index=True, nullable=False)
    director = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, expiring_soon, expired
    comments = Column(Text)
    has_nd = Column(Boolean, default=False)
    history = Column(JSON, default=list)  # История изменений в формате JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Внешние ключи
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Отношения
    lawyer = relationship("User", back_populates="contracts")

    def __repr__(self):
        return f"<Contract(company='{self.company_name}', status='{self.status}')>"