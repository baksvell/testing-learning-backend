from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import os
import json
from typing import List, Optional

# Конфигурация
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_website.db")

# Создание FastAPI приложения
app = FastAPI(
    title="Testing Learning Platform API",
    description="API для платформы обучения тестированию веб-приложений",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://testing-learning-frontend.vercel.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# База данных
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модели базы данных
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False)
    points = Column(Integer, default=10)
    test_cases = Column(Text)  # JSON строка
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

# Pydantic модели
class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    level: int
    experience: int
    created_at: datetime

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    category: str
    difficulty: str
    points: int
    test_cases: Optional[str] = None

class StatsResponse(BaseModel):
    total_users: int
    total_tasks: int
    completed_tasks: int

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Зависимости
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Заглушки для тестовых данных
MOCK_TASKS = [
    {
        "id": 1,
        "title": "Тестирование формы входа",
        "description": "Протестируйте форму входа на наличие валидации email и пароля",
        "category": "UI/UX Testing",
        "difficulty": "Beginner",
        "points": 10,
        "test_cases": json.dumps([
            "Проверить валидацию email",
            "Проверить валидацию пароля",
            "Проверить сообщения об ошибках"
        ])
    },
    {
        "id": 2,
        "title": "API тестирование",
        "description": "Протестируйте API endpoints на корректность ответов",
        "category": "API Testing",
        "difficulty": "Intermediate",
        "points": 20,
        "test_cases": json.dumps([
            "Проверить статус коды",
            "Проверить структуру JSON",
            "Проверить обработку ошибок"
        ])
    }
]

MOCK_STATS = {
    "total_users": 150,
    "total_tasks": 25,
    "completed_tasks": 1200
}

# API маршруты
@app.get("/")
async def root():
    return {"message": "Testing Learning Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks():
    """Получить список всех задач"""
    return MOCK_TASKS

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    """Получить конкретную задачу"""
    task = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Получить статистику платформы"""
    return MOCK_STATS

@app.post("/api/tasks/{task_id}/submit")
async def submit_task(task_id: int, submission: dict):
    """Отправить решение задачи"""
    task = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "message": "Решение принято!",
        "task_id": task_id,
        "points_earned": task["points"],
        "status": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


