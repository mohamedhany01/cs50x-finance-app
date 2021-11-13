import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configure application
app = Flask(__name__)

"""App configrations"""
app.config["TEMPLATES_AUTO_RELOAD"]             = True                      # Ensure templates are auto-reloaded
app.config["SECRET_KEY"]                        = os.environ.get("SECRET_KEY")        # Add a secret key to enable flashed messages and sessions
app.config["SQLALCHEMY_DATABASE_URI"]           = "sqlite:///finance.db"    # A relative path of sqlite db
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]    = False
database = SQLAlchemy(app)

from finance import routes