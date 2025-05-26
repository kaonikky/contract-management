"""
API маршруты для взаимодействия с сервисом DaData
"""
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.models.models import User
from app.services.dadata_service import dadata_service

router = APIRouter(
    prefix="/api/dadata",
    tags=["dadata"],
    responses={404: {"description": "Not found"}},
)


@router.get("/company/{inn}", response_model=Dict[str, Any])
async def get_company_info(
    inn: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получение информации о компании по ИНН
    """
    company = dadata_service.get_company_full_info(inn)
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")
    return company


@router.get("/suggest", response_model=List[Dict[str, Any]])
async def suggest_companies(
    query: str,
    count: Optional[int] = 5,
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Поиск компаний по части наименования или ИНН
    """
    if not query or len(query) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Запрос должен содержать не менее 3 символов"
        )
    
    suggestions = dadata_service.suggest_companies(query, count)
    return suggestions


@router.get("/address/{inn}", response_model=Dict[str, str])
async def get_company_address(
    inn: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Получение юридического адреса компании по ИНН
    """
    address = dadata_service.get_company_address(inn)
    if not address:
        raise HTTPException(status_code=404, detail="Адрес не найден")
    return {"address": address}


@router.get("/director/{inn}", response_model=Dict[str, str])
async def get_company_director(
    inn: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Получение ФИО руководителя компании по ИНН
    """
    director = dadata_service.get_company_director(inn)
    if not director:
        raise HTTPException(status_code=404, detail="Руководитель не найден")
    return {"director": director}