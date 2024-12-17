import psycopg
from werkzeug.security import check_password_hash
from flask import render_template, redirect, flash, url_for
from flask_login import login_user, current_user, logout_user
from app import app
from app.forms import *
from app.user import User

@app.route('/', methods=['GET', 'POST'])
def index():
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        airports = cur.execute('SELECT code, city FROM public.airport').fetchall()
        get_flights_form = flight_search()
        
        departure_choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in airports]
        get_flights_form.depature.choices = departure_choices
        
        arrival_choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in airports]
        get_flights_form.arrival.choices = arrival_choices
        
        if get_flights_form.date.data is None:
            get_flights = cur.execute('SELECT * FROM public.flight WHERE departure = %s AND arrival = %s',(get_flights_form.depature.data, get_flights_form.arrival.data))
        else:
            get_flights = cur.execute('SELECT * FROM public.flight WHERE departure = %s AND arrival = %s AND DATE("departure datetime") = %s',(get_flights_form.depature.data, get_flights_form.arrival.data, get_flights_form.date.data))
        get_flights=get_flights.fetchall()
        return render_template('index.html', title='Главная', form = get_flights_form, search_bool = True, flights = get_flights)
        
    return render_template('index.html', title='Главная', form = get_flights_form, search_bool = False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT id, username, password '
                              'FROM public."admin" '
                              'WHERE username = %s', (login_form.username.data,)).fetchone()
        if res is None or res[2] != login_form.password.data:
            flash('Попытка входа неудачна', 'danger')
            return redirect(url_for('login'))
        id, username, password = res
        user = User(id, username, password)
        login_user(user, remember=login_form.remember_me.data)
        flash(f'Вы успешно вошли в систему, {current_user.username}', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', title='Вход', form=login_form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    interface = adminInterface()
    if interface.models.data:
        return redirect(url_for('models'))
    return render_template('admin/interface.html', title='Панель админа', form=interface)

@app.route('/admin/models', methods=['GET', 'POST'])
def models():
    model_form = adminModels()
    if model_form.show_flights.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT * FROM public."plane model"')
            res = res.fetchall()
        return render_template('admin/models.html', title='Редактирование моделей самолета', form=model_form, plane_models = res, search_bool = True)
    if model_form.add.data:
        if not model_form.name.data:
            flash('Название не может быть пустым!', 'danger')
        elif model_form.economy.data == 0 and model_form.buisness.data == 0 and model_form.first.data == 0:
            flash('Все места не могут быть 0!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."plane model" WHERE name = %s', (model_form.name.data,)).fetchone()
                if res:
                    flash('Такая модель уже есть!', 'danger')
                else:
                    try:
                        cur.execute('INSERT INTO public."plane model" VALUES (%s, %s, %s, %s)',
                                    (model_form.name.data, model_form.economy.data,model_form.buisness.data,model_form.first.data))
                        flash('Модель успешно добавлена', 'success')
                    except Exception as e:
                        flash('Ошибка {e}', 'danger')
                        con.rollback
    return render_template('admin/models.html', title='Редактирование моделей самолета', form=model_form, search_bool = False)