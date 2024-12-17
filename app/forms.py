from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, DateField, IntegerField, SelectField, SubmitField, validators, PasswordField
from wtforms.validators import Optional, NumberRange

class flight_search(FlaskForm):
    depature = SelectField('Вылет*', coerce=str)
    arrival = SelectField('Прилет*', coerce=str)
    date = DateField('Дата вылета', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Сохранить')

class LoginForm(FlaskForm):
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
    buisness = IntegerField('Бизнесс класс', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    first = IntegerField('Первый 1.Kла$', default=0, render_kw={"autocomplete": "off"}, validators=[Optional(), NumberRange(min=0)])
    add = SubmitField('Добавить')
    delete = SubmitField('Удалить')
    change = SubmitField('Изменить')
    show_flights = SubmitField('Показать модели')
    hide_flights = SubmitField('Скрыть модели')