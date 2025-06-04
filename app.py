from flask import Flask, session, render_template, redirect, request, url_for
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_admin.menu import MenuLink
from flask_babel import Babel
from utils.nutrition import calculate_nutrition
import matplotlib.pyplot as plt
import os
import matplotlib

from Db import db
from Db.models import User, Workout, TrainingPlan, Step, Article


app = Flask(__name__)

# Конфигурация
app.secret_key = 'NGTU'

user_db = "admin"
host_ip = "127.0.0.1"
host_port = "5432"
database_name = "project_zoj"
password = "theWeekend"

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{user_db}:{password}@{host_ip}:{host_port}/{database_name}'
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['BABEL_DEFAULT_LOCALE'] = 'ru'


# Инициализация
migrate = Migrate(app, db)
db.init_app(app)
babel = Babel(app)


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


# Функция для загрузки пользователя из сессии
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Админка только для админов
class AdminOnlyView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('loginPage'))

    # Локализация интерфейса
    def get_create_button_text(self):
        return "Создать"

    def get_edit_button_text(self):
        return "Изменить"

    def get_delete_button_text(self):
        return "Удалить"

    def get_save_button_text(self):
        return "Сохранить"

    def get_cancel_button_text(self):
        return "Отмена"

    def get_list_title(self):
        return "Список записей"

    def get_create_title(self):
        return "Создание записи"

    def get_edit_title(self):
        return "Редактирование"


class UserAdmin(AdminOnlyView):
    column_labels = {
        'id': 'ID',
        'name': 'Имя',
        'username': 'Логин',
        'is_admin': 'Администратор'
    }
    column_exclude_list = ['password']


class WorkoutAdmin(AdminOnlyView):
    column_labels = {
        'date': 'Дата',
        'type': 'Тип тренировки',
        'duration_minutes': 'Длительность (мин)',
        'calories_burned': 'Сожжено калорий'
    }


class TrainingPlanAdmin(AdminOnlyView):
    column_labels = {
        'name': 'Название',
        'description': 'Описание',
        'level': 'Уровень'
    }


class ArticleAdmin(AdminOnlyView):
    column_labels = {
        'title': 'Заголовок',
        'content': 'Содержимое',
        'created_at': 'Дата создания'
    }
    form_widget_args = {
        'content': {'rows': 10}
    }


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        user_count = User.query.count()
        workout_count = Workout.query.count()
        plan_count = TrainingPlan.query.count()

        return self.render('admin/index.html',
                           user_count=user_count,
                           workout_count=workout_count,
                           plan_count=plan_count)


admin = Admin(
    app,
    name='FitLife админка',
    index_view=MyAdminIndexView(name='Главная'),
    template_mode='bootstrap4'
)


admin.add_link(MenuLink(name='🏠 На главную', url='/app/index/'))
admin.add_view(UserAdmin(User, db.session, name='Пользователи'))
admin.add_view(TrainingPlanAdmin(TrainingPlan, db.session, name='Планы тренировок'))
admin.add_view(ArticleAdmin(Article, db.session, name='Статьи'))


@app.route('/')
def start():
    return redirect(url_for('main'))


@app.route("/app/index/", methods=['GET', 'POST'])
def main():
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    user = User.query.get(session['id'])
    return render_template('index.html', username=user.username, is_admin=user.is_admin)


@app.route('/app/register', methods=['GET', 'POST'])
def registerPage():
    errors = []
    if request.method == 'GET':
        return render_template("register.html", errors=errors)

    username = request.form.get("username")
    password = request.form.get("password")

    if not (username and password):
        errors.append("Пожалуйста, заполните все поля")
        return render_template("register.html", errors=errors)

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        errors.append('Пользователь с данным именем уже существует')
        return render_template('register.html', errors=errors)

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return redirect("/app/login")


