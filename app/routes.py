import psycopg, re
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, flash, url_for, abort, request
from flask_login import login_user, current_user, logout_user, login_required
from app import app
from app.forms import *
from app.user import User
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from wtforms.validators import InputRequired, Optional

# Стартовая станица
@app.route('/', methods=['GET', 'POST'])
def index():
    get_flights_form = flight_search()

    query = '''
            SELECT 
                f."number", 
                f."plane number",
	            f."departure",
	            f."arrival",
	            f."departure datetime",
	            f."arrival datetime",
	            f."status",
	            f."economy price",
	            f."business price",
	            f."first price",
	            m."name",
	            dep."city" as "departure city",
	            c_dep."name" as "departure country",
	            arr."city" as "arrival city",
	            c_arr."name" as "arrival country",
                m."economy class" - COUNT(CASE WHEN b."type" = 0 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END) AS economy_count, 
                m."business class" - COUNT(CASE WHEN b."type" = 1 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END) AS business_count, 
                m."first class" - COUNT(CASE WHEN b."type" = 2 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END) AS first_count,
                c_arr."visa"  
            FROM public."flight" AS f
            LEFT JOIN public."plane" AS p
                ON f."plane number" = p."number"
            LEFT JOIN public."plane model" AS m
                ON p."model" = m."name"
            LEFT JOIN public."booking" AS b
                ON f."number" = b."flight"
            LEFT JOIN public."airport" as arr
	            ON f."arrival" = arr."code"
            LEFT JOIN public."airport" as dep
	            ON f."departure" = dep."code"
            LEFT JOIN public."city" as city_arr
	            ON arr."city" = city_arr."name"
            LEFT JOIN public."city" as city_dep
	            ON dep."city" = city_dep."name"
            LEFT JOIN public."country" as c_arr
	            ON city_arr."country" = c_arr."name"
            LEFT JOIN public."country" as c_dep
	            ON city_dep."country" = c_dep."name"
            WHERE f."departure" = %s 
            AND f."arrival" = %s 
            AND DATE(f."departure datetime") = %s
            AND (f."status" = 0 OR f."status" = 2)
            AND f."number" NOT IN (  -- исключаем рейсы с бронями для текущего пользователя
                SELECT b."flight" 
                FROM public."booking" AS b 
                WHERE b."passenger" = %s  -- ID текущего пользователя
            )
            GROUP BY f."number", m."economy class", m."business class", m."first class", m."name", arr."city", dep."city", c_dep."name", c_arr."name", c_arr."visa"
            HAVING 
                (m."economy class" - COUNT(CASE WHEN b."type" = 0 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END)) != 0 OR 
                (m."business class" - COUNT(CASE WHEN b."type" = 1 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END)) != 0 OR 
                (m."first class" - COUNT(CASE WHEN b."type" = 2 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END)) != 0
            ORDER BY 
                LEAST(
                    CASE WHEN f."economy price" > 0 THEN f."economy price" ELSE NULL END,
                    CASE WHEN f."business price" > 0 THEN f."business price" ELSE NULL END,
                    CASE WHEN f."first price" > 0 THEN f."first price" ELSE NULL END
                ) {sort}
            '''
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        # Получение данных об аэропортах
        airports = cur.execute('SELECT code, city FROM public.airport').fetchall()
        get_flights_form.departure.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in airports]
        get_flights_form.arrival.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in airports]
        # Если убрана галочка, второе поле с датой не обязательно
    if not get_flights_form.ret_ticket.data:
        get_flights_form.second_date.validators = [Optional()]
    else:
        get_flights_form.second_date.validators = [InputRequired()]
    # Поиск рейсов
    if get_flights_form.submit.data and get_flights_form.validate_on_submit():
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            # Сортировка
            if get_flights_form.choice.data == 'up':
                query = query.format(sort = 'ASC')
            else:
                query = query.format(sort = 'DESC')
            if current_user.is_authenticated:
                id = current_user.id
            else:
                id = -1
            # Получение рейсов
            get_flights_first = cur.execute(query,(get_flights_form.departure.data, get_flights_form.arrival.data, get_flights_form.date.data, id)).fetchall()
            if get_flights_form.ret_ticket.data:
                get_flights_second = cur.execute(query,(get_flights_form.arrival.data, get_flights_form.departure.data, get_flights_form.second_date.data, id)).fetchall()
                return render_template('index.html', title='Главная', form = get_flights_form, search_bool = True, flights = get_flights_first, second_flights = get_flights_second, ret = get_flights_form.ret_ticket.data)
        return render_template('index.html', title='Главная', form = get_flights_form, search_bool = True, flights = get_flights_first, ret = get_flights_form.ret_ticket.data)
    # Бронирование
    if get_flights_form.book.data:
        if not current_user.is_authenticated:
            flash('Забронировать билет на рейс могут только авторизованные пользователи', 'warning')
            return redirect(url_for('login'))
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            query = query.format(sort = 'ASC')
            get_flights_second = cur.execute(query,(get_flights_form.arrival.data, get_flights_form.departure.data, get_flights_form.second_date.data, current_user.id)).fetchall()
        # Если есть обратные рейсы
        if get_flights_form.ret_ticket.data and get_flights_second and len(get_flights_second) > 0:
            return redirect(url_for('confimBook', firstFlight = request.form.get('flight_choice'), ret = True, secondFlight = request.form.get('second_flight_choice')))
        else:
            # Если нет обратных рейсов
            return redirect(url_for('confimBook', firstFlight = request.form.get('flight_choice'), ret = False, secondFlight = "0"))
    return render_template('index.html', title='Главная', form = get_flights_form, search_bool = False, ret = False)

