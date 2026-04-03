from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import (
    Recommendation, EducationInterest, CareerAspiration,
    UserProfile, Transaction, Category, Goal, RecommendationStatus
)
from app.schemas import (
    EducationInterestCreate, CareerAspirationCreate,
    RecommendationResponse
)
from app.services.budget_analyzer import BudgetAnalyzer

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/", response_model=List[RecommendationResponse])
async def get_recommendations(
    status: str = None,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Получить список рекомендаций"""
    query = db.query(Recommendation).filter(Recommendation.user_id == user_id)
    
    if status:
        query = query.filter(Recommendation.status == status)
    
    recommendations = query.order_by(Recommendation.created_at.desc()).all()
    return recommendations


@router.patch("/{rec_id}")
async def update_recommendation_status(
    rec_id: int,
    status: str,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Изменить статус рекомендации (принять/отклонить)"""
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.user_id == user_id
    ).first()
    
    if not rec:
        raise HTTPException(404, "Рекомендация не найдена")
    
    rec.status = status
    db.commit()
    
    return {"status": "success"}


@router.post("/education/interests")
async def add_education_interest(
    interest: EducationInterestCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Добавить интерес к образованию"""
    new_interest = EducationInterest(
        user_id=user_id,
        **interest.dict()
    )
    db.add(new_interest)
    db.commit()
    
    # Автоматически генерируем рекомендации
    await generate_recommendations(user_id, db)
    
    return {"status": "success"}


@router.post("/career/aspirations")
async def add_career_aspiration(
    aspiration: CareerAspirationCreate,
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Добавить карьерное желание"""
    new_aspiration = CareerAspiration(
        user_id=user_id,
        **aspiration.dict()
    )
    db.add(new_aspiration)
    db.commit()
    
    # Автоматически генерируем рекомендации
    await generate_recommendations(user_id, db)
    
    return {"status": "success"}


@router.post("/generate")
async def generate_recommendations(
    user_id: int = 1,
    db: Session = Depends(get_db)
):
    """Сгенерировать рекомендации на основе интересов и данных"""
    
    # Получаем данные пользователя
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    interests = db.query(EducationInterest).filter(
        EducationInterest.user_id == user_id
    ).all()
    aspirations = db.query(CareerAspiration).filter(
        CareerAspiration.user_id == user_id
    ).all()
    
    recommendations = []
    
    # 1. Рекомендации на основе хобби
    if profile and profile.hobbies:
        for hobby in profile.hobbies:
            rec = analyze_hobby_opportunity(hobby, profile, db)
            if rec:
                recommendations.append(rec)
    
    # 2. Рекомендации на основе интересов к образованию
    for interest in interests:
        rec = analyze_education_interest(interest, db)
        if rec:
            recommendations.append(rec)
    
    # 3. Рекомендации на основе карьерных желаний
    for aspiration in aspirations:
        rec = analyze_career_aspiration(aspiration, db)
        if rec:
            recommendations.append(rec)
    
    # Сохраняем рекомендации в БД
    for rec in recommendations:
        existing = db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.title == rec['title']
        ).first()
        
        if not existing:
            new_rec = Recommendation(
                user_id=user_id,
                **rec
            )
            db.add(new_rec)
    
    db.commit()
    
    return {"status": "success", "generated": len(recommendations)}


