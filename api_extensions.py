# Дополнительные API эндпоинты для FastAPI

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json

from main import (
    get_db, get_current_user, User, TestResult, TestTask, 
    Achievement, UserAchievement, LearningProgress
)

# Создаем роутер для дополнительных эндпоинтов
router = APIRouter(prefix="/api", tags=["extensions"])

# Дополнительные эндпоинты для пользователей
@router.get("/user/activity")
async def get_user_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение последней активности пользователя"""
    # Получаем последние результаты тестов
    recent_results = db.query(TestResult).filter_by(user_id=current_user.id)\
        .order_by(TestResult.completed_at.desc())\
        .limit(10).all()
    
    activity = []
    for result in recent_results:
        task = db.query(TestTask).get(result.task_id)
        activity.append({
            'id': result.id,
            'task_id': result.task_id,
            'task_title': task.title if task else f'Задание #{result.task_id}',
            'score': result.score,
            'max_score': result.max_score,
            'passed': result.passed,
            'completed_at': result.completed_at.isoformat(),
            'time_spent': result.time_spent
        })
    
    return activity

@router.get("/user/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение расширенного профиля пользователя"""
    # Статистика по категориям
    category_stats = {}
    categories = ['functional', 'ui', 'api', 'security']
    
    for category in categories:
        results = db.query(TestResult).join(TestTask).filter(
            TestResult.user_id == current_user.id,
            TestTask.category == category,
            TestResult.passed == True
        ).all()
        
        category_stats[category] = {
            'completed': len(results),
            'total_score': sum(r.score for r in results),
            'average_score': sum(r.score for r in results) / len(results) if results else 0
        }
    
    return {
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'level': current_user.level,
            'experience': current_user.experience,
            'total_score': current_user.total_score,
            'created_at': current_user.created_at
        },
        'category_stats': category_stats,
        'total_tasks_completed': db.query(TestResult).filter_by(user_id=current_user.id, passed=True).count(),
        'total_time_spent': sum(r.time_spent or 0 for r in db.query(TestResult).filter_by(user_id=current_user.id).all()),
        'average_attempts': sum(r.attempts for r in db.query(TestResult).filter_by(user_id=current_user.id).all()) / 
                           max(db.query(TestResult).filter_by(user_id=current_user.id).count(), 1)
    }

