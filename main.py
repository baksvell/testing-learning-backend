from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import secrets
import json
from typing import List, Optional

# Конфигурация
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_website.db")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 часа

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

# Безопасность
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Модели базы данных
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    
    # Связи
    achievements = relationship("UserAchievement", back_populates="user")
    test_results = relationship("TestResult", back_populates="user")

class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50))
    points = Column(Integer, default=10)
    category = Column(String(50))
    
    # Связи
    user_achievements = relationship("UserAchievement", back_populates="achievement")

class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

class TestTask(Base):
    __tablename__ = "test_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False)
    points = Column(Integer, default=10)
    test_data = Column(Text)
    expected_result = Column(Text)
    hints = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    test_results = relationship("TestResult", back_populates="task")

class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("test_tasks.id"), nullable=False)
    score = Column(Integer, default=0)
    max_score = Column(Integer, default=0)
    passed = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)
    time_spent = Column(Integer)
    user_answer = Column(Text)
    feedback = Column(Text)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="test_results")
    task = relationship("TestTask", back_populates="test_results")

class LearningProgress(Base):
    __tablename__ = "learning_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=False)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    in_stock = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)

# Pydantic модели
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    level: int
    experience: int
    total_score: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TaskBase(BaseModel):
    title: str
    description: str
    category: str
    difficulty: str
    points: int

class TaskCreate(TaskBase):
    test_data: Optional[dict] = None
    expected_result: Optional[dict] = None
    hints: Optional[List[str]] = None

class TaskResponse(TaskBase):
    id: int
    test_data: Optional[dict] = None
    hints: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TaskSubmission(BaseModel):
    answer: dict
    time_spent: Optional[int] = 0

class TaskResult(BaseModel):
    score: int
    max_score: int
    passed: bool
    feedback: str
    experience_gained: int

class AchievementResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: Optional[str]
    points: int
    category: Optional[str]
    
    class Config:
        from_attributes = True

class UserAchievementResponse(BaseModel):
    id: int
    achievement: AchievementResponse
    earned_at: datetime
    
    class Config:
        from_attributes = True

class ContactMessageCreate(BaseModel):
    name: str
    email: str
    subject: str
    message: str

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    category: str
    in_stock: bool
    stock_quantity: int
    
    class Config:
        from_attributes = True

# Утилиты
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

def evaluate_task(task: TestTask, user_answer: dict) -> tuple[int, str]:
    """Оценивает выполнение задачи пользователем"""
    score = 0
    feedback = []
    
    try:
        expected = json.loads(task.expected_result) if task.expected_result else {}
        
        # Простая проверка соответствия
        if user_answer == expected:
            score = task.points
            feedback.append("Отлично! Задача выполнена правильно.")
        else:
            # Частичная оценка
            score = task.points // 2
            feedback.append("Задача выполнена частично. Проверьте детали.")
        
    except Exception as e:
        feedback.append(f"Ошибка при оценке: {str(e)}")
    
    return score, "; ".join(feedback)

def calculate_level(experience: int) -> int:
    """Вычисляет уровень на основе опыта"""
    return min(experience // 100 + 1, 100)

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Аутентификация
@app.post("/api/auth/register", response_model=Token)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Проверяем существование пользователя
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем уже существует"
        )
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует"
        )
    
    # Создаем пользователя
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Создаем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# Задания
@app.get("/api/tasks", response_model=List[TaskResponse])
async def get_tasks(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(TestTask).filter(TestTask.is_active == True)
    
    if category:
        query = query.filter(TestTask.category == category)
    if difficulty:
        query = query.filter(TestTask.difficulty == difficulty)
    
    tasks = query.all()
    
    # Преобразуем JSON строки в объекты
    result = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "difficulty": task.difficulty,
            "points": task.points,
            "test_data": json.loads(task.test_data) if task.test_data else None,
            "hints": json.loads(task.hints) if task.hints else None,
            "is_active": task.is_active,
            "created_at": task.created_at
        }
        result.append(task_dict)
    
    return result

@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "category": task.category,
        "difficulty": task.difficulty,
        "points": task.points,
        "test_data": json.loads(task.test_data) if task.test_data else None,
        "hints": json.loads(task.hints) if task.hints else None,
        "is_active": task.is_active,
        "created_at": task.created_at
    }