def analyze_hobby_opportunity(hobby: str, profile: UserProfile, db: Session) -> Dict:
    """Анализирует возможность монетизации хобби"""
    
    hobby_lower = hobby.lower()
    
    # IT / Программирование
    if hobby_lower in ['программирование', 'it', 'технологии', 'кодинг']:
        return {
            'person_id': 'self',
            'type': 'education',
            'title': 'Курс по современному программированию',
            'description': 'Углубите знания в востребованных направлениях: Python, AI, веб-разработка',
            'estimated_cost': 60000,
            'estimated_duration': '6 месяцев',
            'expected_benefit': 'Повышение дохода на 50 000–100 000 ₽/мес',
            'roi_months': 3,
            'status': 'suggested'
        }
    
    # Фотография
    elif hobby_lower in ['фото', 'фотография', 'съёмка']:
        return {
            'person_id': 'self',
            'type': 'education',
            'title': 'Курс коммерческой фотографии',
            'description': 'Научитесь зарабатывать на предметной и портретной съёмке',
            'estimated_cost': 25000,
            'estimated_duration': '3 месяца',
            'expected_benefit': 'Дополнительный доход от 30 000 ₽/мес',
            'roi_months': 2,
            'status': 'suggested'
        }
    
    # Йога / Фитнес
    elif hobby_lower in ['йога', 'фитнес', 'спорт']:
        return {
            'person_id': 'self',
            'type': 'education',
            'title': 'Обучение на инструктора йоги/фитнеса',
            'description': 'Станьте сертифицированным инструктором и ведите свои группы',
            'estimated_cost': 50000,
            'estimated_duration': '4 месяца',
            'expected_benefit': 'Доход от 40 000 ₽/мес при 3–4 группах',
            'roi_months': 2,
            'status': 'suggested'
        }
    
    # Рисование / Дизайн
    elif hobby_lower in ['рисование', 'дизайн', 'иллюстрация']:
        return {
            'person_id': 'self',
            'type': 'education',
            'title': 'Курс графического дизайна / иллюстрации',
            'description': 'Создавайте дизайн для соцсетей, логотипы, иллюстрации на заказ',
            'estimated_cost': 40000,
            'estimated_duration': '4 месяца',
            'expected_benefit': 'Доход от 50 000 ₽/мес на фрилансе',
            'roi_months': 2,
            'status': 'suggested'
        }
    
    # Языки
    elif hobby_lower in ['английский', 'языки', 'перевод']:
        return {
            'person_id': 'self',
            'type': 'education',
            'title': 'Курс разговорного английского для работы',
            'description': 'Повысьте уровень языка для карьерного роста',
            'estimated_cost': 35000,
            'estimated_duration': '6 месяцев',
            'expected_benefit': 'Возможность работы в международных компаниях, повышение дохода',
            'roi_months': 4,
            'status': 'suggested'
        }
    
    return None


def analyze_education_interest(interest: EducationInterest, db: Session) -> Dict:
    """Анализирует интерес к образованию"""
    
    area_lower = interest.area.lower()
    
    # IT сфера
    if area_lower in ['it', 'программирование', 'data science', 'ai']:
        return {
            'person_id': interest.person_id,
            'type': 'education',
            'title': f'Курс по {interest.area}',
            'description': 'Получите востребованную профессию с возможностью удалённой работы',
            'estimated_cost': 80000,
            'estimated_duration': '8-12 месяцев',
            'expected_benefit': 'Зарплата от 150 000 ₽/мес для Junior специалиста',
            'roi_months': 4,
            'status': 'suggested'
        }
    
    # Бизнес / Управление
    elif area_lower in ['бизнес', 'управление', 'менеджмент']:
        return {
            'person_id': interest.person_id,
            'type': 'education',
            'title': 'MBA или курс по управлению бизнесом',
            'description': 'Развивайте управленческие навыки для карьерного роста',
            'estimated_cost': 120000,
            'estimated_duration': '12 месяцев',
            'expected_benefit': 'Повышение до управленческой позиции, рост дохода на 30-50%',
            'roi_months': 6,
            'status': 'suggested'
        }
    
    return None


def analyze_career_aspiration(aspiration: CareerAspiration, db: Session) -> Dict:
    """Анализирует карьерное желание"""
    
    return {
        'person_id': aspiration.person_id,
        'type': 'career_change',
        'title': f'Смена деятельности: {aspiration.current_industry} → {aspiration.desired_industry}',
        'description': f'Причина: {aspiration.reason}. Рекомендуем пройти профессиональную переподготовку',
        'estimated_cost': 70000,
        'estimated_duration': '6-8 месяцев',
        'expected_benefit': f'Достижение желаемого дохода {aspiration.target_income:,.0f} ₽/мес',
        'roi_months': 5,
        'status': 'suggested'
    }