# Авторизация админа
@app.route('/admin/login', methods=['GET', 'POST'])
def adminLogin():
    # Запрет доступа авторизованным пользователям
    if current_user.is_authenticated:
        abort(403)
    login_form = loginForm()
    if login_form.validate_on_submit():
        # Получение информации из базы
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT id, username, password '
                              'FROM public."admin" '
                              'WHERE username = %s', (login_form.username.data,)).fetchone()
        if res is None or not check_password_hash(res[2], login_form.password.data):
            flash('Попытка входа неудачна', 'danger')
            return redirect(url_for('adminLogin'))
        # Запоминание пользователя в сессии
        id, username, password = res
        user = User(id, username, password, 0)
        login_user(user, remember=login_form.remember_me.data)
        flash(f'Вы успешно вошли в систему, {current_user.username}', 'success')
        return redirect(url_for('index'))
    return render_template('user/login_registration.html', title='Авторизация админа', form=login_form)

# Выход
@login_required
@app.route('/logout')
def logout():
    # Запрет доступа неавторизованным польователям
    if not current_user.is_authenticated:
        abort(403)
    logout_user()
    return redirect(url_for('index'))

# Интерфейс админа
@login_required
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Доступ только для админов
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    # Перенаправления при нажатиях на кнопки
    interface = adminInterface()
    if interface.models.data:
        return redirect(url_for('models'))
    if interface.planes.data:
        return redirect(url_for('planes'))
    if interface.countries.data:
        return redirect(url_for('countries'))
    if interface.cities.data:
        return redirect(url_for('cities'))
    if interface.airports.data:
        return redirect(url_for('airports'))
    if interface.flights.data:
        return redirect(url_for('flights'))
    return render_template('admin/interface.html', title='Панель админа', form=interface)

# Добавление моделей самолетов
@login_required
@app.route('/admin/models', methods=['GET', 'POST'])
def models():
    # Доступ только для админов
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    model_form = adminModels()
    # Показать модели
    if model_form.show_models.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT * FROM public."plane model"')
            res = res.fetchall()
        return render_template('admin/models.html', title='Редактирование моделей самолета', form=model_form, plane_models = res, search_bool = True)
    # Добавить модель
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
                    except Exception:
                        flash('Неизвестная ошибка', 'danger')
                        con.rollback()
    # Удалить модель
    if model_form.delete.data:
        if not model_form.name.data:
            flash('Название не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."plane model" WHERE name = %s', (model_form.name.data,)).fetchone()
                if res:
                    try:
                        cur.execute('DELETE FROM public."plane model" WHERE name = %s', (model_form.name.data,))
                        flash('Модель успешно удалена', 'success')
                    except Exception:
                        flash('Невозможно удалить модель', 'danger')
                        con.rollback()
                else:
                    flash('Такой модели нет!', 'danger')
    return render_template('admin/models.html', title='Редактирование моделей самолета', form=model_form, search_bool = False)

# Добавление самолетов в парк
@login_required
@app.route('/admin/planes', methods=['GET', 'POST'])
def planes():
    # Доступ только для админов
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    plane_form = adminPlanes()
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        res = (cur.execute('SELECT name FROM public."plane model"')).fetchall()
        plane_form.model.choices = [(model[0], model[0]) for model in res]
        res = (cur.execute('SELECT * FROM public."plane"')).fetchall()
    # Показать модели
    if plane_form.show_planes.data:
        return render_template('admin/planes.html', title='Редактирование самолетов в парке', form=plane_form, planes = res, search_bool = True)
    # Добавить самолет
    if plane_form.add.data:
        if not plane_form.number.data:
            flash('Номер не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."plane" WHERE number = %s', (plane_form.number.data,)).fetchone()
                if res:
                    flash('Самолет с таким номером уже есть!', 'danger')
                elif not re.fullmatch(r"^RA-\d{5}$",plane_form.number.data):
                    flash('Номер должен соответсвовать шаблону RA-#####, где # - цифра', 'danger')
                else:
                    try:
                        cur.execute('INSERT INTO public."plane" VALUES (%s, %s)',
                                    (plane_form.number.data, plane_form.model.data))
                        flash('Самолет успешно добавлен', 'success')
                    except Exception:
                        flash('Неизвестная ошибка', 'danger')
                        con.rollback()
    # Удалить модель
    if plane_form.delete.data:
        if not plane_form.number.data:
            flash('Номер не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."plane" WHERE number = %s', (plane_form.number.data,)).fetchone()
                if not re.fullmatch(r"^RA-\d{5}$",plane_form.number.data):
                    flash('Номер должен соответсвовать шаблону RA-#####, где # - цифра!', 'danger')
                elif res:
                    try:
                        cur.execute('DELETE FROM public."plane" WHERE number = %s', (plane_form.number.data,))
                        flash('Самолет успешно удален', 'success')
                    except Exception:
                        flash('Невозможно удалить самолет', 'danger')
                        con.rollback()
                else:
                    flash('Такого самолета нет!', 'danger')
    return render_template('admin/planes.html', title='Редактирование самолетов в парке', form=plane_form, search_bool = False)

