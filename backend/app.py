from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from models import db
from auth.routes import auth_bp
from categorization.routes import categorization_bp
from statements.routes import statements_bp
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)
    with app.app_context():
        db.create_all()
    JWTManager(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(categorization_bp)
    app.register_blueprint(statements_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)