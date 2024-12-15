import psycopg
from flask import render_template, redirect, flash, url_for
from app import app
from app.forms import flight_search

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
        
        if get_flights_form.validate_on_submit():
            if get_flights_form.date.data is None:
                get_flights = cur.execute('SELECT * FROM public.flight WHERE departure = %s AND arrival = %s',(get_flights_form.depature.data, get_flights_form.arrival.data))
            else:
                get_flights = cur.execute('SELECT * FROM public.flight WHERE departure = %s AND arrival = %s AND DATE("departure datetime") = %s',(get_flights_form.depature.data, get_flights_form.arrival.data, get_flights_form.date.data))
            get_flights=get_flights.fetchall()
            return render_template('index.html', title='Главная', form = get_flights_form, search_bool = True, flights = get_flights)
        
        return render_template('index.html', title='Главная', form = get_flights_form, search_bool = False)

@app.route('/clients', methods=['GET', 'POST'])
def show_clients():
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        users = cur.execute('SELECT * FROM public."user"').fetchall()
        return render_template('clients.html', title='Все пользователи', client_names=users)
    
@app.route('/fligths', methods=['GET', 'POST'])
def show_flights():
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        get_flights = cur.execute('SELECT * FROM public.flight').fetchall()
        return render_template('flights.html', title='Все рейсы', flights=get_flights)