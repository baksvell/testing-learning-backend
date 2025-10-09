from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
from typing import List, Optional

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

# Pydantic модели
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
    },
    {
        "id": 3,
        "title": "Тестирование безопасности",
        "description": "Проверьте защиту от SQL-инъекций и XSS атак",
        "category": "Security Testing",
        "difficulty": "Advanced",
        "points": 30,
        "test_cases": json.dumps([
            "Проверить защиту от SQL-инъекций",
            "Проверить защиту от XSS",
            "Проверить валидацию входных данных"
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

@app.get("/api/user/activity")
async def get_user_activity():
    """Получить активность пользователя"""
    return {
        "recent_tasks": [1, 2],
        "completed_today": 3,
        "streak": 5
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