# Добавление стран в базу
@login_required
@app.route('/admin/countries', methods=['GET', 'POST'])
def countries():
    # Доступ только для админов
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    country_form = adminСountries()
    # Показать страны
    if country_form.show_countries.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = (cur.execute('SELECT * FROM public."country"')).fetchall()
        return render_template('admin/countries.html', title='Редактирование стран в базе', form=country_form, countries = res, search_bool = True)
    # Добавить страну
    if country_form.add.data:
        if not country_form.name.data:
            flash('Название не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."country" WHERE name = %s', (country_form.name.data,)).fetchone()
                if res:
                    flash('Страна с таким названием уже есть!', 'danger')
                else:
                    try:
                        cur.execute('INSERT INTO  public."country" VALUES (%s, %s)',
                                    (country_form.name.data, country_form.visa.data))
                        flash('Страна успешно добавлена', 'success')
                    except Exception:
                        flash('Неизвестная ошибка', 'danger')
                        con.rollback()
    # Удалить страну
    if country_form.delete.data:
        if not country_form.name.data:
            flash('Название не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."country" WHERE name = %s', (country_form.name.data,)).fetchone()
                if res:
                    try:
                        cur.execute('DELETE FROM public."country" WHERE name = %s', (country_form.name.data,))
                        flash('Страна успешно удалена', 'success')
                    except Exception:
                        flash('Невозможно удалить страну', 'danger')
                        con.rollback()
                else:
                    flash('Такой страны нет в базе!', 'danger')
    return render_template('admin/countries.html', title='Редактирование стран в базе', form=country_form, search_bool = False)

# Добавление городов в базу
@login_required
@app.route('/admin/cities', methods=['GET', 'POST'])
def cities():
    # Доступ только для админов
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    city_form = adminСities()
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        res = (cur.execute('SELECT name FROM public."country"')).fetchall()
        city_form.country.choices = [(country[0], country[0]) for country in res]
    # Показать города
    if city_form.show_cities.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = (cur.execute('SELECT * FROM public."city"')).fetchall()
        return render_template('admin/cities.html', title='Редактирование городов в базе', form=city_form, cities = res, search_bool = True)
    # Добавить город
    if city_form.add.data:
        if not city_form.name.data:
            flash('Название не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."city" WHERE name = %s', (city_form.name.data,)).fetchone()
                if res:
                    flash('Город с таким названием уже есть!', 'danger')
                else:
                    try:
                        cur.execute('INSERT INTO  public."city" VALUES (%s, %s)',
                                    (city_form.name.data, city_form.country.data))
                        flash('Город успешно добавлен', 'success')
                    except Exception:
                        flash('Неизвестная ошибка', 'danger')
                        con.rollback()
    # Удалить город
    if city_form.delete.data:
        if not city_form.name.data:
            flash('Название не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."city" WHERE name = %s', (city_form.name.data,)).fetchone()
                if res:
                    try:
                        cur.execute('DELETE FROM public."city" WHERE name = %s', (city_form.name.data,))
                        flash('Город успешно удален', 'success')
                    except Exception:
                        flash('Невозможно удалить город', 'danger')
                        con.rollback()
                else:
                    flash('Такого города нет в базе!', 'danger')
    return render_template('admin/cities.html', title='Редактирование городов в базе', form=city_form, search_bool = False)

# Добавление аэропортов в базу
@app.route('/admin/airports', methods=['GET', 'POST'])
def airports():
    # Доступ только для админов
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    airport_form = adminAirports()
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        res = (cur.execute('SELECT name FROM public."city"')).fetchall()
        airport_form.city.choices = [(city[0], city[0]) for city in res]
    # Показать аэропорты
    if airport_form.show_airports.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = (cur.execute('SELECT * FROM public."airport"')).fetchall()
        return render_template('admin/airports.html', title='Редактирование аэропортов в базе', form=airport_form, airports = res, search_bool = True)
    # Добавить аэропорт
    if airport_form.add.data:
        if not airport_form.code.data:
            flash('Код не может быть пустым!', 'danger')
        elif not airport_form.name.data:
            flash('Название не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."airport" WHERE code = %s', (airport_form.code.data,)).fetchone()
                if res:
                    flash('Аэропорт с таким кодом уже есть!', 'danger')
                elif not re.fullmatch(r"^[A-Z]{3}$",airport_form.code.data):
                    flash('Код аэропорта должен состоять ровно из трех заглавных латинских букв!', 'danger')
                else:
                    try:
                        cur.execute('INSERT INTO  public."airport" VALUES (%s, %s,%s)',
                                    (airport_form.code.data, airport_form.name.data, airport_form.city.data))
                        flash('Аэропорт успешно добавлен', 'success')
                    except Exception:
                        flash('Неизвестная ошибка', 'danger')
                        con.rollback()
    # Удалить модель
    if airport_form.delete.data:
        if not airport_form.code.data:
            flash('Код не может быть пустым!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."airport" WHERE code = %s', (airport_form.code.data,)).fetchone()
                if not re.fullmatch(r"^[A-Z]{3}$",airport_form.code.data):
                    flash('Код аэропорта должен состоять ровно из трех заглавных латинских букв!', 'danger')
                elif res:
                    try:
                        cur.execute('DELETE FROM public."airport" WHERE code = %s', (airport_form.code.data,))
                        flash('Аэропорт успешно удален', 'success')
                    except Exception:
                        flash('Невозможно удалить аэропорт', 'danger')
                        con.rollback()
                else:
                    flash('Такого аэропорта нет!', 'danger')
    return render_template('admin/airports.html', title='Редактирование аэропортов в базе', form=airport_form, search_bool = False)

