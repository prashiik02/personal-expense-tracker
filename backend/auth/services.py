# backend/auth/services.py

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models.user_model import User
from models import db


def register_user(data):

    existing = User.query.filter_by(email=data.email).first()
    if existing:
        return None, "User already exists"

    user = User(
        name=data.name,
        email=data.email,
        password=generate_password_hash(data.password),
        monthly_income=data.monthly_income
    )

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "token": token
    }, None


def login_user(data):

    user = User.query.filter_by(email=data.email).first()

    if not user:
        return None, "Invalid email or password"

    if not check_password_hash(user.password, data.password):
        return None, "Invalid email or password"

    token = create_access_token(identity=str(user.id))

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "token": token
    }, None