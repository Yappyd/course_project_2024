import psycopg, re
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, flash, url_for, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import app
from app.forms import *
from app.user import User
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta

# Стартовая станица
@app.route('/', methods=['GET', 'POST'])
def index():
    get_flights_form = flight_search()
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        airports = cur.execute('SELECT code, city FROM public.airport').fetchall()
        get_flights_form.departure.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in airports]
        get_flights_form.arrival.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in airports]
        
        if get_flights_form.date.data is None:
            get_flights = cur.execute('SELECT * FROM public.flight WHERE departure = %s AND arrival = %s',(get_flights_form.departure.data, get_flights_form.arrival.data))
        else:
            get_flights = cur.execute('SELECT * FROM public.flight WHERE departure = %s AND arrival = %s AND DATE("departure datetime") = %s',(get_flights_form.departure.data, get_flights_form.arrival.data, get_flights_form.date.data))
        get_flights=get_flights.fetchall()
        return render_template('index.html', title='Главная', form = get_flights_form, search_bool = True, flights = get_flights)
        
    return render_template('index.html', title='Главная', form = get_flights_form, search_bool = False)

# Авторизация админа
@app.route('/admin/login', methods=['GET', 'POST'])
def adminLogin():
    if current_user.is_authenticated:
        abort(403)
    login_form = loginForm()
    if login_form.validate_on_submit():
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            res = cur.execute('SELECT id, username, password '
                              'FROM public."admin" '
                              'WHERE username = %s', (login_form.username.data,)).fetchone()
        if res is None or not check_password_hash(res[2], login_form.password.data):
            flash('Попытка входа неудачна', 'danger')
            return redirect(url_for('adminLogin'))
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
    if not current_user.is_authenticated:
        abort(403)
    logout_user()
    return redirect(url_for('index'))

# Интерфейс админа
@login_required
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
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

