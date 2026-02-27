import os
from dotenv import load_dotenv

# load .env from backend folder
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:

    # -------------------------
    # Flask core
    # -------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")

    # -------------------------
    # Database
    # -------------------------
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    if not SQLALCHEMY_DATABASE_URI:
        if all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
            SQLALCHEMY_DATABASE_URI = (
                f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
                f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )
        else:
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'expense_tracker.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------
    # JWT
    # -------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    # -------------------------
    # Uploads
    # -------------------------
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")