@router.put("/user/profile")
async def update_user_profile(
    username: Optional[str] = None,
    email: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление профиля пользователя"""
    # Обновляем только разрешенные поля
    if username and username != current_user.username:
        # Проверяем уникальность
        existing_user = db.query(User).filter_by(username=username).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Имя пользователя уже занято"
            )
        current_user.username = username
    
    if email and email != current_user.email:
        # Проверяем уникальность
        existing_user = db.query(User).filter_by(email=email).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email уже используется"
            )
        current_user.email = email
    
    db.commit()
    
    return {
        'message': 'Профиль обновлен успешно',
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'level': current_user.level,
            'experience': current_user.experience,
            'total_score': current_user.total_score,
            'created_at': current_user.created_at
        }
    }

# Эндпоинты для достижений
@router.post("/achievements/check")
async def check_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Проверка и выдача достижений пользователю"""
    new_achievements = []
    
    # Проверяем различные условия для достижений
    achievements_to_check = [
        {
            'id': 1,
            'condition': lambda: db.query(TestResult).filter_by(user_id=current_user.id, passed=True).count() >= 1,
            'name': 'Первый шаг'
        },
        {
            'id': 2,
            'condition': lambda: db.query(TestResult).join(TestTask).filter(
                TestResult.user_id == current_user.id,
                TestTask.category == 'functional',
                TestResult.passed == True
            ).count() >= 5,
            'name': 'Функциональный тестер'
        },
        {
            'id': 3,
            'condition': lambda: db.query(TestResult).join(TestTask).filter(
                TestResult.user_id == current_user.id,
                TestTask.category == 'ui',
                TestResult.passed == True
            ).count() >= 5,
            'name': 'UI Мастер'
        },
        {
            'id': 4,
            'condition': lambda: db.query(TestResult).join(TestTask).filter(
                TestResult.user_id == current_user.id,
                TestTask.category == 'api',
                TestResult.passed == True
            ).count() >= 5,
            'name': 'API Эксперт'
        },
        {
            'id': 5,
            'condition': lambda: db.query(TestResult).join(TestTask).filter(
                TestResult.user_id == current_user.id,
                TestTask.category == 'security',
                TestResult.passed == True
            ).count() >= 5,
            'name': 'Безопасник'
        },
        {
            'id': 6,
            'condition': lambda: db.query(TestResult).filter_by(
                user_id=current_user.id,
                passed=True
            ).filter(TestResult.time_spent <= 30).count() >= 1,
            'name': 'Скоростной'
        },
        {
            'id': 7,
            'condition': lambda: db.query(TestResult).filter_by(
                user_id=current_user.id,
                passed=True
            ).filter(TestResult.score == TestResult.max_score).count() >= 1,
            'name': 'Перфекционист'
        },
        {
            'id': 8,
            'condition': lambda: db.query(TestResult).filter_by(
                user_id=current_user.id,
                attempts=3,
                passed=True
            ).count() >= 1,
            'name': 'Настойчивый'
        }
    ]
    
    for achievement_check in achievements_to_check:
        # Проверяем, есть ли уже это достижение у пользователя
        existing = db.query(UserAchievement).filter_by(
            user_id=current_user.id,
            achievement_id=achievement_check['id']
        ).first()
        
        if not existing and achievement_check['condition']():
            # Выдаем достижение
            user_achievement = UserAchievement(
                user_id=current_user.id,
                achievement_id=achievement_check['id']
            )
            db.add(user_achievement)
            
            # Получаем информацию о достижении
            achievement = db.query(Achievement).get(achievement_check['id'])
            if achievement:
                new_achievements.append({
                    'id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'icon': achievement.icon,
                    'points': achievement.points,
                    'category': achievement.category
                })
                
                # Добавляем очки пользователю
                current_user.experience += achievement.points
                current_user.total_score += achievement.points
    
    db.commit()
    
    return {
        'new_achievements': new_achievements,
        'total_achievements': len(new_achievements)
    }

# Эндпоинты для аналитики
@router.get("/analytics/overview")
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение общей аналитики платформы"""
    # Статистика пользователя
    user_stats = {
        'total_tasks': db.query(TestTask).count(),
        'completed_tasks': db.query(TestResult).filter_by(user_id=current_user.id, passed=True).count(),
        'total_score': current_user.total_score,
        'level': current_user.level,
        'experience': current_user.experience
    }
    
    # Статистика по категориям
    category_stats = {}
    for category in ['functional', 'ui', 'api', 'security']:
        category_tasks = db.query(TestTask).filter_by(category=category).count()
        completed_tasks = db.query(TestResult).join(TestTask).filter(
            TestResult.user_id == current_user.id,
            TestTask.category == category,
            TestResult.passed == True
        ).count()
        
        category_stats[category] = {
            'total': category_tasks,
            'completed': completed_tasks,
            'completion_rate': (completed_tasks / category_tasks * 100) if category_tasks > 0 else 0
        }
    
    # Временная статистика (последние 30 дней)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_activity = db.query(TestResult).filter(
        TestResult.user_id == current_user.id,
        TestResult.completed_at >= thirty_days_ago
    ).count()
    
    return {
        'user_stats': user_stats,
        'category_stats': category_stats,
        'recent_activity': recent_activity,
        'last_30_days': recent_activity
    }

@router.get("/analytics/performance")
async def get_performance_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение аналитики производительности"""
    # Среднее время выполнения заданий
    results = db.query(TestResult).filter_by(user_id=current_user.id).all()
    avg_time = sum(r.time_spent or 0 for r in results) / len(results) if results else 0
    
    # Процент успешных попыток
    total_attempts = len(results)
    successful_attempts = len([r for r in results if r.passed])
    success_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0
    
    # Средний балл
    avg_score = sum(r.score for r in results) / len(results) if results else 0
    
    # Статистика по сложности
    difficulty_stats = {}
    for difficulty in ['easy', 'medium', 'hard']:
        difficulty_results = db.query(TestResult).join(TestTask).filter(
            TestResult.user_id == current_user.id,
            TestTask.difficulty == difficulty
        ).all()
        
        if difficulty_results:
            difficulty_stats[difficulty] = {
                'total': len(difficulty_results),
                'passed': len([r for r in difficulty_results if r.passed]),
                'avg_score': sum(r.score for r in difficulty_results) / len(difficulty_results),
                'avg_time': sum(r.time_spent or 0 for r in difficulty_results) / len(difficulty_results)
            }
    
    return {
        'avg_time_spent': avg_time,
        'success_rate': success_rate,
        'avg_score': avg_score,
        'difficulty_stats': difficulty_stats,
        'total_attempts': total_attempts,
        'successful_attempts': successful_attempts
    }

# Эндпоинты для социальных функций
@router.post("/social/follow")
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Подписка на пользователя"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Нельзя подписаться на себя"
        )
    
    # Проверяем существование пользователя
    target_user = db.query(User).get(user_id)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )
    
    # Здесь можно добавить логику подписки
    # Для простоты просто возвращаем успех
    
    return {
        'message': f'Вы подписались на {target_user.username}',
        'following': True
    }

