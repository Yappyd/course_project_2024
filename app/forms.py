from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, DateField, IntegerField, SelectField, SubmitField, validators, PasswordField, DateTimeField, TimeField, RadioField
from wtforms.validators import Optional, NumberRange, ValidationError, Regexp, DataRequired
from datetime import date

def validate_dates(form, field):
    # Получаем значения из полей
    departure_date = form.date.data
    return_date = form.second_date.data
    ret = form.ret_ticket.data
    # Проверка, что оба значения больше текущей даты
    if departure_date <= date.today():
        raise ValidationError('Дата вылета должна быть позже сегодняшнего дня.')

    # Проверка, что дата вылета больше, чем дата возвращения
    if ret and return_date and departure_date > return_date:
        raise ValidationError('Дата вылета должна быть раньше даты возвращения.')

def validate_age(form, field):
    today = date.today()
    min_age_date = today.replace(year=today.year - 12)

    # Если возраст меньше 12 лет
    if field.data > min_age_date:
        raise ValidationError('Зарегистрированными могут только пользователи старше 12 лет!')

# Главная страница
class flight_search(FlaskForm):
    departure = SelectField('Вылет', coerce=str)
    arrival = SelectField('Прилет', coerce=str)
    date = DateField('Дата вылета', format='%Y-%m-%d', validators=[validators.InputRequired(), validate_dates])
    ret_ticket = BooleanField('Нужен обратный билет?' , render_kw={"id": "show-date-checkbox"})
    second_date = DateField('Дата вылета обратно', format='%Y-%m-%d',validators=[validators.InputRequired()], render_kw={"id": "name-input"})
    choice = RadioField(choices=[('up', 'Фильтровать по возрастанию цены'), ('down', 'Фильтровать по убыванию цены')],
    default='up',  # Значение по умолчанию
    validators=[DataRequired()])
    submit = SubmitField('Показать рейсы')
    book = SubmitField('Забронировать')

