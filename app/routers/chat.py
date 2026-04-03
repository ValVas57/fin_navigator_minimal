from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, UserProfile, Goal
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str

def get_user_context(user_id: int, db: Session) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()

    context = f"Пользователь: {user.full_name or 'не указано'}\n"
    if profile:
        context += f"Возраст: {profile.age or 'не указан'}\n"
        if profile.hobbies:
            context += f"Хобби: {', '.join(profile.hobbies)}\n"
        if profile.family_members:
            members = [f"{m['name']} ({m['relation']})" for m in profile.family_members]
            context += f"Семья: {', '.join(members)}\n"
        if profile.financial_goals:
            context += f"Финансовые цели: {', '.join(profile.financial_goals)}\n"
    if goals:
        context += "Активные цели:\n"
        for g in goals:
            context += f"- {g.name}: {g.current_amount}/{g.target_amount} руб.\n"
    return context

@router.post("/message")
async def chat(request: ChatRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    context = get_user_context(current_user.id, db)
    
    # Простой ответ-заглушка
    reply = f"""📊 ФинНавигатор (тестовый режим)

Я вижу ваши данные:
{context}

Ваш вопрос: {request.message}

В ближайшее время здесь появится AI-ассистент. А пока вы можете:
- Заполнить профиль (хобби, семья, цели)
- Создать финансовые цели
- Загрузить расходы (в разработке)

Спасибо за использование ФинНавигатора!"""
    
    return {"response": reply}