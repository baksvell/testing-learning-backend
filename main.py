from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
# База данных временно отключена для совместимости с Render

# Модели базы данных временно отключены

# Создание FastAPI приложения
app = FastAPI(
    title="Testing Learning Platform API",
    description="API для платформы обучения тестированию",
    version="1.2.1"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

class TaskSubmission(BaseModel):
    solution: str
    notes: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

# JWT настройки
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Функция get_db временно отключена

# Простые тестовые пользователи (с простыми паролями для тестирования)
MOCK_USERS = {
    "testuser": "testpass123",  # Простой пароль для тестирования
    "admin": "admin123"         # Простой пароль для тестирования
}

# Функции для работы с паролями (упрощенные для тестирования)
def verify_password(plain_password, stored_password):
    # Для тестирования просто сравниваем строки
    return plain_password == stored_password

def get_password_hash(password):
    # Для тестирования просто возвращаем пароль как есть
    # В продакшене здесь было бы настоящее хеширование
    return password

# JWT функции
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Простые тестовые данные
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

# API маршруты
@app.get("/")
async def root():
    return {"message": "Testing Learning Platform API", "version": "1.6.0", "status": "working"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "API is working",
        "timestamp": datetime.utcnow(),
        "version": "1.6.0"
    }

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
    return {
        "total_users": 150,
        "total_tasks": 2,
        "completed_tasks": 1200
    }

@app.post("/api/tasks/{task_id}/submit")
async def submit_task(task_id: int, submission: TaskSubmission):
    """Отправить решение задачи"""
    task = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "message": "Решение принято!",
        "task_id": task_id,
        "points_earned": task["points"],
        "status": "success",
        "submission_time": datetime.utcnow()
    }

@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    """Регистрация нового пользователя"""
    if user_data.username in MOCK_USERS:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # В реальном приложении здесь бы сохраняли в базу данных
    MOCK_USERS[user_data.username] = user_data.password
    
    return {
        "message": "User registered successfully",
        "username": user_data.username,
        "email": user_data.email
    }

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Вход пользователя"""
    if user_credentials.username not in MOCK_USERS:
        raise HTTPException(status_code=401, detail="Invalid username")
    
    # Проверяем пароль (упрощенно для тестирования)
    if user_credentials.password != MOCK_USERS[user_credentials.username]:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_credentials.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/user/activity")
async def get_user_activity(current_user: str = Depends(verify_token)):
    """Получить активность пользователя (требует авторизации)"""
    return {
        "username": current_user,
        "recent_tasks": [1, 2],
        "completed_today": 3,
        "streak": 5,
        "last_activity": datetime.utcnow()
    }

@app.get("/api/user/profile")
async def get_user_profile(current_user: str = Depends(verify_token)):
    """Получить профиль пользователя (требует авторизации)"""
    return {
        "username": current_user,
        "join_date": "2025-01-01",
        "total_points": 150,
        "level": "Beginner"
    }

@app.get("/api/database/test")
async def test_database():
    """Тест подключения к базе данных"""
    return {
        "status": "info",
        "message": "База данных временно отключена для совместимости с Render",
        "database_type": "Отключена",
        "note": "PostgreSQL драйверы несовместимы с Python 3.13 на Render"
    }

# Для Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
