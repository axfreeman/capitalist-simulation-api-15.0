import os
from configparser import ConfigParser

# TODO get this working
config = ConfigParser()
config.read('config.cfg')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SQLALCHEMY_DATABASE_URL= "sqlite:///./sql_app.db"


