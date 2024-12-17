from flask import Flask
from app.config import Config
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap5(app)
login_manager = LoginManager()
login_manager.init_app(app)

from app import routes