# Рейсы админа
@login_required
@app.route('/admin/flights', methods=['GET', 'POST'])
def flights():
    # Доступ только для админов
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    flight_form = adminFlights()
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()

        number = '%'
        plane = '%'
        departure = '%'
        arrival = '%'
        date_departure = '%'
        status = '%'

        if flight_form.number.data and flight_form.number.data != '-1':
            number = flight_form.number.data
        if flight_form.plane.data and flight_form.plane.data!='-1':
            plane=flight_form.plane.data
        if flight_form.departure.data and flight_form.departure.data!='-1':
            departure=flight_form.departure.data
        if flight_form.arrival.data and flight_form.arrival.data!='-1':
            arrival=flight_form.arrival.data
        if flight_form.date.data:
            date_departure = flight_form.date.data.strftime('%Y-%m-%d')
        if flight_form.status.data and flight_form.status.data!='-1':
            status=flight_form.status.data

        flight_form.number.choices = [(-1, 'Выберите рейс')] 
        flight_form.plane.choices = [(-1, 'Выберите самолет')] 
        flight_form.departure.choices = [(-1, 'Выберите аэропорт вылета')]
        flight_form.arrival.choices = [(-1, 'Выберите аэропорт прилета')]

        res = (cur.execute('SELECT * FROM public."flight"')).fetchall()
        flight_form.number.choices += [(ress[0], ress[0]) for ress in res]
        res = (cur.execute('SELECT * FROM public."plane"')).fetchall()
        flight_form.plane.choices += [(ress[1], ress[1]) for ress in res]
        res = cur.execute('SELECT code, city FROM public.airport').fetchall()
        flight_form.departure.choices += [(airport[0], f"{airport[1]} ({airport[0]})") for airport in res]
        flight_form.arrival.choices += [(airport[0], f"{airport[1]} ({airport[0]})") for airport in res]

        # Удалить рейс
        delete_btn = request.form.get('flight_delete')
        if delete_btn:
            try:
                cur.execute('DELETE FROM public."flight" WHERE number = %s', (delete_btn,))
                flash('Рейс успешно удален', 'success')
            except Exception:
                flash('Невозможно удалить рейс', 'danger')
                con.rollback()

        # Изменить рейс
        change_btn = request.form.get('flight_change')
        if change_btn:
            return redirect(url_for('change_flights', flight = change_btn))

        res = (cur.execute('SELECT * FROM public."flight" WHERE "number" LIKE %s AND "plane number" LIKE %s AND "departure" LIKE %s AND "arrival" LIKE %s AND TO_CHAR("departure datetime", \'YYYY-MM-DD\') LIKE %s AND TO_CHAR("status", \'FM999999999\') LIKE %s'
                        , (number,plane,departure,arrival,date_departure,status))).fetchall()
    if flight_form.add.data:
        return redirect(url_for('add_flights'))
    return render_template('admin/flights.html', title='Редактирование рейсов', form=flight_form, flights = res, search_bool = True, today=date.today())

