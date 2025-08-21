import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth_routes import auth_bp
from src.routes.ai_routes import ai_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///leo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'ton-secret-super-secure'

CORS(app)
JWTManager(app)
db.init_app(app)

# Enregistrement des routes
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(ai_bp, url_prefix="/api/ai")

@app.route("/")
def index():
    return {"message": "Bienvenue sur le backend de Léo 👋"}

# Création automatique de la base au démarrage (Render + Gunicorn)
with app.app_context():
    db.create_all()