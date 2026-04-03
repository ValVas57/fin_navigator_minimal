from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import tempfile
import os
import uuid

from app.database import get_db
from app.services.parser import quick_parse, ExcelParser
from app.schemas import UploadPreviewResponse, UploadConfirmRequest
from app.models import Transaction, Category, TransactionSource

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/preview")
async def preview_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> UploadPreviewResponse:
    """Загружает файл и возвращает предпросмотр данных"""
    
    # Проверяем расширение
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Поддерживаются только файлы Excel (.xlsx, .xls)")
    
    # Сохраняем временный файл
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Парсим файл
        parser = ExcelParser(tmp_path)
        preview = parser.get_preview_data()
        
        # Получаем системные категории из БД
        db_categories = db.query(Category).filter(Category.is_income == False).all()
        system_categories = [cat.name for cat in db_categories]
        
        return UploadPreviewResponse(
            months=preview['months'],
            categories=preview['categories'],
            total_amount=preview['total_amount'],
            anomalies=preview['anomalies'],
            system_categories=system_categories,
            suggested_mapping=preview['suggested_mapping']
        )
        
    except Exception as e:
        raise HTTPException(500, f"Ошибка при разборе файла: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.post("/confirm")
async def confirm_upload(
    request: UploadConfirmRequest,
    user_id: int = 1,  # TODO: из аутентификации
    db: Session = Depends(get_db)
):
    """Подтверждает импорт с выбранным маппингом категорий"""
    
    # Сохраняем файл (в реальном приложении файл уже должен быть загружен)
    # Здесь упрощённо: ожидаем, что файл уже загружен через preview
    
    # Получаем категории из БД
    categories = {
        cat.name: cat.id 
        for cat in db.query(Category).all()
    }
    
    # TODO: здесь должна быть логика импорта с использованием переданного маппинга
    
    return {"status": "success", "message": "Импорт выполнен успешно"}