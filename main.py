from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Создание FastAPI приложения
app = FastAPI(
    title="Testing Learning Platform API",
    description="API для платформы обучения тестированию",
    version="1.0.4"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Простые тестовые данные
MOCK_TASKS = [
    {
        "id": 1,
        "title": "Тестирование формы входа",
        "description": "Протестируйте форму входа на наличие валидации email и пароля",
        "category": "UI/UX Testing",
        "difficulty": "Beginner",
        "points": 10
    },
    {
        "id": 2,
        "title": "API тестирование",
        "description": "Протестируйте API endpoints на корректность ответов",
        "category": "API Testing",
        "difficulty": "Intermediate",
        "points": 20
    }
]

# API маршруты
@app.get("/")
async def root():
    return {"message": "Testing Learning Platform API", "version": "1.0.4", "status": "working"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is working"}

@app.get("/api/tasks")
async def get_tasks():
    """Получить список всех задач"""
    return MOCK_TASKS

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    """Получить конкретную задачу"""
    task = next((t for t in MOCK_TASKS if t["id"] == task_id), None)
    if not task:
        return {"error": "Task not found"}, 404
    return task

@app.get("/api/stats")
async def get_stats():
    """Получить статистику платформы"""
    return {
        "total_users": 150,
        "total_tasks": 2,
        "completed_tasks": 1200
    }

# Для Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
