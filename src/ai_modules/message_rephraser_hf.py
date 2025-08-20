"""
Module de reformulation intelligente des messages
Utilise Hugging Face Transformers pour la reformulation et des règles d'apaisement
Version gratuite pour le déploiement
"""

import re
import logging
from typing import Dict, List, Any, Optional

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageRephraser:
    def __init__(self):
        """Initialise le module de reformulation avec des règles locales"""
        logger.info("Module de reformulation initialisé en mode gratuit (règles locales)")
        
        # Règles d'apaisement lexical
        self.trigger_replacements = {
            'comme d\'habitude': 'comme convenu précédemment',
            'encore': 'à nouveau',
            'jamais': 'rarement',
            'toujours': 'souvent',
            'à cause de toi': 'en raison de cette situation',
            't\'as qu\'à': 'il serait possible de',
            'tu fais exprès': 'il semble y avoir un malentendu',
            'c\'est ta faute': 'cette situation nécessite notre attention',
            'tu ne comprends rien': 'il y a peut-être besoin de clarification',
            'tu m\'énerves': 'cette situation est difficile',
            'arrête de': 'il serait préférable de ne pas',
            'tu dois': 'il serait bien de',
            'pourquoi tu': 'serait-il possible de'
        }
        
        # Phrases de recentrage sur l'enfant
        self.child_focused_phrases = [
            "dans l'intérêt de l'enfant",
            "pour le bien-être de notre enfant",
            "selon ce qui a été convenu",
            "pour éviter un malentendu",
            "afin de maintenir la stabilité pour l'enfant"
        ]
        
        # Réponses types
        self.template_responses = [
            "J'ai bien reçu ton message. Pour le bien de notre enfant, pourrions-nous discuter de cela calmement ?",
            "Merci pour ton message. Dans l'intérêt de notre enfant, je propose que nous trouvions une solution ensemble.",
            "J'ai pris note de ton message. Pour éviter tout malentendu, pourrions-nous clarifier ce point ?",
            "Merci de m'avoir informé. Dans l'intérêt de notre enfant, je vais réfléchir à ta demande.",
            "J'ai bien compris ton message. Pour le bien-être de notre enfant, restons constructifs."
        ]
    
    def detect_triggers(self, text):
        """Détecte les mots et expressions déclencheurs dans le texte"""
        triggers = []
        text_lower = text.lower()
        
        for trigger in self.trigger_replacements.keys():
            if trigger in text_lower:
                triggers.append(trigger)
        
        # Détection d'autres indicateurs de tension
        tension_indicators = ['!', 'MAJUSCULES', 'accusations directes']
        if any(char in text for char in ['!', '?']):
            triggers.append('ponctuation excessive')
        
        if text.isupper():
            triggers.append('majuscules excessives')
        
        return triggers
    
    def apply_calming_rules(self, text):
        """Applique les règles d'apaisement au texte"""
        result = text
        
        # Appliquer les remplacements de déclencheurs
        for trigger, replacement in self.trigger_replacements.items():
            result = re.sub(re.escape(trigger), replacement, result, flags=re.IGNORECASE)
        
        # Règles de transformation grammaticale
        grammar_rules = [
            # Remplacer les accusations directes
            (r'\btu (ne |n\')?(.+?) (jamais|toujours)', r'il serait bien de \2'),
            (r'\btu es (.+)', r'il semble que'),
            (r'\bpourquoi tu (.+)', r'serait-il possible de \1'),
            
            # Supprimer les généralisations
            (r'\btoujours\b', 'parfois'),
            (r'\bjamais\b', 'rarement'),
            
            # Adoucir le ton
            (r'\barrête de (.+)', r'il serait préférable de ne pas \1'),
            (r'\btu dois (.+)', r'il serait bien de \1'),
            
            # Centrer sur l'enfant
            (r'\bc\'est ta faute', 'pour le bien de notre enfant'),
            (r'\bà cause de toi', 'dans l\'intérêt de notre enfant'),
        ]
        
        for pattern, replacement in grammar_rules:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Nettoyage de la ponctuation
        result = re.sub(r'!{2,}', '.', result)  # Remplacer !! par .
        result = re.sub(r'\?{2,}', '?', result)  # Limiter les ?
        result = re.sub(r'\s+', ' ', result).strip()  # Nettoyer les espaces
        
        # Ajouter une formule de politesse si nécessaire
        if not any(word in result.lower() for word in ['merci', 'cordialement', 's\'il te plaît']):
            if not result.endswith('.'):
                result += '.'
            result += ' Merci.'
        
        return result
    
    def rephrase_message(self, original_message, context=None):
        """
        Reformule un message en appliquant les règles d'apaisement
        
        Args:
            original_message (str): Message original à reformuler
            context (dict): Contexte optionnel (jugement, historique)
            
        Returns:
            dict: Résultat de la reformulation
        """
        try:
            if not original_message or not original_message.strip():
                return {
                    'original': original_message,
                    'rephrased_options': [],
                    'analysis': {},
                    'recommendation': 'Message vide'
                }
            
            # Détecter les déclencheurs
            triggers = self.detect_triggers(original_message)
            
            # Appliquer les règles d'apaisement
            calmed_text = self.apply_calming_rules(original_message)
            
            # Créer une version alternative plus formelle
            formal_version = self.create_formal_version(original_message)
            
            # Préparer les options de reformulation
            options = []
            
            if calmed_text != original_message:
                options.append({
                    'text': calmed_text,
                    'method': 'rules_based',
                    'confidence': 0.8,
                    'description': 'Reformulation basée sur les règles d\'apaisement'
                })
            
            if formal_version != calmed_text:
                options.append({
                    'text': formal_version,
                    'method': 'formal_template',
                    'confidence': 0.7,
                    'description': 'Version plus formelle et neutre'
                })
            
            return {
                'original': original_message,
                'rephrased_options': options,
                'analysis': {
                    'triggers_detected': triggers,
                    'sentiment': 'hostile' if len(triggers) > 2 else 'neutre',
                    'emotion_detected': triggers
                },
                'recommendation': self.generate_recommendation(triggers, options)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la reformulation: {e}")
            return {
                'original': original_message,
                'rephrased_options': [],
                'analysis': {'error': str(e)},
                'recommendation': 'Erreur lors de la reformulation'
            }
    
    def create_formal_version(self, message):
        """Crée une version plus formelle du message"""
        # Extraire l'intention principale du message
        if any(word in message.lower() for word in ['récupérer', 'chercher', 'prendre']):
            return "Je souhaiterais organiser la récupération de notre enfant selon les modalités convenues. Merci de me confirmer les détails."
        
        if any(word in message.lower() for word in ['retard', 'en retard', 'attendre']):
            return "Il y a eu un contretemps. Je vous tiendrai informé(e) de l'heure d'arrivée. Merci de votre compréhension."
        
        if any(word in message.lower() for word in ['problème', 'souci', 'difficulté']):
            return "Il semble y avoir une situation qui nécessite notre attention. Pourrions-nous en discuter dans l'intérêt de notre enfant ?"
        
        if any(word in message.lower() for word in ['médecin', 'docteur', 'santé', 'malade']):
            return "Je vous informe d'une question concernant la santé de notre enfant. Merci de me tenir au courant de votre côté également."
        
        # Version générique
        return "J'ai un point à aborder concernant notre enfant. Pourrions-nous en discuter de manière constructive ? Merci."
    
    def generate_recommendation(self, triggers, options):
        """Génère une recommandation d'usage"""
        if len(triggers) > 3:
            return "Votre message contient plusieurs éléments de tension. Nous recommandons fortement d'utiliser une des reformulations proposées."
        elif len(triggers) > 0:
            return "Votre message pourrait être mal interprété. Une reformulation pourrait améliorer la communication."
        elif not options:
            return "Votre message est déjà approprié pour la communication."
        else:
            return "Votre message est assez neutre. Les reformulations sont optionnelles."
    
    def generate_responses(self, message, context=None):
        """
        Génère des réponses suggérées pour un message
        
        Args:
            message (str): Message reçu
            context (dict): Contexte optionnel
            
        Returns:
            list: Liste de réponses suggérées
        """
        # Adapter selon le contexte du message
        if any(word in message.lower() for word in ['urgent', 'important', 'problème']):
            return [
                "J'ai bien reçu ton message urgent. Pour le bien de notre enfant, je vais traiter cela rapidement.",
                "Merci de m'avoir alerté. Dans l'intérêt de notre enfant, nous devons résoudre cela ensemble.",
                "J'ai pris note de l'urgence. Je reviens vers toi rapidement pour le bien-être de notre enfant."
            ]
        
        if any(word in message.lower() for word in ['merci', 'accord', 'ok', 'bien']):
            return [
                "Merci pour ton message. C'est parfait pour notre enfant.",
                "J'ai bien reçu. Merci pour ta collaboration dans l'intérêt de notre enfant.",
                "Parfait, cela convient bien pour le bien-être de notre enfant."
            ]
        
        # Réponses génériques
        return self.template_responses[:3]
    
    def generate_assisted_responses(self, received_message, context=None):
        """
        Génère des réponses assistées à un message reçu
        
        Args:
            received_message (str): Message reçu auquel répondre
            context (dict): Contexte optionnel
            
        Returns:
            list: Liste de réponses suggérées avec métadonnées
        """
        responses = self.generate_responses(received_message, context)
        
        return [
            {
                'text': response,
                'type': 'assisted_response',
                'focus': 'child_centered'
            }
            for response in responses
        ]
    
    def mirror_mode(self, message):
        """
        Mode miroir : analyse l'impact émotionnel potentiel d'un message
        
        Args:
            message (str): Message à analyser
            
        Returns:
            dict: Analyse de l'impact émotionnel
        """
        triggers = self.detect_triggers(message)
        
        # Calculer un score d'impact émotionnel
        impact_score = len(triggers) * 2
        
        # Ajouter des points pour d'autres indicateurs
        if any(char in message for char in ['!', '?']):
            impact_score += 1
        
        if message.isupper():
            impact_score += 3
        
        # Déterminer le niveau d'impact
        if impact_score >= 6:
            impact_level = "Élevé"
            recommendation = "Ce message risque de créer des tensions. Une reformulation est fortement recommandée."
        elif impact_score >= 3:
            impact_level = "Modéré"
            recommendation = "Ce message pourrait être mal perçu. Considérez une reformulation."
        else:
            impact_level = "Faible"
            recommendation = "Ce message semble approprié pour la communication."
        
        return {
            'impact_score': impact_score,
            'impact_level': impact_level,
            'triggers_detected': triggers,
            'recommendation': recommendation,
            'suggested_changes': [
                "Utiliser un ton plus neutre",
                "Éviter les accusations directes",
                "Centrer sur l'intérêt de l'enfant",
                "Ajouter une formule de politesse"
            ] if impact_score > 2 else []
        }