# Добавление рейсов
@login_required
@app.route('/admin/flights/add', methods=['GET', 'POST'])
def add_flights():
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    flight_form = add_adminFlights()
    if flight_form.back.data:
        return redirect(url_for('flights'))
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        res = (cur.execute('SELECT model, number FROM public."plane"')).fetchall()
        flight_form.plane.choices = [(plane[1], f"{plane[1]} ({plane[0]})") for plane in res]
        res = cur.execute('SELECT code, city FROM public.airport').fetchall()
        flight_form.departure.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in res]
        flight_form.arrival.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in res]

    if flight_form.add.data:
        if not flight_form.number.data:
            flash('Номер не может быть пустым!', 'danger')
        elif not flight_form.date.data:
            flash('Дата не модет быть пустой!', 'danger')
        elif flight_form.date.data <= date.today():
            flash('Дата не может быть меньше или равна сегодняшней!', 'danger')
        elif not flight_form.time.data:
            flash('Время вылета не может быть пустым!', 'danger')
        elif not flight_form.travel_time.data:
            flash('Время в пути не может быть пустым!', 'danger')
        elif flight_form.time.data == time(0, 0):
            flash('Время в пути не может быть 00:00!', 'danger')
        else:
            departure_datetime = datetime.combine(flight_form.date.data, flight_form.time.data)
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                airports = cur.execute('SELECT city FROM public."airport" WHERE code = %s OR code = %s', (flight_form.departure.data,flight_form.arrival.data)).fetchall()
                if not re.fullmatch(r"^OBL\d{4}$",flight_form.number.data):
                    flash('Номер должен соответсвовать шаблону OBL####, где # - цифра!', 'danger')
                elif len(airports) < 2 or airports[0][0] == airports[1][0]:
                    flash('Города вылета и прибытия должны различаться!', 'danger')
                else:
                    try_bool = True
                    datetimes = cur.execute('SELECT "departure datetime", "arrival datetime" FROM public."flight" WHERE "plane number" = %s', (flight_form.plane.data,)).fetchall()
                    for departure, arrival  in datetimes:
                        if departure <= departure_datetime <= arrival:
                            flash ('Самолет в это время уже занят!', 'danger')
                            try_bool = False
                            break
                    if try_bool:
                        
                        try_bool = True
                        plases = cur.execute('SELECT pm."economy class",pm."business class",pm."first class" FROM "plane" p JOIN public."plane model" pm ON p."model" = pm."name" WHERE p."number" = %s', (flight_form.plane.data,)).fetchone()
                        if plases[0] > 0 and flight_form.economy.data == 0:
                            flash ('Не указана цена за место эконом класса!', 'danger')
                            try_bool = False
                        if plases[1] > 0 and flight_form.buisness.data == 0:
                            flash ('Не указана цена за место бизнесс класса!', 'danger')
                            try_bool = False
                        if plases[2] > 0 and flight_form.first.data == 0:
                            flash ('Не указана цена за место первого класса!', 'danger')
                            try_bool = False
                        if plases[0] == 0 and flight_form.economy.data > 0:
                            flash ('Указана цена за место эконом класса, которого нет в модели!', 'danger')
                            try_bool = False
                        if plases[1] == 0 and flight_form.buisness.data > 0:
                            flash ('Указана цена за место бизнесс класса, которого нет в модели!', 'danger')
                            try_bool = False
                        if plases[2] == 0 and flight_form.first.data > 0:
                            flash ('Указана цена за место первого класса, которого нет в модели!', 'danger')
                            try_bool = False
                        if try_bool:
                            number = (cur.execute('SELECT * FROM public."flight" WHERE number = %s', (flight_form.number.data,))).fetchall()
                            if number:
                                flash ('Рейс с таким номером уже есть!', 'danger')
                            else:
                                travel_delta = timedelta(hours=flight_form.travel_time.data.hour, minutes=flight_form.travel_time.data.minute)
                                arrival_datetime = departure_datetime+travel_delta
                                try:
                                    cur.execute('INSERT INTO  public."flight" VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                        (flight_form.number.data,flight_form.plane.data,flight_form.departure.data,flight_form.arrival.data,departure_datetime, arrival_datetime,0,flight_form.economy.data,flight_form.buisness.data,flight_form.first.data))
                                    flash('Рейс успешно добавлен', 'success')
                                    return redirect(url_for('flights'))
                                except Exception:
                                    flash('Невозможно добавить рейс', 'danger')
    return render_template('admin/add_flights.html', title='Добавление рейсов', form=flight_form)


# Изменение рейсов
@login_required
@app.route('/admin/flights/chnage/<flight>', methods=['GET', 'POST'])
def change_flights(flight):
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    flight_form = change_adminFlights()
    if flight_form.back.data:
        return redirect(url_for('flights'))

    if flight_form.change.data:
        if not flight_form.number.data:
            flash('Номер не может быть пустым!', 'danger')
        elif not flight_form.date.data:
            flash('Дата не модет быть пустой!', 'danger')
        elif flight_form.date.data <= date.today():
            flash('Дата не может быть меньше или равна сегодняшней!', 'danger')
        elif not flight_form.time.data:
            flash('Время вылета не может быть пустым!', 'danger')
        elif not flight_form.travel_time.data:
            flash('Время в пути не может быть пустым!', 'danger')
        elif flight_form.time.data == time(0, 0):
            flash('Время в пути не может быть 00:00!', 'danger')
        else:
            departure_datetime = datetime.combine(flight_form.date.data, flight_form.time.data)
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                airports = cur.execute('SELECT city FROM public."airport" WHERE code = %s OR code = %s', (flight_form.departure.data,flight_form.arrival.data)).fetchall()
                if not re.fullmatch(r"^OBL\d{4}$",flight_form.number.data):
                    flash('Номер должен соответсвовать шаблону OBL####, где # - цифра!', 'danger')
                elif len(airports) < 2 or airports[0][0] == airports[1][0]:
                    flash('Города вылета и прибытия должны различаться!', 'danger')
                else:
                    number = cur.execute('SELECT * FROM public."flight" WHERE number = %s', (flight_form.number.data,)).fetchone()
                    if not number:
                        flash ('Рейс с таким номером не существует!', 'danger')
                    elif number[5] < datetime.combine(date.today(), datetime.min.time()):
                        flash ('Нельзя менять данные прошедших рейсов!', 'danger')
                    else:
                        try_bool = True
                        datetimes = cur.execute('SELECT "departure datetime", "arrival datetime", "number" FROM public."flight" WHERE "plane number" = %s', (flight_form.plane.data,)).fetchall()
                        for departure, arrival, number  in datetimes:
                            if number == flight_form.number.data:
                                continue
                            if departure <= departure_datetime <= arrival:
                                flash ('Самолет в это время уже занят!', 'danger')
                                try_bool = False
                                break
                        if try_bool:
                        
                            try_bool = True
                            plases = cur.execute('SELECT pm."economy class",pm."business class",pm."first class" FROM "plane" p JOIN public."plane model" pm ON p."model" = pm."name" WHERE p."number" = %s', (flight_form.plane.data,)).fetchone()
                            if plases[0] > 0 and flight_form.economy.data == 0:
                                flash ('Не указана цена за место эконом класса!', 'danger')
                                try_bool = False
                            if plases[1] > 0 and flight_form.buisness.data == 0:
                                flash ('Не указана цена за место бизнесс класса!', 'danger')
                                try_bool = False
                            if plases[2] > 0 and flight_form.first.data == 0:
                                flash ('Не указана цена за место первого класса!', 'danger')
                                try_bool = False
                            if try_bool:
                                travel_delta = timedelta(hours=flight_form.travel_time.data.hour, minutes=flight_form.travel_time.data.minute)
                                arrival_datetime = departure_datetime+travel_delta
                                try:
                                    cur.execute('UPDATE "flight" SET "plane number" = %s, "departure" = %s, "arrival" = %s, "departure datetime" = %s, "arrival datetime" = %s, "status" = %s, "economy price" = %s, "business price" = %s, "first price" = %s WHERE "number" = %s',
                                        (flight_form.plane.data,flight_form.departure.data,flight_form.arrival.data,departure_datetime, arrival_datetime,flight_form.status.data,flight_form.economy.data,flight_form.buisness.data,flight_form.first.data, flight_form.number.data))
                                    flash('Рейс успешно изменен', 'success')
                                except Exception:
                                    flash('Невозможно изменить рейс', 'danger')

    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()

        res = (cur.execute('SELECT model, number FROM public."plane"')).fetchall()
        flight_form.plane.choices = [(plane[1], f"{plane[1]} ({plane[0]})") for plane in res]
        res = cur.execute('SELECT code, city FROM public.airport').fetchall()
        flight_form.departure.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in res]
        flight_form.arrival.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in res]

        current_flight = cur.execute('SELECT * FROM public."flight" WHERE "number" = %s', (flight,)).fetchone()
        flight_form.number.data = current_flight[0]
        flight_form.plane.data = current_flight[1]
        flight_form.departure.data = current_flight[2]
        flight_form.arrival.data = current_flight[3]
        flight_form.date.data = (current_flight[4]).date()
        flight_form.time.data = (current_flight[4]).time()

        time_diff = current_flight[5] - current_flight[4]
        hours = (time_diff.seconds // 3600)
        minutes = (time_diff.seconds % 3600) // 60
        time_diff_as_time = time(hours, minutes)
        flight_form.travel_time.data = time_diff_as_time

        flight_form.economy.data = current_flight[7]
        flight_form.buisness.data = current_flight[8]
        flight_form.first.data = current_flight[9]

    return render_template('admin/change_flights.html', title='Изменение рейсов', form=flight_form)


# Регистрация
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    # Запрет доступа авторизованным пользователям
    if current_user.is_authenticated:
        abort(403)
    registration_form = registrationForm()
    if registration_form.validate_on_submit():
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                user = cur.execute('SELECT * FROM public."user" WHERE "login" = %s', (registration_form.login.data,)).fetchone()
                if user:
                    flash ('Пользователь с таким именем уже есть!', 'danger')
                else:
                    try:
                        password_hash = generate_password_hash(registration_form.password.data)
                        cur.execute('INSERT INTO public."user" VALUES (%s, %s, %s)', (registration_form.login.data,password_hash, registration_form.birthdate.data))
                        flash(f'Вы успешно зарегистрированы, {registration_form.login.data}', 'success')
                        return redirect(url_for('login'))
                    except Exception:
                        flash('Не удалось зарегистрироваться', 'danger')
    return render_template('user/login_registration.html', title='Регистрация', form=registration_form)

# Авторизация пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Запрет доступа авторизованным пользователям
    if current_user.is_authenticated:
        abort(403)
    login_form = loginForm()
    if login_form.validate_on_submit():
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT id, login, password '
                              'FROM public."user" '
                              'WHERE login = %s', (login_form.username.data,)).fetchone()
        if res is None or not check_password_hash(res[2], login_form.password.data):
            flash('Попытка входа неудачна', 'danger')
            return redirect(url_for('login'))
        id, username, password = res
        user = User(id, username, password, 1)
        login_user(user, remember=login_form.remember_me.data)
        flash(f'Вы успешно вошли в систему, {current_user.username}', 'success')
        return redirect(url_for('index'))
    return render_template('user/login_registration.html', title='Авторизация', form=login_form)

