from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.models import Contract, User
from app.schemas.contract import ContractCreate, ContractUpdate, ContractHistoryEntry
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import json


def calculate_contract_status(end_date: datetime):
    """
    Рассчитывает статус контракта на основе даты окончания
    """
    now = datetime.utcnow()
    
    # Рассчитываем разницу в днях
    days_left = (end_date - now).days
    
    if days_left < 0:
        return {"status": "expired", "days_left": 0}
    elif days_left <= 30:
        return {"status": "expiring_soon", "days_left": days_left}
    else:
        return {"status": "active", "days_left": days_left}


def get_contracts(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    status: str = None,
    lawyer_id: int = None,
    search: str = None,
    current_user: User = None
):
    """
    Получение списка контрактов с фильтрацией и пагинацией
    Обычные пользователи видят только свои контракты,
    администраторы могут видеть все контракты
    """
    query = db.query(Contract)
    
    # Фильтрация по статусу
    if status:
        query = query.filter(Contract.status == status)
    
    # Фильтрация по юристу
    if lawyer_id:
        query = query.filter(Contract.lawyer_id == lawyer_id)
    elif current_user and current_user.role != "admin":
        # Обычные пользователи видят только свои контракты
        query = query.filter(Contract.lawyer_id == current_user.id)
    
    # Фильтрация по поисковой строке
    if search:
        query = query.filter(
            or_(
                Contract.company_name.ilike(f"%{search}%"),
                Contract.inn.ilike(f"%{search}%"),
                Contract.director.ilike(f"%{search}%"),
                Contract.address.ilike(f"%{search}%")
            )
        )
    
    # Получаем контракты с пагинацией
    contracts = query.offset(skip).limit(limit).all()
    
    # Рассчитываем актуальные статусы и дни до истечения
    result = []
    for contract in contracts:
        status_info = calculate_contract_status(contract.end_date)
        
        # Обновляем статус в базе данных, если он изменился
        if contract.status != status_info["status"]:
            contract.status = status_info["status"]
            db.commit()
        
        # Создаем объект с дополнительной информацией
        contract_dict = {
            "id": contract.id,
            "company_name": contract.company_name,
            "inn": contract.inn,
            "director": contract.director,
            "address": contract.address,
            "end_date": contract.end_date,
            "status": contract.status,
            "comments": contract.comments,
            "has_nd": contract.has_nd,
            "lawyer_id": contract.lawyer_id,
            "history": contract.history,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
            "days_left": status_info["days_left"]
        }
        
        result.append(contract_dict)
    
    return result


def get_contract(db: Session, contract_id: int, current_user: User = None):
    """
    Получение контракта по ID
    Обычные пользователи могут получать информацию только о своих контрактах,
    администраторы могут получать информацию о любых контрактах
    """
    # Получаем контракт из базы данных
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Контракт с ID {contract_id} не найден"
        )
    
    # Проверяем права доступа
    if current_user and current_user.role != "admin" and contract.lawyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому контракту"
        )
    
    # Рассчитываем актуальный статус и дни до истечения
    status_info = calculate_contract_status(contract.end_date)
    
    # Обновляем статус в базе данных, если он изменился
    if contract.status != status_info["status"]:
        contract.status = status_info["status"]
        db.commit()
    
    # Создаем объект с дополнительной информацией
    contract_dict = {
        "id": contract.id,
        "company_name": contract.company_name,
        "inn": contract.inn,
        "director": contract.director,
        "address": contract.address,
        "end_date": contract.end_date,
        "status": contract.status,
        "comments": contract.comments,
        "has_nd": contract.has_nd,
        "lawyer_id": contract.lawyer_id,
        "history": contract.history,
        "created_at": contract.created_at,
        "updated_at": contract.updated_at,
        "days_left": status_info["days_left"]
    }
    
    return contract_dict


def get_contract_by_inn(db: Session, inn: str):
    """Получение контракта по ИНН"""
    return db.query(Contract).filter(Contract.inn == inn).first()


def create_contract(db: Session, contract: ContractCreate, current_user: User):
    """Создание нового контракта"""
    # Проверяем, что контракт с таким ИНН еще не существует
    existing_contract = get_contract_by_inn(db, contract.inn)
    
    if existing_contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Контракт с ИНН {contract.inn} уже существует"
        )
    
    # Определяем ID юриста
    lawyer_id = contract.lawyer_id if contract.lawyer_id else current_user.id
    
    # Если указан ID юриста, проверяем, существует ли такой юрист
    if lawyer_id != current_user.id:
        # Только администраторы могут создавать контракты для других юристов
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не можете создать контракт для другого юриста"
            )
        
        # Проверяем существование юриста
        lawyer = db.query(User).filter(User.id == lawyer_id).first()
        
        if not lawyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Юрист с ID {lawyer_id} не найден"
            )
    
    # Рассчитываем статус контракта
    status_info = calculate_contract_status(contract.end_date)
    
    # Создаем запись в истории
    history_entry = ContractHistoryEntry(
        userId=current_user.id,
        username=current_user.username,
        action="create",
        changes={},
        timestamp=datetime.utcnow().isoformat()
    )
    
    # Создаем новый контракт
    db_contract = Contract(
        company_name=contract.company_name,
        inn=contract.inn,
        director=contract.director,
        address=contract.address,
        end_date=contract.end_date,
        status=status_info["status"],
        comments=contract.comments,
        has_nd=contract.has_nd,
        lawyer_id=lawyer_id,
        history=[history_entry.dict()]
    )
    
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    
    # Добавляем информацию о днях до истечения
    contract_dict = get_contract(db, db_contract.id)
    
    return contract_dict


