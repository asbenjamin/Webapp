import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dad21df148eb2c0d147d609246c613fc'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app) #with sqlalchemy we can rep database struc as classes, aka models
bcrypt = Bcrypt(app)
login_manager = LoginManager(app) #add some func.lity in dbase- models.py which handles everything in teh background
login_manager.login_view = 'login' #sets the login route, telling user to login be4 viewing account info
login_manager.login_message_category = 'info' #bootstrap nice blue information alert
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER') #check use of environment variables to hide sensitive info.
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)

from webapp import routes #this is to avoid circular imports, the routes import app after it has been initialised