# Личный кабинет
@app.route('/account', methods=['GET', 'POST'])
def account():
    # Доступ только для авторизованных пользователей
    if not current_user.is_authenticated or current_user.role != 1:
        abort(403)
    account_form=accountForm()
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        query = '''
            SELECT f."number", p."number", p."model", c_dep."name", city_dep."name",
            dep."code", c_arr."name", city_arr."name", arr."code", f."departure datetime",
            f."arrival datetime", c_arr."visa", book."type", book."status", f."status"
            FROM public."booking" AS book
            LEFT JOIN public."flight" as f
            ON book."flight" = f."number"
            LEFT JOIN public."plane" as p
            ON f."plane number" = p."number"
            LEFT JOIN public."airport" as arr
            ON f."arrival" = arr."code"
            LEFT JOIN public."airport" as dep
            ON f."departure" = dep."code"
            LEFT JOIN public."city" as city_arr
            ON arr."city" = city_arr."name"
            LEFT JOIN public."city" as city_dep
            ON dep."city" = city_dep."name"
            LEFT JOIN public."country" as c_arr
            ON city_arr."country" = c_arr."name"
            LEFT JOIN public."country" as c_dep
            ON city_dep."country" = c_dep."name"
            WHERE book."passenger" = %s
            '''
        get_bookings = cur.execute(query, (current_user.id,)).fetchall()

    # Получение данных из базы
    if request.method == 'GET':
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT money FROM public."user" WHERE id = %s', (current_user.id,)).fetchone()
            account_form.money.data = res[0]
    # Пополнение счета
    if account_form.change_money.data:
        try:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('UPDATE "user" SET money = %s WHERE id = %s', (account_form.money.data,current_user.id))
            flash('Счет успешно изменен', 'success')
        except Exception:
            flash('Не удалось изменить счет', 'danger')
    # Переход к изменению данных
    if account_form.change_data.data:
        return redirect(url_for('accountChange'))
    # Переход к конкретному бронированию
    if account_form.change_booking.data:
        return redirect(url_for('changeBooking', flight = request.form.get('booking_choice')))
    return render_template('user/account.html', title=f'Личный кабинет пользователя {current_user.username}', form=account_form, bookings = get_bookings)

