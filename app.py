from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import secrets
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///test_website.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = secrets.token_hex(16)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Инициализация расширений
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, origins=['http://localhost:3000', 'https://your-frontend.vercel.app'])

# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)
    
    # Связи
    achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    test_results = db.relationship('TestResult', backref='user', lazy=True)
    learning_progress = db.relationship('LearningProgress', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'level': self.level,
            'experience': self.experience,
            'total_score': self.total_score,
            'created_at': self.created_at.isoformat()
        }

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    points = db.Column(db.Integer, default=10)
    category = db.Column(db.String(50))  # testing, security, ui, api
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'points': self.points,
            'category': self.category
        }

class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'achievement': self.achievement.to_dict(),
            'earned_at': self.earned_at.isoformat()
        }

class TestTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # functional, ui, api, security
    difficulty = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    points = db.Column(db.Integer, default=10)
    test_data = db.Column(db.Text)  # JSON с тестовыми данными
    expected_result = db.Column(db.Text)  # JSON с ожидаемым результатом
    hints = db.Column(db.Text)  # JSON с подсказками
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'points': self.points,
            'test_data': json.loads(self.test_data) if self.test_data else None,
            'hints': json.loads(self.hints) if self.hints else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('test_task.id'), nullable=False)
    score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=0)
    passed = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=1)
    time_spent = db.Column(db.Integer)  # в секундах
    user_answer = db.Column(db.Text)  # JSON с ответом пользователя
    feedback = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'score': self.score,
            'max_score': self.max_score,
            'passed': self.passed,
            'attempts': self.attempts,
            'time_spent': self.time_spent,
            'user_answer': json.loads(self.user_answer) if self.user_answer else None,
            'feedback': self.feedback,
            'completed_at': self.completed_at.isoformat()
        }

class LearningProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'level': self.level,
            'experience': self.experience,
            'tasks_completed': self.tasks_completed,
            'last_activity': self.last_activity.isoformat()
        }

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    in_stock = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=0)

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# Аутентификация
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Необходимы username, email и password'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Пользователь с таким именем уже существует'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Пользователь успешно зарегистрирован',
        'access_token': access_token,
        'user': user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Необходимы username и password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'message': 'Успешный вход в систему',
            'access_token': access_token,
            'user': user.to_dict()
        })
    
    return jsonify({'error': 'Неверные учетные данные'}), 401

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    return jsonify(user.to_dict())

# Задачи для тестирования
@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    
    query = TestTask.query.filter_by(is_active=True)
    
    if category:
        query = query.filter_by(category=category)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    tasks = query.all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    task = TestTask.query.get_or_404(task_id)
    return jsonify(task.to_dict())

@app.route('/api/tasks/<int:task_id>/submit', methods=['POST'])
@jwt_required()
def submit_task(task_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    
    task = TestTask.query.get_or_404(task_id)
    
    # Проверяем ответ пользователя
    score, feedback = evaluate_task(task, data.get('answer', {}))
    
    # Сохраняем результат
    test_result = TestResult(
        user_id=user_id,
        task_id=task_id,
        score=score,
        max_score=task.points,
        passed=score >= task.points * 0.7,  # 70% для прохождения
        user_answer=json.dumps(data.get('answer', {})),
        feedback=feedback,
        time_spent=data.get('time_spent', 0)
    )
    
    db.session.add(test_result)
    
    # Обновляем прогресс пользователя
    user = User.query.get(user_id)
    if test_result.passed:
        user.experience += score
        user.total_score += score
        
        # Проверяем повышение уровня
        new_level = calculate_level(user.experience)
        if new_level > user.level:
            user.level = new_level
            # Здесь можно добавить уведомление о повышении уровня
    
    db.session.commit()
    
    return jsonify({
        'score': score,
        'max_score': task.points,
        'passed': test_result.passed,
        'feedback': feedback,
        'experience_gained': score if test_result.passed else 0
    })

def evaluate_task(task, user_answer):
    """Оценивает выполнение задачи пользователем"""
    # Базовая логика оценки - можно расширить
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

def calculate_level(experience):
    """Вычисляет уровень на основе опыта"""
    return min(experience // 100 + 1, 100)  # Максимум 100 уровень

# Достижения
@app.route('/api/achievements', methods=['GET'])
@jwt_required()
def get_achievements():
    user_id = get_jwt_identity()
    user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()
    return jsonify([ua.to_dict() for ua in user_achievements])

@app.route('/api/achievements/available', methods=['GET'])
@jwt_required()
def get_available_achievements():
    user_id = get_jwt_identity()
    user_achievement_ids = [ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=user_id).all()]
    available_achievements = Achievement.query.filter(~Achievement.id.in_(user_achievement_ids)).all()
    return jsonify([achievement.to_dict() for achievement in available_achievements])

# Прогресс обучения
@app.route('/api/progress', methods=['GET'])
@jwt_required()
def get_progress():
    user_id = get_jwt_identity()
    progress = LearningProgress.query.filter_by(user_id=user_id).all()
    return jsonify([p.to_dict() for p in progress])

# Рейтинг
@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    limit = request.args.get('limit', 10, type=int)
    users = User.query.order_by(User.total_score.desc()).limit(limit).all()
    return jsonify([user.to_dict() for user in users])

# Статистика
@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    total_tasks = TestTask.query.count()
    completed_tasks = TestResult.query.filter_by(user_id=user_id, passed=True).count()
    total_achievements = Achievement.query.count()
    user_achievements = UserAchievement.query.filter_by(user_id=user_id).count()
    
    return jsonify({
        'user': user.to_dict(),
        'tasks': {
            'total': total_tasks,
            'completed': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        },
        'achievements': {
            'total': total_achievements,
            'earned': user_achievements,
            'earned_rate': (user_achievements / total_achievements * 100) if total_achievements > 0 else 0
        }
    })

# Обратная связь
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    
    if not data or not all(k in data for k in ['name', 'email', 'subject', 'message']):
        return jsonify({'error': 'Необходимы все поля'}), 400
    
    message = ContactMessage(
        name=data['name'],
        email=data['email'],
        subject=data['subject'],
        message=data['message']
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'message': 'Сообщение отправлено успешно'}), 201

# Товары (для тестирования)
@app.route('/api/products', methods=['GET'])
def get_products():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    query = Product.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(Product.name.contains(search))
    
    products = query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'category': p.category,
        'in_stock': p.in_stock,
        'stock_quantity': p.stock_quantity
    } for p in products])

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'category': product.category,
        'in_stock': product.in_stock,
        'stock_quantity': product.stock_quantity
    })

# Инициализация базы данных
def init_db():
    with app.app_context():
        db.create_all()
        
        # Создаем тестовые данные
        if Achievement.query.count() == 0:
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
                db.session.add(achievement)
        
        if TestTask.query.count() == 0:
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
                db.session.add(task)
        
        if Product.query.count() == 0:
            products = [
                Product(name='Смартфон', description='Современный смартфон', price=25000, category='electronics', stock_quantity=10),
                Product(name='Ноутбук', description='Игровой ноутбук', price=75000, category='electronics', stock_quantity=5),
                Product(name='Книга Python', description='Учебник по Python', price=1500, category='books', stock_quantity=20),
                Product(name='Футболка', description='Хлопковая футболка', price=800, category='clothing', stock_quantity=50),
                Product(name='Горшок для цветов', description='Керамический горшок', price=300, category='home', stock_quantity=15),
            ]
            for product in products:
                db.session.add(product)
        
        db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
