from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, DateField, IntegerField, SelectField, SubmitField, validators, PasswordField, DateTimeField, TimeField
from wtforms.validators import Optional, NumberRange

class flight_search(FlaskForm):
    departure = SelectField('Вылет', coerce=str)
    arrival = SelectField('Прилет', coerce=str)
    date = DateField('Дата вылета', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Показать рейсы')

class loginForm(FlaskForm):
    username = StringField('Логин', [validators.InputRequired()], render_kw={"autocomplete": "off"})
    password = PasswordField('Пароль', [validators.InputRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class adminInterface(FlaskForm):
    flights = SubmitField ('Рейсы')
    models = SubmitField ('Модели самолетов')
    planes = SubmitField ('Самолеты')
    countries = SubmitField ('Страны')
    cities = SubmitField ('Города')
    airports = SubmitField ('Аэропорты')

class adminModels(FlaskForm):
    name = StringField('Название модели', render_kw={"autocomplete": "off"}, validators=[Optional()])
    economy = IntegerField('Эконом класс', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    buisness = IntegerField('Бизнес класс', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    first = IntegerField('Первый 1.Kла$', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_models = SubmitField('Показать модели')
    hide_models = SubmitField('Скрыть модели')

class adminPlanes(FlaskForm):
    number = StringField('Номер модели', render_kw={"autocomplete": "off"},
                          validators=[Optional()])
    model = SelectField('Модель', coerce=str)
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_planes = SubmitField('Показать самолеты')
    hide_planes = SubmitField('Скрыть самолеты')

class adminСountries(FlaskForm):
    name = StringField('Название страны', render_kw={"autocomplete": "off"}, validators=[Optional()])
    visa = BooleanField('Необходимость визы')
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_countries = SubmitField('Показать страны')
    hide_countries = SubmitField('Скрыть страны')

class adminСities(FlaskForm):
    name = StringField('Название города', render_kw={"autocomplete": "off"}, validators=[Optional()])
    country = SelectField('Страна', coerce=str)
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_cities = SubmitField('Показать города')
    hide_cities = SubmitField('Скрыть города')

class adminAirports(FlaskForm):
    code = StringField('Код аэропорта', render_kw={"autocomplete": "off"}, validators=[Optional()])
    name = StringField('Название аэропорта', render_kw={"autocomplete": "off"}, validators=[Optional()])
    city = SelectField('Страна', coerce=str)
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    show_airports = SubmitField('Показать аэропорты')
    hide_airports = SubmitField('Скрыть аэропорты')

class adminFlights(FlaskForm):
    number = StringField('Номер рейса', render_kw={"autocomplete": "off"}, validators=[Optional()])
    plane = SelectField('Самолет', coerce=str)
    departure = SelectField('Место вылета', coerce=str)
    arrival = SelectField('Место прилета', coerce=str)
    date = DateField('Дата вылета', format='%Y-%m-%d', validators=[Optional()])
    time = TimeField('Время вылета',format='%H:%M', validators=[Optional()])
    travel_time = TimeField('Время в пути',format='%H:%M', validators=[Optional()])
    status = SelectField('Статус', coerce=str, choices=[(0, 'Запланирован'), (1, 'В полете'), (2, 'Перенесен'), (3, 'Отменен'), (4, 'Отменен')])
    economy = IntegerField('Цена эконом класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    buisness = IntegerField('Цена бизнес класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    first = IntegerField('Цена первого класса', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    change = SubmitField('Изменить')
    check_number = BooleanField('Учитывать номер рейса')
    check_plane = BooleanField('Учитывать самолет')
    check_departure = BooleanField('Учитывать место вылета')
    check_arrival = BooleanField('Учитывать место прилета')
    check_date = BooleanField('Учитывать дату вылета')
    check_status = BooleanField('Учитывать статус')
    show_flights = SubmitField('Показать рейсы')
    hide_flights = SubmitField('Скрыть рейсы')

class registrationForm(FlaskForm):
    login = StringField('Имя пользователя', validators=[validators.Length(min=3, max=25)], render_kw={"autocomplete": "off"})
    password = PasswordField('Пароль', validators=[ validators.Length(min=3, max=100)])
    confirm  = PasswordField('Повторите пароль', validators=[ validators.Length(min=3, max=100)], render_kw={"autocomplete": "off"})
    birthdate = DateField('Дата рождения', format='%Y-%m-%d', validators=[validators.InputRequired()])
    submit = SubmitField('Зарегистрироваться')

class accountForm(FlaskForm):
    changeData = SubmitField('Изменение данных аккаунта')

class accountChangeForm(FlaskForm):
    login = StringField('Имя пользователя', validators=[validators.Length(min=3, max=25),validators.InputRequired()], render_kw={"autocomplete": "off"})
    password = PasswordField('Пароль', validators=[Optional(), validators.Length(min=3, max=100)])
    confirm  = PasswordField('Повторите пароль', validators=[Optional(), validators.Length(min=3, max=100)], render_kw={"autocomplete": "off"})
    birthdate = DateField('Дата рождения', format='%Y-%m-%d', validators=[validators.InputRequired()])
    surname = StringField('Фамилия', validators=[Optional()], render_kw={"autocomplete": "off"})
    name = StringField('Имя', validators=[Optional()], render_kw={"autocomplete": "off"})
    patronymic = StringField('Отчество', validators=[Optional()], render_kw={"autocomplete": "off"})
    email = StringField('E-mail', [Optional(), validators.Email()])
    phone = StringField('Телефон', validators=[Optional(), validators.Length(11)], render_kw={"autocomplete": "off"})
    submit = SubmitField('Изменить данные')