def update_contract(db: Session, contract_id: int, contract_update: ContractUpdate, current_user: User):
    """
    Обновление контракта
    Обычные пользователи могут обновлять только свои контракты,
    администраторы могут обновлять любые контракты
    """
    # Получаем контракт из базы данных
    db_contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not db_contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Контракт с ID {contract_id} не найден"
        )
    
    # Проверяем права доступа
    if current_user.role != "admin" and db_contract.lawyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому контракту"
        )
    
    # Если меняется ИНН, проверяем, что новый ИНН не занят
    if contract_update.inn and contract_update.inn != db_contract.inn:
        existing_contract = get_contract_by_inn(db, contract_update.inn)
        
        if existing_contract:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Контракт с ИНН {contract_update.inn} уже существует"
            )
    
    # Если меняется ID юриста, проверяем, существует ли такой юрист
    if contract_update.lawyer_id and contract_update.lawyer_id != db_contract.lawyer_id:
        # Только администраторы могут менять юриста контракта
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не можете изменить юриста контракта"
            )
        
        # Проверяем существование юриста
        lawyer = db.query(User).filter(User.id == contract_update.lawyer_id).first()
        
        if not lawyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Юрист с ID {contract_update.lawyer_id} не найден"
            )
    
    # Отслеживаем изменения для истории
    changes = {}
    update_data = contract_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        old_value = getattr(db_contract, key)
        
        # Если значение изменилось
        if old_value != value:
            # Для дат преобразуем в строку
            if key == 'end_date' and old_value and value:
                old_str = old_value.isoformat()
                new_str = value.isoformat()
                changes[key] = {"old": old_str, "new": new_str}
            else:
                changes[key] = {"old": old_value, "new": value}
            
            # Обновляем значение
            setattr(db_contract, key, value)
    
    # Если изменилась дата окончания, пересчитываем статус
    if 'end_date' in update_data:
        status_info = calculate_contract_status(db_contract.end_date)
        db_contract.status = status_info["status"]
    
    # Обновляем историю, только если были изменения
    if changes:
        history_entry = ContractHistoryEntry(
            userId=current_user.id,
            username=current_user.username,
            action="update",
            changes=changes,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Получаем текущую историю и добавляем новую запись
        history = db_contract.history if db_contract.history else []
        history.append(history_entry.dict())
        db_contract.history = history
    
    db.commit()
    db.refresh(db_contract)
    
    # Получаем обновленный контракт с дополнительной информацией
    return get_contract(db, db_contract.id)


def delete_contract(db: Session, contract_id: int):
    """Удаление контракта"""
    db_contract = db.query(Contract).filter(Contract.id == contract_id).first()
    
    if not db_contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Контракт с ID {contract_id} не найден"
        )
    
    db.delete(db_contract)
    db.commit()
    
    return {"message": f"Контракт с ID {contract_id} успешно удален"}


def get_stats(db: Session, lawyer_id: int = None, current_user: User = None):
    """
    Получение статистики по контрактам
    Обычные пользователи видят только статистику по своим контрактам,
    администраторы могут видеть статистику по всем контрактам
    """
    query = db.query(Contract)
    
    # Обычные пользователи видят только свои контракты
    if current_user and current_user.role != "admin" and not lawyer_id:
        lawyer_id = current_user.id
    
    # Фильтрация по юристу
    if lawyer_id:
        query = query.filter(Contract.lawyer_id == lawyer_id)
    
    # Получаем все контракты
    contracts = query.all()
    
    # Обновляем статусы контрактов
    for contract in contracts:
        status_info = calculate_contract_status(contract.end_date)
        if contract.status != status_info["status"]:
            contract.status = status_info["status"]
    
    # Фиксируем изменения в базе данных
    db.commit()
    
    # Считаем статистику
    total = len(contracts)
    active = sum(1 for c in contracts if c.status == "active")
    expiring_soon = sum(1 for c in contracts if c.status == "expiring_soon")
    expired = sum(1 for c in contracts if c.status == "expired")
    
    stats = {
        "total": total,
        "active": active,
        "expiring_soon": expiring_soon,
        "expired": expired
    }
    
    # Если запрос от администратора и не указан конкретный юрист,
    # добавляем статистику по каждому юристу
    if current_user and current_user.role == "admin" and not lawyer_id:
        per_lawyer = {}
        
        # Получаем всех юристов
        lawyers = db.query(User).all()
        
        for lawyer in lawyers:
            lawyer_contracts = db.query(Contract).filter(Contract.lawyer_id == lawyer.id).all()
            
            # Подсчитываем статистику для каждого юриста
            lawyer_total = len(lawyer_contracts)
            lawyer_active = sum(1 for c in lawyer_contracts if c.status == "active")
            lawyer_expiring_soon = sum(1 for c in lawyer_contracts if c.status == "expiring_soon")
            lawyer_expired = sum(1 for c in lawyer_contracts if c.status == "expired")
            
            per_lawyer[lawyer.username] = {
                "total": lawyer_total,
                "active": lawyer_active,
                "expiring_soon": lawyer_expiring_soon,
                "expired": lawyer_expired
            }
        
        stats["per_lawyer"] = per_lawyer
    
    return stats