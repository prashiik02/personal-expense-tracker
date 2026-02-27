# backend/auth/routes.py

from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from auth.schemas import RegisterSchema, LoginSchema
from auth.services import register_user, login_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():

    try:
        data = RegisterSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    result, error = register_user(data)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(result), 201


@auth_bp.route("/login", methods=["POST"])
def login():

    try:
        data = LoginSchema(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

    result, error = login_user(data)

    if error:
        return jsonify({"error": error}), 401

    return jsonify(result), 200