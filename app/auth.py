from datetime import datetime, timedelta
from jose import JWTError, jwt
import hashlib
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()

def get_password_hash(password: str) -> str:
    """Простое хэширование для тестирования"""
    return hashlib.sha256((password + "finnavigator_salt").encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return get_password_hash(plain) == hashed

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    # Преобразуем user_id в строку
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    print("🔑 Decoding with SECRET_KEY:", SECRET_KEY)
    print("📦 Token received:", token)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("✅ Payload decoded:", payload)
        user_id = payload.get("sub")
        if user_id is None:
            print("❌ No 'sub' in payload")
            raise HTTPException(401, "Invalid token")
    except JWTError as e:
        print("❌ JWTError:", e)
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print("❌ User not found")
        raise HTTPException(401, "User not found")
    return user