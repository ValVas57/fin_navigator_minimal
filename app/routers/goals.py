from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models import Goal
from app.auth import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/goals", tags=["goals"])

class GoalCreate(BaseModel):
    name: str
    target_amount: float
    deadline: Optional[date] = None

@router.get("/")
async def get_goals(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Goal).filter(Goal.user_id == current_user.id, Goal.status == "active").all()

@router.post("/")
async def create_goal(data: GoalCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    new_goal = Goal(user_id=current_user.id, **data.dict())
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal

@router.post("/{goal_id}/contribute")
async def contribute(goal_id: int, amount: float, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    goal.current_amount += amount
    if goal.current_amount >= goal.target_amount:
        goal.status = "achieved"
    db.commit()
    return {"current_amount": goal.current_amount, "remaining": goal.target_amount - goal.current_amount}