# Добавление рейсов
@login_required
@app.route('/admin/flights', methods=['GET', 'POST'])
def flights():
    if not current_user.is_authenticated or current_user.role != 0:
        abort(403)
    flight_form = adminFlights()
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        res = (cur.execute('SELECT model, number FROM public."plane"')).fetchall()
        flight_form.plane.choices = [(plane[1], f"{plane[1]} ({plane[0]})") for plane in res]
        res = cur.execute('SELECT code, city FROM public.airport').fetchall()
        flight_form.departure.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in res]
        flight_form.arrival.choices = [(airport[0], f"{airport[1]} ({airport[0]})") for airport in res]
    # Показать все рейсы
    if flight_form.show_flights.data:
        with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
            cur = con.cursor()
            number = '%'
            plane = '%'
            departure = '%'
            arrival = '%'
            date_departure = '%'
            status = '%'
            # Фильтры
            if flight_form.check_number.data:
                if flight_form.number.data: 
                    number = flight_form.number.data
                else:
                    flash('Номер рейса пустой, фильтр игнорируется', 'warning')
            if flight_form.check_plane.data:
                plane=flight_form.plane.data
            if flight_form.check_departure.data:
                departure=flight_form.departure.data
            if flight_form.check_arrival.data:
                arrival=flight_form.arrival.data
            if flight_form.check_date.data:
                if flight_form.date.data:
                    date_departure = flight_form.date.data.strftime('%Y-%m-%d')
                else:
                    flash('Дата пустая, фильтр игнорируется', 'warning')
            if flight_form.check_status.data:
                status=flight_form.status.data
            res = (cur.execute('SELECT * FROM public."flight" WHERE "number" LIKE %s AND "plane number" LIKE %s AND "departure" LIKE %s AND "arrival" LIKE %s AND TO_CHAR("departure datetime", \'YYYY-MM-DD\') LIKE %s AND TO_CHAR("status", \'FM999999999\') LIKE %s'
                               , (number,plane,departure,arrival,date_departure,status))).fetchall()
        return render_template('admin/flights.html', title='Редактирование рейсов', form=flight_form, flights = res, search_bool = True)
    # Добавить рейс
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
                        if try_bool:
                            number = (cur.execute('SELECT * FROM public."flight" WHERE number = %s', (flight_form.number.data,))).fetchall()
                            if number:
                                flash ('Рейс с таким номером уже есть!', 'danger')
                            else:
                                travel_delta = timedelta(hours=flight_form.travel_time.data.hour, minutes=flight_form.travel_time.data.minute)
                                arrival_datetime = departure_datetime+travel_delta
                                # cur.execute('INSERT INTO  public."flight" VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                #         (flight_form.number.data,flight_form.plane.data,flight_form.departure.data,flight_form.arrival.data,departure_datetime, arrival_datetime,0,flight_form.economy.data,flight_form.buisness.data,flight_form.first.data))
                                try:
                                    cur.execute('INSERT INTO  public."flight" VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                        (flight_form.number.data,flight_form.plane.data,flight_form.departure.data,flight_form.arrival.data,departure_datetime, arrival_datetime,0,flight_form.economy.data,flight_form.buisness.data,flight_form.first.data))
                                    flash('Рейс успешно добавлен', 'success')
                                except Exception:
                                    flash('Невозможно добавить рейс', 'danger')
    # Удалить рейс
    if flight_form.delete.data:
        if not flight_form.number.data:
            flash('Номер не может быть пустым!', 'danger')
        elif not re.fullmatch(r"^OBL\d{4}$",flight_form.number.data):
            flash('Номер должен соответсвовать шаблону OBL####, где # - цифра!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                res = cur.execute('SELECT * FROM public."flight" WHERE number = %s', (flight_form.number.data,)).fetchone()
                if not res:
                    flash('Рейса с таким номером не существует!', 'danger')
                else:
                    try:
                        cur.execute('DELETE FROM public."flight" WHERE number = %s', (flight_form.number.data,))
                        flash('Рейс успешно удален', 'success')
                    except Exception:
                        flash('Невозможно удалить рейс', 'danger')
                        con.rollback()
    # Изменить рейс
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
                                # cur.execute('INSERT INTO  public."flight" VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                #         (flight_form.number.data,flight_form.plane.data,flight_form.departure.data,flight_form.arrival.data,departure_datetime, arrival_datetime,0,flight_form.economy.data,flight_form.buisness.data,flight_form.first.data))
                                try:
                                    cur.execute('UPDATE "flight" SET "plane number" = %s, "departure" = %s, "arrival" = %s, "departure datetime" = %s, "arrival datetime" = %s, "status" = %s, "economy price" = %s, "business price" = %s, "first price" = %s WHERE "number" = %s',
                                        (flight_form.plane.data,flight_form.departure.data,flight_form.arrival.data,departure_datetime, arrival_datetime,flight_form.status.data,flight_form.economy.data,flight_form.buisness.data,flight_form.first.data, flight_form.number.data))
                                    flash('Рейс успешно изменен', 'success')
                                except Exception:
                                    flash('Невозможно изменить рейс', 'danger')
    return render_template('admin/flights.html', title='Редактирование рейсов', form=flight_form, search_bool = False)

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        abort(403)
    registration_form = registrationForm()
    if registration_form.submit.data:
        if registration_form.password.data != registration_form.confirm.data:
            flash ('Пароли не совпадают!', 'danger')
        elif registration_form.birthdate.data > date.today()-relativedelta(years=12):
            flash ('Зарегистрироваться могут только пользователи старше 12 лет!', 'danger')
        else:
            with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
                cur = con.cursor()
                user = cur.execute('SELECT * FROM public."user" WHERE "login" = %s', (registration_form.login.data,)).fetchone()
                if user:
                    flash ('Пользователь с таким именем уже есть!', 'danger')
                else:
                    password_hash = generate_password_hash(registration_form.password.data)
                    cur.execute('INSERT INTO "user" VALUES (%s, %s, %s)', (registration_form.login.data,password_hash, registration_form.birthdate.data))
                    flash(f'Вы успешно зарегистрированы, {registration_form.login.data}', 'success')
                    return redirect(url_for('login'))
    return render_template('user/login_registration.html', title='Регистрация', form=registration_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
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

@app.route('/account', methods=['GET', 'POST'])
def account():
    account_form=accountForm()
    if not current_user.is_authenticated or current_user.role != 1:
        abort(403)
    if account_form.changeData.data:
        return redirect(url_for('accountChange'))
    return render_template('user/account.html', title='Личный кабинет', form=account_form)

@app.route('/account/change', methods=['GET', 'POST'])
def accountChange():
    accountChange_form=accountChangeForm()
    if not current_user.is_authenticated or current_user.role != 1:
        abort(403)
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
    if accountChange_form.submit.data:
        pas_bool = False
        birthdate = res[3]
        if accountChange_form.password.data or accountChange_form.confirm.data:
            if len(accountChange_form.password.data) < 3 or len(accountChange_form.submit.data) < 3:
                flash('Пароль должен состоять минимум из 3 символов!', 'danger')
            elif accountChange_form.password.data != accountChange_form.submit.data: 
                flash('Пароли не совпадают!', 'danger')
            else:
                pas_bool = True
        
        if accountChange_form.birthdate.data > date.today()-relativedelta(years=12):
            flash ('Зарегистрированными могут быть только пользователи старше 12 лет!', 'danger')
        else:
            birthdate = accountChange_form.birthdate.data
        
    return render_template('user/account_change.html', title='Изменение данных', form=accountChange_form)