# Изменение данных аккаунта
@app.route('/account/change', methods=['GET', 'POST'])
def accountChange():
    accountChange_form=accountChangeForm()
    # Доступ только для авторизованных пользователей
    if not current_user.is_authenticated or current_user.role != 1:
        abort(403)
    # Получение данных из базы
    if request.method == 'GET':
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT * FROM public."user" WHERE id = %s', (current_user.id,)).fetchone()
            accountChange_form.login.data = res[0]
            accountChange_form.birthdate.data = res[2]
            accountChange_form.surname.data = res[3]
            accountChange_form.name.data = res[4]
            accountChange_form.patronymic.data = res[5]
            accountChange_form.email.data = res[6]
            accountChange_form.phone.data = res[7]
    # Изменить данные
    if accountChange_form.submit.data:
        accountChange_form.phone.data = re.sub(r'[()\s-]', '', accountChange_form.phone.data)
    if accountChange_form.validate_on_submit():

        if accountChange_form.email.data:
            email = accountChange_form.email.data
        else:
            email = None

        if accountChange_form.phone.data:
            phone = accountChange_form.phone.data
        else:
            phone = None
        
        # Проверка полей на уникальность
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT * FROM public."user" WHERE login = %s and id != %s', (accountChange_form.login.data,current_user.id)).fetchone()
            cur_email = cur.execute('SELECT * FROM public."user" WHERE email = %s and id != %s', (accountChange_form.email.data,current_user.id)).fetchone()
            cur_phone = cur.execute('SELECT * FROM public."user" WHERE phone = %s and id != %s', (accountChange_form.phone.data,current_user.id)).fetchone()
        if res:
            flash ('Данный логин уже занят', 'danger')
        elif cur_email:
            flash ('Данный email уже занят', 'danger')
        elif cur_phone:
            flash ('Данный телефон уже занят', 'danger')
        elif accountChange_form.password.data or accountChange_form.confirm.data:
            password = generate_password_hash(accountChange_form.password.data)
        # Изменение информации в базе
            try:
                with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                    cur = con.cursor()
                    res = cur.execute('UPDATE "user" SET "login" = %s, "password" = %s,   "birthdate" = %s, "surname" = %s, "name" = %s, "patronymic" = %s, "email" = %s, "phone" = %s WHERE "id" = %s'
                                      , (accountChange_form.login.data, password, accountChange_form.birthdate.data, accountChange_form.surname.data, accountChange_form.name.data, accountChange_form.patronymic.data, email, phone, current_user.id))
                flash('Данные успешно обновлены', 'danger')
            except Exception:
                flash('Не удалось обновить данные', 'danger')
        else:
            try:
                with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                    cur = con.cursor()
                    res = cur.execute('UPDATE "user" SET "login" = %s,   "birthdate" = %s, "surname" = %s, "name" = %s, "patronymic" = %s, "email" = %s, "phone" = %s WHERE "id" = %s'
                                      , (accountChange_form.login.data, accountChange_form.birthdate.data, accountChange_form.surname.data, accountChange_form.name.data, accountChange_form.patronymic.data, email, phone, current_user.id))
                flash('Данные успешно обновлены', 'success')
            except Exception:
                flash('Не удалось обновить данные', 'danger')
    return render_template('user/account_change.html', title='Изменение данных', form=accountChange_form)

# Подтверждение брони
@app.route('/confimBook/<firstFlight>/<ret>/<secondFlight>', methods=['GET', 'POST'])
def confimBook(firstFlight, ret, secondFlight):
    # Доступ только для авторизованных пользователей
    if not current_user.is_authenticated or current_user.role != 1:
        abort(403)
    booking_form=confimBooking()

    # Изменение счета
    if booking_form.change_money.data:
        try:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('UPDATE "user" SET money = %s WHERE id = %s', (booking_form.money.data,current_user.id))
            flash('Счет успешно изменен', 'success')
        except Exception:
            flash('Не удалось изменить счет', 'danger')

    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        res_money = cur.execute('SELECT money FROM public."user" WHERE id = %s', (current_user.id,)).fetchone()
        booking_form.money.data = res_money[0]
        query = '''
        SELECT f."number",p."number",p."model", c_dep."name", city_dep."name",
        dep."code", c_arr."name", city_arr."name", arr."code", f."departure datetime",
        f. "arrival datetime", f."economy price", f."business price", f."first price", c_arr."visa"
        FROM public."flight" AS f
        LEFT JOIN public."plane" AS p
            ON f."plane number" = p."number"
        LEFT JOIN public."airport" AS arr
            ON f."arrival" = arr."code"
        LEFT JOIN public."airport" AS dep
            ON f."departure" = dep."code"
        LEFT JOIN public."city" AS city_arr
            ON arr."city" = city_arr."name"
        LEFT JOIN public."city" AS city_dep
            ON dep."city" = city_dep."name"
        LEFT JOIN public."country" AS c_arr
            ON city_arr."country" = c_arr."name"
        LEFT JOIN public."country" AS c_dep
            ON city_dep."country" = c_dep."name"
        WHERE f."number" = %s
        '''

        res_first = cur.execute(query,(firstFlight,)).fetchone()
        if ret == 'True':
            res_second = cur.execute(query,(secondFlight,)).fetchone()
        else:
            res_second = 0
    # Обязательная оплата
    message = False
    if res_first[9] < datetime.now() + timedelta(days=7):
        booking_form.pay.data = True
        booking_form.pay.render_kw = {'disabled': 'disabled'}
        message = True

    # Подтверждение брони
    if booking_form.submit.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            pay_bool = True
            first_choice = request.form.get('first_choice')
            if ret == 'True':
                second_choice = request.form.get('second_choice')
            # Если выбрана оплата сразу
            if booking_form.pay.data:
                first_index = 11 + int(first_choice)
                pay_count = res_first[first_index]
                if ret == 'True':
                    second_index = 11 + int(second_choice)
                    pay_count += res_second[second_index]
                if pay_count > res_money[0]:
                    flash('Недостаточно средств на счете!', 'danger')
                    pay_bool = False
                else:
                    try:
                        res = cur.execute('UPDATE "user" SET money = %s WHERE id = %s', (res_money[0]-pay_count,current_user.id))
                        con.commit()
                        flash('Оплата прошла успешно', 'success')
                    except Exception:
                        flash('Не удалось оплатить', 'danger')
                        pay_bool = False
            if pay_bool:
                try:
                    res = cur.execute('INSERT INTO public."booking" VALUES (%s,%s, %s, %s)', (firstFlight, current_user.id, int(first_choice), booking_form.pay.data))
                    if ret == 'True':
                        res = cur.execute('INSERT INTO public."booking" VALUES (%s,%s, %s, %s)', (secondFlight, current_user.id, int(second_choice), booking_form.pay.data))
                    con.commit()
                    flash('Успешно забронировано', 'success')
                    return redirect(url_for('account'))
                except Exception:
                    flash('Не удалось забронировать', 'danger')

    return render_template('user/confim_booking.html', title='Подтверждение брони', form=booking_form, first = res_first, ret_bool = ret, second = res_second, mes = message)