# Форма авторизации
class loginForm(FlaskForm):
    username = StringField('Логин', [validators.InputRequired()], render_kw={"autocomplete": "off"})
    password = PasswordField('Пароль', [validators.InputRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

# Панель админа
class adminInterface(FlaskForm):
    flights = SubmitField ('Рейсы')
    models = SubmitField ('Модели самолетов')
    planes = SubmitField ('Самолеты')
    countries = SubmitField ('Страны')
    cities = SubmitField ('Города')
    airports = SubmitField ('Аэропорты')

# Редактирование моделей самолетов
class adminModels(FlaskForm):
    name = StringField('Название модели', render_kw={"autocomplete": "off"}, validators=[Optional()])
    economy = IntegerField('Эконом класс', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    buisness = IntegerField('Бизнес класс', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    first = IntegerField('Первый класс', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_models = SubmitField('Показать модели')
    hide_models = SubmitField('Скрыть модели')

# Редактирование самолетов
class adminPlanes(FlaskForm):
    number = StringField('Номер модели', render_kw={"autocomplete": "off"},
                          validators=[Optional()])
    model = SelectField('Модель', coerce=str)
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_planes = SubmitField('Показать самолеты')
    hide_planes = SubmitField('Скрыть самолеты')

# Редактирование стран
class adminСountries(FlaskForm):
    name = StringField('Название страны', render_kw={"autocomplete": "off"}, validators=[Optional()])
    visa = BooleanField('Необходимость визы')
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_countries = SubmitField('Показать страны')
    hide_countries = SubmitField('Скрыть страны')

# Редактирование городов
class adminСities(FlaskForm):
    name = StringField('Название города', render_kw={"autocomplete": "off"}, validators=[Optional()])
    country = SelectField('Страна', coerce=str)
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_cities = SubmitField('Показать города')
    hide_cities = SubmitField('Скрыть города')

# Редактирование аэропортов
class adminAirports(FlaskForm):
    code = StringField('Код аэропорта', render_kw={"autocomplete": "off"}, validators=[Optional()])
    name = StringField('Название аэропорта', render_kw={"autocomplete": "off"}, validators=[Optional()])
    city = SelectField('Страна', coerce=str)
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_airports = SubmitField('Показать аэропорты')
    hide_airports = SubmitField('Скрыть аэропорты')

# Редактирование рейсов
class adminFlights(FlaskForm):
    number =  SelectField('Рейс', coerce=str, default=-1)
    plane = SelectField('Самолет', coerce=str, default=-1)
    departure = SelectField('Место вылета', coerce=str, default=-1)
    arrival = SelectField('Место прилета', coerce=str, default=-1)
    date = DateField('Дата вылета', format='%Y-%m-%d', validators=[Optional()])
    # time = TimeField('Время вылета',format='%H:%M', validators=[Optional()])
    # travel_time = TimeField('Время в пути',format='%H:%M', validators=[Optional()])
    status = SelectField('Статус', coerce=str, choices=[(-1, 'Выберите статус'),(0, 'Запланирован'), (1, 'В полете'), (2, 'Перенесен'), (3, 'Отменен'), (4, 'Выполнен')])
    # economy = IntegerField('Цена эконом класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    # buisness = IntegerField('Цена бизнес класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    # first = IntegerField('Цена первого класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    add = SubmitField('Добавить')
    # delete = SubmitField('Удалить')
    # change = SubmitField('Изменить')
    show_flights = SubmitField('Показать рейсы')


class add_adminFlights(FlaskForm):
    number = StringField('Номер рейса', render_kw={"autocomplete": "off"})
    plane = SelectField('Самолет', coerce=str, default=-1)
    departure = SelectField('Место вылета', coerce=str, default=-1)
    arrival = SelectField('Место прилета', coerce=str, default=-1)
    date = DateField('Дата вылета', format='%Y-%m-%d')
    time = TimeField('Время вылета',format='%H:%M')
    travel_time = TimeField('Время в пути',format='%H:%M')
    status = SelectField('Статус', coerce=str, choices=[(0, 'Запланирован'), (1, 'В полете'), (2, 'Перенесен'), (3, 'Отменен'), (4, 'Выполнен')])
    economy = IntegerField('Цена эконом класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    buisness = IntegerField('Цена бизнес класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    first = IntegerField('Цена первого класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    add = SubmitField('Добавить')
    back = SubmitField('Назад')

class change_adminFlights(FlaskForm):
    number = StringField('Номер рейса', render_kw={"autocomplete": "off"}, validators=[Optional()])
    plane = SelectField('Самолет', coerce=str, default=-1)
    departure = SelectField('Место вылета', coerce=str, default=-1)
    arrival = SelectField('Место прилета', coerce=str, default=-1)
    date = DateField('Дата вылета', format='%Y-%m-%d')
    time = TimeField('Время вылета',format='%H:%M')
    travel_time = TimeField('Время в пути',format='%H:%M')
    status = SelectField('Статус', coerce=str, choices=[(0, 'Запланирован'), (1, 'В полете'), (2, 'Перенесен'), (3, 'Отменен'), (4, 'Выполнен')])
    economy = IntegerField('Цена эконом класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    buisness = IntegerField('Цена бизнес класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    first = IntegerField('Цена первого класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    change = SubmitField('Изменить')
    back = SubmitField('Назад')

# Форма регистрации
class registrationForm(FlaskForm):
    login = StringField('Имя пользователя', validators=[validators.InputRequired(),validators.Length(min=3, max=25)], render_kw={"autocomplete": "off"})
    password = PasswordField('Пароль', validators=[validators.InputRequired(),
                                        validators.Length(min=3, max=100),
                                        validators.EqualTo('confirm', message='Пароли должны совпадать')])
    confirm  = PasswordField('Повторите пароль', validators=[validators.InputRequired(), validators.Length(min=3, max=100)], render_kw={"autocomplete": "off"})
    birthdate = DateField('Дата рождения', format='%Y-%m-%d', validators=[validators.InputRequired(), validate_age])
    submit = SubmitField('Зарегистрироваться')

# Личный кабинет
class accountForm(FlaskForm):
    money = IntegerField('Счёт', default=0, render_kw={"autocomplete": "off"}, validators=[validators.InputRequired(), NumberRange(min=0)])
    change_money = SubmitField('Изменить счёт')
    change_data = SubmitField('Изменение данных аккаунта')
    change_booking = SubmitField('Подробнее о брони')

# Изменение персональных данных
class accountChangeForm(FlaskForm):
    login = StringField('Имя пользователя', validators=[validators.Length(min=3, max=25),validators.InputRequired()], render_kw={"autocomplete": "off"})
    password = PasswordField('Пароль', validators=[validators.Optional(),
                                        validators.Length(min=3, max=100),
                                        validators.EqualTo('confirm', message='Пароли должны совпадать')])
    confirm  = PasswordField('Повторите пароль', validators=[validators.Optional(), validators.Length(min=3, max=100)], render_kw={"autocomplete": "off"})
    birthdate = DateField('Дата рождения', format='%Y-%m-%d', validators=[validators.InputRequired(), validate_age])
    surname = StringField('Фамилия', validators=[Optional()], render_kw={"autocomplete": "off"})
    name = StringField('Имя', validators=[Optional()], render_kw={"autocomplete": "off"})
    patronymic = StringField('Отчество', validators=[Optional()], render_kw={"autocomplete": "off"})
    email = StringField('E-mail', [Optional(), validators.Email()], render_kw={"autocomplete": "off"})
    phone = StringField('Телефон', validators=[
        Optional(),
        Regexp(r'^\+7\d{10}$', message='Введите действующий номер телефона')
    ], render_kw={"autocomplete": "off", "id": "phone-input"})
    submit = SubmitField('Изменить данные')

# Подтвержжение бронирования
class confimBooking(FlaskForm):
    money = IntegerField('Счёт', default=0, render_kw={"autocomplete": "off"}, validators=[validators.InputRequired(), NumberRange(min=0)])
    change_money = SubmitField('Изменить счёт')
    pay = BooleanField('Оплатить сразу?')
    submit = SubmitField('Подтвердить бронь')

# Изменение бронирования
class changeBookingForm(FlaskForm):
    pay = SubmitField('Оплатить')
    change_class = SubmitField('Изменить класс')
    delete = SubmitField('Удалить бронь')