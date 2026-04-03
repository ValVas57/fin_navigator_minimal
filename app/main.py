from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, profile, goals, chat
import os

# Импортируем роутеры
from app.routers import auth, profile, goals

app = FastAPI(title="FinNavigator", servers=[{"url": "http://localhost:8000"}])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(goals.router)
app.include_router(chat.router)

# --- Эндпоинты ДО статики ---
@app.get("/")
async def root():
    return {"message": "FinNavigator is running!", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# --- Статика В КОНЦЕ ---
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")