@app.post("/api/tasks/{task_id}/submit", response_model=TaskResult)
async def submit_task(
    task_id: int,
    submission: TaskSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(TestTask).filter(TestTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    
    # Проверяем ответ пользователя
    score, feedback = evaluate_task(task, submission.answer)
    
    # Сохраняем результат
    test_result = TestResult(
        user_id=current_user.id,
        task_id=task_id,
        score=score,
        max_score=task.points,
        passed=score >= task.points * 0.7,  # 70% для прохождения
        user_answer=json.dumps(submission.answer),
        feedback=feedback,
        time_spent=submission.time_spent
    )
    
    db.add(test_result)
    
    # Обновляем прогресс пользователя
    if test_result.passed:
        current_user.experience += score
        current_user.total_score += score
        
        # Проверяем повышение уровня
        new_level = calculate_level(current_user.experience)
        if new_level > current_user.level:
            current_user.level = new_level
    
    db.commit()
    
    return TaskResult(
        score=score,
        max_score=task.points,
        passed=test_result.passed,
        feedback=feedback,
        experience_gained=score if test_result.passed else 0
    )

# Достижения
@app.get("/api/achievements", response_model=List[UserAchievementResponse])
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.id
    ).all()
    
    result = []
    for ua in user_achievements:
        result.append({
            "id": ua.id,
            "achievement": {
                "id": ua.achievement.id,
                "name": ua.achievement.name,
                "description": ua.achievement.description,
                "icon": ua.achievement.icon,
                "points": ua.achievement.points,
                "category": ua.achievement.category
            },
            "earned_at": ua.earned_at
        })
    
    return result

@app.get("/api/achievements/available", response_model=List[AchievementResponse])
async def get_available_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_achievement_ids = [
        ua.achievement_id for ua in 
        db.query(UserAchievement).filter(UserAchievement.user_id == current_user.id).all()
    ]
    
    available_achievements = db.query(Achievement).filter(
        ~Achievement.id.in_(user_achievement_ids)
    ).all()
    
    return available_achievements

# Прогресс обучения
@app.get("/api/progress")
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id
    ).all()
    
    result = []
    for p in progress:
        result.append({
            "id": p.id,
            "category": p.category,
            "level": p.level,
            "experience": p.experience,
            "tasks_completed": p.tasks_completed,
            "last_activity": p.last_activity
        })
    
    return result

# Рейтинг
@app.get("/api/leaderboard")
async def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.total_score.desc()).limit(limit).all()
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "level": user.level,
            "experience": user.experience,
            "total_score": user.total_score,
            "created_at": user.created_at
        })
    
    return result

# Статистика
@app.get("/api/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_tasks = db.query(TestTask).count()
    completed_tasks = db.query(TestResult).filter(
        TestResult.user_id == current_user.id,
        TestResult.passed == True
    ).count()
    
    total_achievements = db.query(Achievement).count()
    user_achievements = db.query(UserAchievement).filter(
        UserAchievement.user_id == current_user.id
    ).count()
    
    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "level": current_user.level,
            "experience": current_user.experience,
            "total_score": current_user.total_score,
            "created_at": current_user.created_at
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        },
        "achievements": {
            "total": total_achievements,
            "earned": user_achievements,
            "earned_rate": (user_achievements / total_achievements * 100) if total_achievements > 0 else 0
        }
    }

# Обратная связь
@app.post("/api/contact")
async def contact(message: ContactMessageCreate, db: Session = Depends(get_db)):
    db_message = ContactMessage(
        name=message.name,
        email=message.email,
        subject=message.subject,
        message=message.message
    )
    
    db.add(db_message)
    db.commit()
    
    return {"message": "Сообщение отправлено успешно"}

# Товары (для тестирования)
@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    
    if category and category != "all":
        query = query.filter(Product.category == category)
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    products = query.all()
    return products

@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return product

