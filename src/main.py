import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth_routes import auth_bp
from src.routes.ai_routes import ai_bp

