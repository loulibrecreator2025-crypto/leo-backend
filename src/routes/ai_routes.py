"""
Routes API pour les modules IA de l'application Léo.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.ai_modules.sentiment_analyzer import SentimentAnalyzer
from src.ai_modules.message_rephraser_hf import MessageRephraser
from src.ai_modules.legal_processor import LegalProcessor
from src.models.message import Message, db
from src.models.judgment import Judgment
import os

ai_bp = Blueprint('ai', __name__)

# Initialisation des modules IA
sentiment_analyzer = SentimentAnalyzer()
message_rephraser = MessageRephraser()
legal_processor = LegalProcessor()

@ai_bp.route('/analyze-sentiment', methods=['POST'])
@jwt_required()
def analyze_sentiment():
    """
    Analyse le sentiment d'un message.
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400
        
        message = data['message']
        analysis = sentiment_analyzer.analyze_sentiment(message)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/rephrase-message', methods=['POST'])
@jwt_required()
def rephrase_message():
    """
    Reformule un message pour le rendre plus neutre et apaisant.
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400
        
        message = data['message']
        context = data.get('context', None)
        
        result = message_rephraser.rephrase_message(message, context)
        
        # Optionnel: sauvegarder en base si l'utilisateur consent
        user_id = get_jwt_identity()
        if data.get('save_to_history', False):
            new_message = Message(
                sender_id=user_id,
                original_content=message,
                rephrased_content=result['rephrased_options'][0]['text'] if result['rephrased_options'] else None,
                sentiment_analysis_result=result['analysis'],
                consent_to_store=True
            )
            db.session.add(new_message)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/generate-responses', methods=['POST'])
@jwt_required()
def generate_responses():
    """
    Génère des réponses assistées à un message reçu.
    """
    try:
        data = request.get_json()
        if not data or 'received_message' not in data:
            return jsonify({'error': 'Message reçu requis'}), 400
        
        received_message = data['received_message']
        context = data.get('context', None)
        
        responses = message_rephraser.generate_assisted_responses(received_message, context)
        
        return jsonify({
            'success': True,
            'responses': responses
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/mirror-mode', methods=['POST'])
@jwt_required()
def mirror_mode():
    """
    Mode miroir: simule l'impact émotionnel d'un message avant envoi.
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message requis'}), 400
        
        message = data['message']
        feedback = sentiment_analyzer.get_mirror_feedback(message)
        
        return jsonify({
            'success': True,
            'feedback': feedback
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/process-legal-document', methods=['POST'])
@jwt_required()
def process_legal_document():
    """
    Traite un document juridique pour extraire les informations clés.
    """
    try:
        data = request.get_json()
        if not data or 'document_text' not in data:
            return jsonify({'error': 'Texte du document requis'}), 400
        
        document_text = data['document_text']
        result = legal_processor.process_document(document_text)
        
        # Sauvegarder le résultat en base
        user_id = get_jwt_identity()
        if result['success']:
            new_judgment = Judgment(
                user_id=user_id,
                document_path=data.get('document_path', 'uploaded_document'),
                extracted_data_json=result['extracted_data']
            )
            db.session.add(new_judgment)
            db.session.commit()
            
            result['judgment_id'] = new_judgment.id
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/upload-legal-document', methods=['POST'])
@jwt_required()
def upload_legal_document():
    """
    Upload et traite un fichier de document juridique.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400
        
        # Sauvegarde temporaire du fichier
        upload_folder = '/tmp/leo_uploads'
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)
        
        # Simulation OCR (dans un vrai environnement, utiliser AWS Textract ou Tesseract)
        document_text = legal_processor.simulate_ocr(file_path)
        
        # Traitement du document
        result = legal_processor.process_document(document_text)
        
        # Sauvegarder le résultat en base
        user_id = get_jwt_identity()
        if result['success']:
            new_judgment = Judgment(
                user_id=user_id,
                document_path=file_path,
                extracted_data_json=result['extracted_data']
            )
            db.session.add(new_judgment)
            db.session.commit()
            
            result['judgment_id'] = new_judgment.id
        
        # Nettoyage du fichier temporaire
        os.remove(file_path)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/get-judgments', methods=['GET'])
@jwt_required()
def get_judgments():
    """
    Récupère les jugements traités pour l'utilisateur connecté.
    """
    try:
        user_id = get_jwt_identity()
        judgments = Judgment.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'success': True,
            'judgments': [judgment.to_dict() for judgment in judgments]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/get-message-history', methods=['GET'])
@jwt_required()
def get_message_history():
    """
    Récupère l'historique des messages pour l'utilisateur connecté.
    """
    try:
        user_id = get_jwt_identity()
        messages = Message.query.filter_by(sender_id=user_id, consent_to_store=True).all()
        
        return jsonify({
            'success': True,
            'messages': [message.to_dict() for message in messages]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/delete-message-history', methods=['DELETE'])
@jwt_required()
def delete_message_history():
    """
    Supprime l'historique des messages (droit à l'oubli).
    """
    try:
        user_id = get_jwt_identity()
        Message.query.filter_by(sender_id=user_id).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Historique supprimé avec succès'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

