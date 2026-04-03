from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UserProfile
from app.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/profile", tags=["profile"])

class ProfileCreate(BaseModel):
    first_name: Optional[str] = None
    age: Optional[int] = None
    hobbies: List[str] = []
    family_members: List[dict] = []
    financial_goals: List[str] = []

@router.get("/")
async def get_profile(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return {"user_id": current_user.id}
    return profile

@router.post("/")
async def create_or_update_profile(data: ProfileCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile:
        for key, value in data.dict().items():
            setattr(profile, key, value)
    else:
        profile = UserProfile(user_id=current_user.id, **data.dict())
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
