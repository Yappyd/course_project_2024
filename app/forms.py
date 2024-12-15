from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, DateField, IntegerField, SelectField, SubmitField, validators
from wtforms.validators import Optional

class flight_search(FlaskForm):
    depature = SelectField('Вылет*', coerce=str)
    arrival = SelectField('Прилет*', coerce=str)
    date = DateField('Дата вылета', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Сохранить')