@router.get("/social/feed")
async def get_social_feed(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение ленты активности"""
    # Получаем последние достижения всех пользователей
    recent_achievements = db.query(UserAchievement, User, Achievement)\
        .join(User, UserAchievement.user_id == User.id)\
        .join(Achievement, UserAchievement.achievement_id == Achievement.id)\
        .order_by(UserAchievement.earned_at.desc())\
        .limit(20).all()
    
    feed = []
    for user_achievement, user, achievement in recent_achievements:
        feed.append({
            'type': 'achievement',
            'user': {
                'id': user.id,
                'username': user.username,
                'level': user.level
            },
            'achievement': {
                'id': achievement.id,
                'name': achievement.name,
                'description': achievement.description,
                'icon': achievement.icon,
                'points': achievement.points,
                'category': achievement.category
            },
            'timestamp': user_achievement.earned_at.isoformat()
        })
    
    return feed

# Эндпоинты для уведомлений
@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение уведомлений пользователя"""
    # Здесь можно добавить систему уведомлений
    # Для простоты возвращаем пустой список
    
    return []

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Отметка уведомления как прочитанного"""
    # Здесь можно добавить логику отметки уведомлений
    
    return {'message': 'Уведомление отмечено как прочитанное'}

# Эндпоинты для поиска
@router.get("/search")
async def search(
    q: str,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Поиск по платформе"""
    if not q:
        raise HTTPException(
            status_code=400,
            detail="Не указан поисковый запрос"
        )
    
    results = {
        'tasks': [],
        'users': [],
        'achievements': []
    }
    
    # Поиск заданий
    tasks = db.query(TestTask).filter(
        TestTask.title.contains(q) | TestTask.description.contains(q)
    ).limit(10).all()
    
    for task in tasks:
        results['tasks'].append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'category': task.category,
            'difficulty': task.difficulty,
            'points': task.points,
            'test_data': json.loads(task.test_data) if task.test_data else None,
            'hints': json.loads(task.hints) if task.hints else None,
            'is_active': task.is_active,
            'created_at': task.created_at
        })
    
    # Поиск пользователей
    users = db.query(User).filter(User.username.contains(q)).limit(10).all()
    
    for user in users:
        results['users'].append({
            'id': user.id,
            'username': user.username,
            'level': user.level,
            'total_score': user.total_score
        })
    
    # Поиск достижений
    achievements = db.query(Achievement).filter(
        Achievement.name.contains(q) | Achievement.description.contains(q)
    ).limit(10).all()
    
    for achievement in achievements:
        results['achievements'].append({
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon,
            'points': achievement.points,
            'category': achievement.category
        })
    
    return results