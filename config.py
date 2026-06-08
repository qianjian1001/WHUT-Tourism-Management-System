import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'travel-agency-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "travel.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
