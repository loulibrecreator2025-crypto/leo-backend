"""
Routes d'authentification pour l'application Léo.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, db
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Inscription d'un nouvel utilisateur.
    """
    try:
        data = request.get_json()
        
        # Validation des données
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} requis'}), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        role = data.get('role', 'user')  # 'user' ou 'pro'
        
        # Vérification que l'utilisateur n'existe pas déjà
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email déjà utilisé'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Nom d\'utilisateur déjà utilisé'}), 400
        
        # Validation du mot de passe (minimum 8 caractères)
        if len(password) < 8:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 8 caractères'}), 400
        
        # Création du nouvel utilisateur
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Génération du token JWT
        access_token = create_access_token(
            identity=new_user.id,
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'success': True,
            'message': 'Utilisateur créé avec succès',
            'access_token': access_token,
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Connexion d'un utilisateur.
    """
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400
        
        email = data['email']
        password = data['password']
        
        # Recherche de l'utilisateur
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
        
        # Génération du token JWT
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=7)
        )
        
        return jsonify({
            'success': True,
            'message': 'Connexion réussie',
            'access_token': access_token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Récupère le profil de l'utilisateur connecté.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Met à jour le profil de l'utilisateur connecté.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        
        # Mise à jour des champs autorisés
        if 'username' in data:
            # Vérifier que le nouveau nom d'utilisateur n'est pas déjà pris
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Nom d\'utilisateur déjà utilisé'}), 400
            user.username = data['username']
        
        if 'email' in data:
            # Vérifier que le nouvel email n'est pas déjà pris
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Email déjà utilisé'}), 400
            user.email = data['email']
        
        if 'preferences' in data:
            user.preferences = data['preferences']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profil mis à jour avec succès',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change le mot de passe de l'utilisateur connecté.
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Mot de passe actuel et nouveau mot de passe requis'}), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Vérification du mot de passe actuel
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({'error': 'Mot de passe actuel incorrect'}), 401
        
        # Validation du nouveau mot de passe
        if len(new_password) < 8:
            return jsonify({'error': 'Le nouveau mot de passe doit contenir au moins 8 caractères'}), 400
        
        # Mise à jour du mot de passe
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mot de passe changé avec succès'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    """
    Supprime le compte de l'utilisateur connecté (droit à l'oubli).
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        # Suppression de toutes les données associées
        from src.models.message import Message
        from src.models.judgment import Judgment
        
        Message.query.filter_by(sender_id=user_id).delete()
        Judgment.query.filter_by(user_id=user_id).delete()
        
        # Suppression de l'utilisateur
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Compte supprimé avec succès'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

