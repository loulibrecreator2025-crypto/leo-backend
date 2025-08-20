"""
Module de détection émotionnelle pour l'application Léo.
Analyse le ton et le sentiment des messages pour identifier les reproches, 
le sarcasme, l'agressivité passive, les accusations, et la manipulation émotionnelle.
"""

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import re
from typing import Dict, List, Any

class SentimentAnalyzer:
    def __init__(self):
        """
        Initialise le module de détection émotionnelle.
        Utilise un modèle pré-entraîné pour l'analyse des sentiments en français.
        """
        try:
            # Utilisation d'un modèle français pour l'analyse des sentiments
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                tokenizer="nlptown/bert-base-multilingual-uncased-sentiment"
            )
        except Exception as e:
            print(f"Erreur lors du chargement du modèle de sentiment: {e}")
            self.sentiment_pipeline = None
        
        # Mots et expressions déclencheurs pour la détection d'agressivité
        self.trigger_words = {
            'reproches': ['comme d\'habitude', 'encore', 'jamais', 'toujours', 'à cause de toi', 't\'as qu\'à'],
            'sarcasme': ['bien sûr', 'évidemment', 'c\'est ça', 'parfait', 'génial'],
            'accusations': ['tu fais exprès', 'tu mens', 'tu ne comprends rien', 'c\'est ta faute'],
            'manipulation': ['si tu m\'aimais', 'tu ne penses qu\'à toi', 'les enfants vont souffrir']
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyse le sentiment et le ton d'un message.
        
        Args:
            text (str): Le texte à analyser
            
        Returns:
            Dict[str, Any]: Résultat de l'analyse avec sentiment, score et détails
        """
        if not text or not text.strip():
            return {
                'sentiment': 'neutre',
                'score': 0.5,
                'emotion_detected': [],
                'trigger_words_found': [],
                'recommendation': 'Message vide'
            }
        
        result = {
            'sentiment': 'neutre',
            'score': 0.5,
            'emotion_detected': [],
            'trigger_words_found': [],
            'recommendation': ''
        }
        
        # Analyse avec le modèle de sentiment si disponible
        if self.sentiment_pipeline:
            try:
                sentiment_result = self.sentiment_pipeline(text)
                if sentiment_result:
                    label = sentiment_result[0]['label'].lower()
                    score = sentiment_result[0]['score']
                    
                    # Mapping des labels vers nos catégories
                    if 'negative' in label or '1' in label or '2' in label:
                        result['sentiment'] = 'hostile'
                    elif 'positive' in label or '4' in label or '5' in label:
                        result['sentiment'] = 'positif'
                    else:
                        result['sentiment'] = 'neutre'
                    
                    result['score'] = score
            except Exception as e:
                print(f"Erreur lors de l'analyse de sentiment: {e}")
        
        # Détection des mots déclencheurs
        text_lower = text.lower()
        for category, words in self.trigger_words.items():
            found_words = [word for word in words if word in text_lower]
            if found_words:
                result['emotion_detected'].append(category)
                result['trigger_words_found'].extend(found_words)
        
        # Détection de patterns spécifiques
        patterns = self._detect_patterns(text)
        result['emotion_detected'].extend(patterns)
        
        # Génération de recommandations
        result['recommendation'] = self._generate_recommendation(result)
        
        return result
    
    def _detect_patterns(self, text: str) -> List[str]:
        """
        Détecte des patterns spécifiques dans le texte.
        
        Args:
            text (str): Le texte à analyser
            
        Returns:
            List[str]: Liste des patterns détectés
        """
        patterns_detected = []
        text_lower = text.lower()
        
        # Détection de questions rhétoriques agressives
        if re.search(r'\?.*\?', text) or text_lower.count('?') > 2:
            patterns_detected.append('questions_rhetoriques')
        
        # Détection d'exclamations excessives
        if text.count('!') > 2:
            patterns_detected.append('exclamations_excessives')
        
        # Détection de généralisation
        generalization_words = ['tous', 'toutes', 'personne', 'rien', 'jamais', 'toujours']
        if any(word in text_lower for word in generalization_words):
            patterns_detected.append('generalisation')
        
        # Détection de comparaisons négatives
        if any(phrase in text_lower for phrase in ['contrairement à', 'au moins lui', 'elle au moins']):
            patterns_detected.append('comparaison_negative')
        
        return patterns_detected
    
    def _generate_recommendation(self, analysis_result: Dict[str, Any]) -> str:
        """
        Génère une recommandation basée sur l'analyse.
        
        Args:
            analysis_result (Dict[str, Any]): Résultat de l'analyse
            
        Returns:
            str: Recommandation pour l'utilisateur
        """
        if analysis_result['sentiment'] == 'hostile' or analysis_result['emotion_detected']:
            return "Ce message contient des signaux de tension. Voulez-vous l'adoucir ?"
        elif analysis_result['sentiment'] == 'neutre':
            return "Message neutre, prêt à être envoyé."
        else:
            return "Message positif, bon pour la communication."
    
    def get_mirror_feedback(self, text: str) -> Dict[str, Any]:
        """
        Génère un feedback pour le mode miroir.
        
        Args:
            text (str): Le texte à analyser
            
        Returns:
            Dict[str, Any]: Feedback pour le mode miroir
        """
        analysis = self.analyze_sentiment(text)
        
        # Création du graphique de perception
        perception_scores = {
            'agressif': 0.1,
            'flou': 0.2,
            'informatif': 0.4,
            'rassurant': 0.3
        }
        
        # Ajustement des scores basé sur l'analyse
        if analysis['sentiment'] == 'hostile':
            perception_scores['agressif'] = 0.7
            perception_scores['informatif'] = 0.2
            perception_scores['rassurant'] = 0.1
        elif analysis['emotion_detected']:
            perception_scores['agressif'] = 0.4
            perception_scores['flou'] = 0.4
            perception_scores['informatif'] = 0.2
        
        return {
            'perception_scores': perception_scores,
            'mirror_message': "Et si on te l'envoyait, tu le vivrais comment ?",
            'analysis': analysis
        }

