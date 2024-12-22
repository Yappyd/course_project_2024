import psycopg
from app import login_manager
from flask_login import UserMixin
from app import app

class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password = password
        self.role = role

@login_manager.user_loader
def load_user(id):
    with psycopg.connect(host=app.config['DB_SERVER'], user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], dbname=app.config['DB_NAME']) as con:
        cur = con.cursor()
        user  = cur.execute('SELECT login, password '
                            'FROM public."user" '
                            'WHERE id = %s', (id,)).fetchone()
        if user:
            username, password = user
            return User(id, username, password, 1)
        username, password = cur.execute('SELECT username, password '
                                        'FROM public."admin" '
                                        'WHERE id = %s', (id,)).fetchone()
    return User(id, username, password, 0)