# Изменение брони
@app.route('/account/changeBooking/<flight>', methods=['GET', 'POST'])
def changeBooking(flight):
    # Доступ только для авторизованных пользователей
    if not current_user.is_authenticated or current_user.role != 1:
        abort(403)
    changeBooking_form=changeBookingForm()
    prosrochka = False
    vremia = False
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        query = '''
            SELECT f."number", p."number", p."model", c_dep."name", city_dep."name",
            dep."code", c_arr."name", city_arr."name", arr."code", f."departure datetime",
            f."arrival datetime", c_arr."visa", book."type", book."status", f."status",
            f."economy price", f."business price", f."first price"
            FROM public."booking" AS book
            LEFT JOIN public."flight" as f
            ON book."flight" = f."number"
            LEFT JOIN public."plane" as p
            ON f."plane number" = p."number"
            LEFT JOIN public."airport" as arr
            ON f."arrival" = arr."code"
            LEFT JOIN public."airport" as dep
            ON f."departure" = dep."code"
            LEFT JOIN public."city" as city_arr
            ON arr."city" = city_arr."name"
            LEFT JOIN public."city" as city_dep
            ON dep."city" = city_dep."name"
            LEFT JOIN public."country" as c_arr
            ON city_arr."country" = c_arr."name"
            LEFT JOIN public."country" as c_dep
            ON city_dep."country" = c_dep."name"
            WHERE book."passenger" = %s
            AND f."number" = %s
            '''
        
        second_query = '''
        SELECT 
            m."economy class" - COUNT(CASE WHEN b."type" = 0 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END) AS economy_count, 
            m."business class" - COUNT(CASE WHEN b."type" = 1 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END) AS business_count, 
            m."first class" - COUNT(CASE WHEN b."type" = 2 AND NOT(b."status" = False AND f."departure datetime" < NOW() + INTERVAL '7 days') THEN 1 END) AS first_count
        FROM public."flight" AS f
        LEFT JOIN public."plane" AS p
            ON f."plane number" = p."number"
        LEFT JOIN public."plane model" AS m
            ON p."model" = m."name"
        LEFT JOIN public."booking" AS b
            ON f."number" = b."flight"
        WHERE f."number" = %s
        GROUP BY f."number", m."economy class", m."business class", m."first class"
        '''

        # Получение данных из базы
        get_booking = cur.execute(query, (current_user.id, flight)).fetchone()
        get_places = cur.execute(second_query, (flight,)).fetchone()
        get_money = cur.execute('SELECT money FROM public."user" WHERE id = %s', (current_user.id,)).fetchone()
    # Если бронь просрочена
    if (get_booking[9] < datetime.now() + timedelta(days=7)) and not get_booking[13]:
        prosrochka = True

    # Если рейс выполнен
    if get_booking[9] < datetime.now():
        vremia = True

    # Оплата
    if changeBooking_form.pay.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            if get_booking[12] == 0:
                price = get_booking[15]
            elif get_booking[12] == 1:
                price = get_booking[16]
            else:
                price = get_booking[17]
            if get_money[0] < get_booking[15+get_booking[12]]:
                flash('Недостаточно средств на счете!', 'danger')
            else:
                try:
                    cur.execute('UPDATE public."user" SET money = %s WHERE id = %s', (get_money[0]-price,current_user.id))
                    cur.execute('UPDATE public."booking" SET "status" = %s WHERE "passenger" = %s AND "flight" = %s', (True, current_user.id, flight))
                    con.commit()
                    flash('Оплата прошла успешно', 'success')
                except Exception:
                    flash('Не удалось оплатить', 'danger')
    # Изменение класса
    if changeBooking_form.change_class.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            if not get_booking[13]:
                try:
                    cur.execute('UPDATE public."booking" SET "type" = %s WHERE "passenger" = %s AND "flight" = %s', (request.form.get('place_choice'), current_user.id, flight))
                    flash('Класс билета успешно изменен', 'success')
                except Exception:
                    flash('Не удалось изменить класс билета', 'danger')
            else:
                # Пересчёт при оплаченном билете
                get_money = cur.execute('SELECT money FROM public."user" WHERE id = %s', (current_user.id,)).fetchone()
                price = get_booking[15+int(request.form.get('place_choice'))] - get_booking[15+get_booking[12]]
                if get_money[0] < price:
                    flash('Недостаточно средств на счете!', 'danger')
                else:
                    try:
                        cur.execute('UPDATE public."booking" SET "type" = %s WHERE "passenger" = %s AND "flight" = %s', (request.form.get('place_choice'), current_user.id, flight))
                        cur.execute('UPDATE public."user" SET money = %s WHERE id = %s', (get_money[0]-price,current_user.id))
                        flash('Класс билета успешно изменен', 'success')
                    except Exception:
                        flash('Не удалось изменить класс билета', 'danger')
    # Удаление брони
    if changeBooking_form.delete.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            try:
                cur.execute('Delete FROM public."booking" WHERE "passenger" = %s AND "flight" = %s', (current_user.id, flight))    
                if get_booking[13]:
                    # Возврат средств
                    if (get_booking[9] < datetime.now() + timedelta(days=7)):
                        cur.execute('UPDATE public."user" SET money = %s WHERE id = %s', (get_money[0]+int((get_booking[15+get_booking[12]])/2),current_user.id))
                        flash('50% суммы возвращены', 'success')
                    elif (get_booking[9] >= datetime.now() + timedelta(days=7)):
                        cur.execute('UPDATE public."user" SET money = %s WHERE id = %s', (get_money[0]+int(get_booking[15+get_booking[12]]),current_user.id))
                        flash('Вся сумма возвращена', 'success')
                flash('Бронь успешно удалена', 'success')
                return redirect(url_for('account'))
            except Exception:
                flash('Не удалось удалить бронь', 'danger')
    return render_template('user/changeBooking.html', title='Информация о брони', form=changeBooking_form, booking = get_booking, srok = prosrochka, time = vremia, places = get_places)