from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.base import get_db
from app.models.models import User
from app.schemas.contract import Contract as ContractSchema, ContractCreate, ContractUpdate, ContractStats
from app.core.auth import get_current_user, get_current_admin
from app.services import contract_service

router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"],
)


@router.get("/", response_model=List[ContractSchema])
async def read_contracts(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    lawyer_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение списка контрактов с фильтрацией и пагинацией
    Обычные пользователи видят только свои контракты,
    администраторы могут видеть все контракты
    """
    return contract_service.get_contracts(
        db, 
        skip=skip, 
        limit=limit, 
        status=status,
        lawyer_id=lawyer_id,
        search=search,
        current_user=current_user
    )


@router.get("/stats", response_model=ContractStats)
async def get_stats(
    lawyer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение статистики по контрактам
    Обычные пользователи видят только статистику по своим контрактам,
    администраторы могут видеть статистику по всем контрактам
    """
    return contract_service.get_stats(db, lawyer_id, current_user)


@router.get("/{contract_id}", response_model=ContractSchema)
async def read_contract(
    contract_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о контракте по ID
    Обычные пользователи могут получать информацию только о своих контрактах,
    администраторы могут получать информацию о любых контрактах
    """
    return contract_service.get_contract(db, contract_id, current_user)


@router.post("/", response_model=ContractSchema)
async def create_contract(
    contract: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создание нового контракта"""
    return contract_service.create_contract(db, contract, current_user)


@router.put("/{contract_id}", response_model=ContractSchema)
async def update_contract(
    contract_id: int,
    contract_update: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновление контракта
    Обычные пользователи могут обновлять только свои контракты,
    администраторы могут обновлять любые контракты
    """
    return contract_service.update_contract(db, contract_id, contract_update, current_user)


@router.delete("/{contract_id}", response_model=dict)
async def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Только администраторы могут удалять контракты
):
    """Удаление контракта (только для администраторов)"""
    return contract_service.delete_contract(db, contract_id)