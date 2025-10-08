# Тесты для FastAPI приложения

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base
import os

# Тестовая база данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    """Тест проверки здоровья API"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_register_user(setup_database):
    """Тест регистрации пользователя"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_register_duplicate_user(setup_database):
    """Тест регистрации дублирующегося пользователя"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    # Первая регистрация
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200
    
    # Вторая регистрация с тем же username
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert "уже существует" in response.json()["detail"]

def test_login_user(setup_database):
    """Тест входа пользователя"""
    # Сначала регистрируем пользователя
    user_data = {
        "username": "logintest",
        "email": "login@example.com",
        "password": "testpassword123"
    }
    client.post("/api/auth/register", json=user_data)
    
    # Теперь входим
    login_data = {
        "username": "logintest",
        "password": "testpassword123"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(setup_database):
    """Тест входа с неверными учетными данными"""
    login_data = {
        "username": "nonexistent",
        "password": "wrongpassword"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Неверные учетные данные" in response.json()["detail"]

def test_get_current_user(setup_database):
    """Тест получения данных текущего пользователя"""
    # Регистрируем и входим
    user_data = {
        "username": "currentuser",
        "email": "current@example.com",
        "password": "testpassword123"
    }
    client.post("/api/auth/register", json=user_data)
    
    login_data = {
        "username": "currentuser",
        "password": "testpassword123"
    }
    login_response = client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Получаем данные пользователя
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "currentuser"
    assert data["email"] == "current@example.com"

def test_get_tasks_unauthorized():
    """Тест получения заданий без авторизации"""
    response = client.get("/api/tasks")
    assert response.status_code == 401

def test_get_tasks_authorized(setup_database):
    """Тест получения заданий с авторизацией"""
    # Регистрируем и входим
    user_data = {
        "username": "taskuser",
        "email": "task@example.com",
        "password": "testpassword123"
    }
    client.post("/api/auth/register", json=user_data)
    
    login_data = {
        "username": "taskuser",
        "password": "testpassword123"
    }
    login_response = client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Получаем задания
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/tasks", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_submit_task(setup_database):
    """Тест отправки ответа на задание"""
    # Регистрируем и входим
    user_data = {
        "username": "submituser",
        "email": "submit@example.com",
        "password": "testpassword123"
    }
    client.post("/api/auth/register", json=user_data)
    
    login_data = {
        "username": "submituser",
        "password": "testpassword123"
    }
    login_response = client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Получаем задания
    headers = {"Authorization": f"Bearer {token}"}
    tasks_response = client.get("/api/tasks", headers=headers)
    
    if tasks_response.status_code == 200 and tasks_response.json():
        task_id = tasks_response.json()[0]["id"]
        
        # Отправляем ответ
        submission_data = {
            "answer": {"description": "Тестовый ответ"},
            "time_spent": 120
        }
        
        response = client.post(
            f"/api/tasks/{task_id}/submit",
            json=submission_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert "passed" in data
        assert "feedback" in data

def test_get_achievements(setup_database):
    """Тест получения достижений"""
    # Регистрируем и входим
    user_data = {
        "username": "achievementuser",
        "email": "achievement@example.com",
        "password": "testpassword123"
    }
    client.post("/api/auth/register", json=user_data)
    
    login_data = {
        "username": "achievementuser",
        "password": "testpassword123"
    }
    login_response = client.post("/api/auth/login", json=login_data)
    token = login_response.json()["access_token"]
    
    # Получаем достижения
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/achievements", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_leaderboard():
    """Тест получения рейтинга"""
    response = client.get("/api/leaderboard")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_contact_message(setup_database):
    """Тест отправки контактного сообщения"""
    message_data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "message": "This is a test message"
    }
    
    response = client.post("/api/contact", json=message_data)
    assert response.status_code == 200
    assert "отправлено успешно" in response.json()["message"]

def test_get_products():
    """Тест получения товаров"""
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_products_with_category():
    """Тест получения товаров по категории"""
    response = client.get("/api/products?category=electronics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_products_with_search():
    """Тест поиска товаров"""
    response = client.get("/api/products?search=phone")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

# Запуск тестов
if __name__ == "__main__":
    pytest.main([__file__])