# Инициализация базы данных
def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Создаем тестовые данные
        if db.query(Achievement).count() == 0:
            achievements = [
                Achievement(name="Первый шаг", description="Выполните первую задачу", icon="🎯", points=10, category="general"),
                Achievement(name="Функциональный тестер", description="Выполните 5 задач по функциональному тестированию", icon="🔧", points=50, category="functional"),
                Achievement(name="UI Мастер", description="Выполните 5 задач по UI тестированию", icon="🎨", points=50, category="ui"),
                Achievement(name="API Эксперт", description="Выполните 5 задач по API тестированию", icon="🔌", points=50, category="api"),
                Achievement(name="Безопасник", description="Выполните 5 задач по тестированию безопасности", icon="🛡️", points=50, category="security"),
                Achievement(name="Скоростной", description="Выполните задачу менее чем за 30 секунд", icon="⚡", points=25, category="performance"),
                Achievement(name="Перфекционист", description="Выполните задачу на 100%", icon="💯", points=30, category="quality"),
                Achievement(name="Настойчивый", description="Выполните задачу с 3-й попытки", icon="💪", points=20, category="persistence"),
            ]
            for achievement in achievements:
                db.add(achievement)
        
        if db.query(TestTask).count() == 0:
            tasks = [
                TestTask(
                    title="Тестирование формы регистрации",
                    description="Протестируйте форму регистрации на сайте. Найдите все возможные ошибки валидации.",
                    category="functional",
                    difficulty="easy",
                    points=20,
                    test_data=json.dumps({
                        "form_fields": ["username", "email", "password", "confirm_password"],
                        "validation_rules": {
                            "username": {"min_length": 3, "max_length": 20, "required": True},
                            "email": {"format": "email", "required": True},
                            "password": {"min_length": 6, "required": True},
                            "confirm_password": {"match": "password", "required": True}
                        }
                    }),
                    expected_result=json.dumps({
                        "test_cases": [
                            "Пустые поля",
                            "Некорректный email",
                            "Короткий пароль",
                            "Несовпадающие пароли",
                            "Длинное имя пользователя"
                        ]
                    }),
                    hints=json.dumps([
                        "Попробуйте отправить форму с пустыми полями",
                        "Проверьте валидацию email формата",
                        "Попробуйте пароль короче 6 символов"
                    ])
                ),
                TestTask(
                    title="Тестирование API эндпоинта",
                    description="Протестируйте API эндпоинт /api/products. Проверьте различные сценарии запросов.",
                    category="api",
                    difficulty="medium",
                    points=30,
                    test_data=json.dumps({
                        "endpoint": "/api/products",
                        "methods": ["GET"],
                        "parameters": ["category", "search"]
                    }),
                    expected_result=json.dumps({
                        "test_cases": [
                            "GET запрос без параметров",
                            "GET запрос с параметром category",
                            "GET запрос с параметром search",
                            "GET запрос с неверными параметрами"
                        ]
                    }),
                    hints=json.dumps([
                        "Используйте Postman или curl для тестирования",
                        "Проверьте различные значения параметра category",
                        "Попробуйте поиск по несуществующему товару"
                    ])
                ),
                TestTask(
                    title="Тестирование безопасности",
                    description="Проверьте сайт на уязвимости. Попробуйте SQL инъекции и XSS атаки.",
                    category="security",
                    difficulty="hard",
                    points=50,
                    test_data=json.dumps({
                        "target_fields": ["search", "username", "email"],
                        "attack_vectors": ["SQL injection", "XSS", "CSRF"]
                    }),
                    expected_result=json.dumps({
                        "expected_behavior": [
                            "Защита от SQL инъекций",
                            "Экранирование XSS",
                            "CSRF токены"
                        ]
                    }),
                    hints=json.dumps([
                        "Попробуйте ввести ' OR 1=1 -- в поле поиска",
                        "Попробуйте <script>alert('XSS')</script> в текстовых полях",
                        "Проверьте наличие CSRF токенов в формах"
                    ])
                )
            ]
            for task in tasks:
                db.add(task)
        
        if db.query(Product).count() == 0:
            products = [
                Product(name='Смартфон', description='Современный смартфон', price=25000, category='electronics', stock_quantity=10),
                Product(name='Ноутбук', description='Игровой ноутбук', price=75000, category='electronics', stock_quantity=5),
                Product(name='Книга Python', description='Учебник по Python', price=1500, category='books', stock_quantity=20),
                Product(name='Футболка', description='Хлопковая футболка', price=800, category='clothing', stock_quantity=50),
                Product(name='Горшок для цветов', description='Керамический горшок', price=300, category='home', stock_quantity=15),
            ]
            for product in products:
                db.add(product)
        
        db.commit()
        
    finally:
        db.close()

# Подключение дополнительных эндпоинтов
from api_extensions import router as extensions_router
app.include_router(extensions_router)

# Инициализация при запуске
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