@app.route('/app/login', methods=["GET", "POST"])
def loginPage():
    errors = []
    if request.method == 'GET':
        return render_template("login.html", errors=errors)

    username = request.form.get("username")
    password = request.form.get("password")

    if not (username and password):
        errors.append("Пожалуйста, заполните все поля")
        return render_template("login.html", errors=errors)

    user = User.query.filter_by(username=username).first()
    if user is None or not check_password_hash(user.password, password):
        errors.append('Неправильный пользователь или пароль')
        return render_template("login.html", errors=errors)

    session['id'] = user.id
    session['username'] = user.username

    login_user(user)

    return redirect("/app/index/")


@app.route('/app/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('loginPage'))


@app.route('/app/profile', methods=['GET', 'POST'])
def user_profile():
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    user = User.query.get(session['id'])

    if request.method == 'POST':
        user.gender = request.form.get('gender')
        user.age = request.form.get('age')
        user.height_cm = request.form.get('height_cm')
        user.weight_kg = request.form.get('weight_kg')
        user.goal = request.form.get('goal')
        user.activity_level = request.form.get('activity_level')
        db.session.commit()
        return redirect(url_for('user_profile'))

    return render_template('profile.html', user=user)


@app.route('/app/steps', methods=['GET', 'POST'])
def steps():
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    user = User.query.get(session['id'])

    if request.method == 'POST':
        date = request.form.get('date')
        step_count = request.form.get('steps')

        step = Step(user_id=user.id, date=datetime.strptime(date, '%Y-%m-%d'), steps=int(step_count))
        db.session.add(step)
        db.session.commit()
        return redirect(url_for('steps'))

    history = Step.query.filter_by(user_id=user.id).order_by(Step.date.desc()).all()
    return render_template('steps.html', steps=history)


@app.route('/app/nutrition')
def nutrition_recommendation():
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    user = User.query.get(session['id'])
    if not all([user.age, user.height_cm, user.weight_kg, user.goal]):
        return redirect(url_for('user_profile'))  # попросим заполнить профиль

    nutrition = calculate_nutrition(user)
    return render_template('nutrition.html', nutrition=nutrition)


@app.route('/app/trainings', methods=['GET', 'POST'])
def trainings():
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    user = User.query.get(session['id'])

    # Фильтрация тренировок по типу
    filter_type = request.args.get('type')
    if filter_type:
        workouts = Workout.query.filter_by(user_id=user.id, type=filter_type).order_by(Workout.date.desc()).all()
    else:
        workouts = Workout.query.filter_by(user_id=user.id).order_by(Workout.date.desc()).all()

    # Загрузка планов
    plans = TrainingPlan.query.filter_by(is_global=True).all()

    # Обработка создания тренировки
    if request.method == 'POST':
        if 'type' in request.form:
            workout_type = request.form.get('type')
            if workout_type == 'custom':
                workout_type = request.form.get('custom_type')

            date = request.form.get('date')
            duration = int(request.form.get('duration'))

            calories_burned = duration * 5

            new = Workout(
                user_id=user.id,
                type=workout_type,
                date=date,
                duration_minutes=duration,
                calories_burned=calories_burned
            )
            db.session.add(new)
            db.session.commit()
            return redirect(url_for('trainings'))

        elif 'title' in request.form:
            title = request.form['title']
            description = request.form['description']
            new_plan = TrainingPlan(user_id=user.id, title=title, description=description)
            db.session.add(new_plan)
            db.session.commit()
            return redirect(url_for('trainings'))

    return render_template('trainings.html', workouts=workouts, filter_type=filter_type, plans=plans)


@app.route('/workouts/new', methods=['GET', 'POST'])
def new_workout():
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    if request.method == 'POST':
        user = User.query.get(session['id'])
        workout_type = request.form.get('type')
        date = request.form.get('date')
        duration = int(request.form.get('duration'))

        calories_burned = duration * 5

        new = Workout(
            user_id=user.id,
            type=workout_type,
            date=date,
            duration_minutes=duration,
            calories_burned=calories_burned
        )
        db.session.add(new)
        db.session.commit()

        return redirect(url_for('trainings'))

    return render_template('new_workout.html')


@app.route('/workouts/edit/<int:workout_id>', methods=['GET', 'POST'])
def edit_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if 'id' not in session or workout.user_id != session['id']:
        return redirect(url_for('trainings'))

    if request.method == 'POST':
        workout.type = request.form.get('type')
        workout.date = request.form.get('date')
        workout.duration_minutes = int(request.form.get('duration'))

        met_values = {"Бег": 10, "Силовая": 6, "Йога": 2.5, "Велотренажёр": 7, "Плавание": 8}
        met = met_values.get(workout.type, 5)
        user = User.query.get(workout.user_id)
        weight = user.weight_kg or 70
        duration_hours = workout.duration_minutes / 60
        workout.calories_burned = round(met * weight * duration_hours)

        db.session.commit()
        return redirect(url_for('trainings'))

    return render_template('edit_workout.html', workout=workout)


@app.route('/workouts/delete/<int:workout_id>')
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if 'id' not in session or workout.user_id != session['id']:
        return redirect(url_for('trainings'))

    db.session.delete(workout)
    db.session.commit()
    return redirect(url_for('trainings'))


@app.route('/steps/edit/<int:id>', methods=['GET', 'POST'])
def edit_steps(id):
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    step = Step.query.filter_by(id=id, user_id=session['id']).first_or_404()

    if request.method == 'POST':
        step.date = request.form['date']
        step.steps = int(request.form['steps'])
        db.session.commit()
        return redirect(url_for('steps'))

    return render_template('edit_steps.html', step=step)


@app.route('/steps/delete/<int:id>')
def delete_steps(id):
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    step = Step.query.filter_by(id=id, user_id=session['id']).first_or_404()
    db.session.delete(step)
    db.session.commit()
    return redirect(url_for('steps'))


@app.route('/stats')
def stats():
    if 'id' not in session:
        return redirect(url_for('loginPage'))

    user_id = session['id']
    user = User.query.get(user_id)

    matplotlib.use('Agg')  # Используем без GUI

    workouts = Workout.query.filter_by(user_id=user_id).order_by(Workout.date).all()
    total_workouts = len(workouts)
    total_minutes = sum(w.duration_minutes for w in workouts)
    total_calories = sum(w.calories_burned for w in workouts)
    active_days = len(set(w.date for w in workouts))

    type_counts = {}
    for w in workouts:
        type_counts[w.type] = type_counts.get(w.type, 0) + 1

    if type_counts:
        labels, values = zip(*type_counts.items())

        plt.figure(figsize=(8, 5))
        plt.bar(labels, values, color='#6b69b3', edgecolor='black')

        plt.title("Распределение типов тренировок", fontsize=14, fontweight='bold')
        plt.xlabel("Тип", fontsize=12)
        plt.ylabel("Количество", fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()

        type_path = os.path.join("static", "workout_types.png")
        plt.savefig(type_path)
        plt.close()
    else:
        type_path = None

    # Шаги
    steps = Step.query.filter_by(user_id=user_id).all()
    total_steps = sum(s.steps for s in steps)

    return render_template(
        "stats.html",
        username=user.username,
        total_workouts=total_workouts,
        total_minutes=total_minutes,
        total_calories=total_calories,
        total_steps=total_steps,
        active_days=active_days,
        type_chart=type_path
    )


@app.route('/plans/<int:plan_id>')
def view_plan(plan_id):
    plan = TrainingPlan.query.get_or_404(plan_id)
    return render_template('view_plan.html', plan=plan)


@app.route('/articles')
def articles():
    all_articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('articles.html', articles=all_articles)


@app.route('/articles/<int:article_id>')
def view_article(article_id):
    article = Article.query.get_or_404(article_id)
    return render_template('article_detail.html', article=article)


@app.route('/plans')
@login_required
def view_plans():
    user_plans = TrainingPlan.query.filter_by(user_id=current_user.id).all()
    global_plans = TrainingPlan.query.filter_by(is_global=True).all()

    plans = user_plans + global_plans
    return render_template('plans.html', plans=plans)


# Для хоста
'''if os.environ.get("RENDER") == "true":
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


with app.app_context():
    existing = User.query.filter_by(username="Admin").first()
    if not existing:
        user = User(
            username="Admin",
            password=generate_password_hash("123"),
            is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        print("Пользователь Wonderwol создан и назначен админом.")
    else:
        print("Пользователь уже существует.")'''
