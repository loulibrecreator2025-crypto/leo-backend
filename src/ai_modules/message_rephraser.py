"""
Module de reformulation intelligente pour l'application Léo.
Transforme les messages conflictuels en communications neutres et apaisées,
tout en préservant le contenu informatif.
"""

from openai import OpenAI
import re
from typing import Dict, List, Any, Optional
from src.ai_modules.sentiment_analyzer import SentimentAnalyzer

class MessageRephraser:
    def __init__(self):
        """
        Initialise le module de reformulation intelligente.
        """
        self.sentiment_analyzer = SentimentAnalyzer()
        self.client = OpenAI()  # Utilise la variable d'environnement OPENAI_API_KEY
        
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
            'tu ne comprends rien': 'il y a peut-être besoin de clarification'
        }
        
        # Phrases de recentrage sur l'enfant
        self.child_focused_phrases = [
            "dans l'intérêt de l'enfant",
            "pour le bien-être de notre enfant",
            "selon ce qui a été convenu",
            "pour éviter un malentendu",
            "afin de maintenir la stabilité pour l'enfant"
        ]
    
    def rephrase_message(self, original_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Reformule un message en appliquant les règles d'apaisement et de neutralité.
        
        Args:
            original_message (str): Le message original à reformuler
            context (Optional[Dict]): Contexte additionnel (jugement, historique, etc.)
            
        Returns:
            Dict[str, Any]: Résultat de la reformulation avec plusieurs options
        """
        if not original_message or not original_message.strip():
            return {
                'original': original_message,
                'rephrased_options': [],
                'analysis': {},
                'recommendation': 'Message vide'
            }
        
        # Analyse du sentiment du message original
        sentiment_analysis = self.sentiment_analyzer.analyze_sentiment(original_message)
        
        # Application des règles typées
        rule_based_version = self._apply_typed_rules(original_message)
        
        # Génération avec LLM (OpenAI)
        llm_versions = self._generate_with_llm(original_message, sentiment_analysis, context)
        
        # Combinaison et validation des versions
        final_options = self._combine_and_validate(rule_based_version, llm_versions, sentiment_analysis)
        
        return {
            'original': original_message,
            'rephrased_options': final_options,
            'analysis': sentiment_analysis,
            'recommendation': self._generate_usage_recommendation(sentiment_analysis, final_options)
        }
    
    def _apply_typed_rules(self, message: str) -> str:
        """
        Applique les règles typées d'apaisement lexical et structurel.
        
        Args:
            message (str): Le message à traiter
            
        Returns:
            str: Message après application des règles
        """
        processed_message = message
        
        # Règles d'apaisement lexical
        for trigger, replacement in self.trigger_replacements.items():
            processed_message = re.sub(
                re.escape(trigger), 
                replacement, 
                processed_message, 
                flags=re.IGNORECASE
            )
        
        # Suppression des points d'exclamation excessifs
        processed_message = re.sub(r'!{2,}', '!', processed_message)
        processed_message = re.sub(r'!', '.', processed_message)
        
        # Suppression des questions rhétoriques agressives
        processed_message = re.sub(r'\?{2,}', '?', processed_message)
        
        # Nettoyage des espaces multiples
        processed_message = re.sub(r'\s+', ' ', processed_message).strip()
        
        return processed_message
    
    def _generate_with_llm(self, message: str, sentiment_analysis: Dict, context: Optional[Dict] = None) -> List[str]:
        """
        Génère des reformulations en utilisant un LLM (OpenAI).
        
        Args:
            message (str): Le message à reformuler
            sentiment_analysis (Dict): Analyse du sentiment
            context (Optional[Dict]): Contexte additionnel
            
        Returns:
            List[str]: Liste des reformulations générées
        """
        try:
            # Construction du prompt
            system_prompt = """Tu es un assistant spécialisé dans la médiation parentale. 
            Ton rôle est de reformuler les messages entre parents séparés pour les rendre neutres, 
            apaisés et centrés sur l'intérêt de l'enfant. 

            Règles à respecter:
            - Préserver le contenu informatif essentiel
            - Éliminer l'agressivité, les reproches et les accusations
            - Utiliser un ton neutre et respectueux
            - Centrer sur l'intérêt de l'enfant quand c'est pertinent
            - Phrases courtes et claires
            - Une seule information principale par message
            - Pas de points d'exclamation ni de questions rhétoriques"""
            
            user_prompt = f"""Message à reformuler: "{message}"
            
            Sentiment détecté: {sentiment_analysis.get('sentiment', 'neutre')}
            Émotions détectées: {', '.join(sentiment_analysis.get('emotion_detected', []))}
            
            Propose 2 reformulations différentes, numérotées 1. et 2."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Extraction des reformulations numérotées
            reformulations = []
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('1.') or line.startswith('2.'):
                    reformulation = line[2:].strip()
                    if reformulation:
                        reformulations.append(reformulation)
            
            return reformulations[:2]  # Maximum 2 reformulations
            
        except Exception as e:
            print(f"Erreur lors de la génération LLM: {e}")
            return []
    
    def _combine_and_validate(self, rule_based: str, llm_versions: List[str], sentiment_analysis: Dict) -> List[Dict[str, Any]]:
        """
        Combine et valide les différentes versions de reformulation.
        
        Args:
            rule_based (str): Version basée sur les règles
            llm_versions (List[str]): Versions générées par LLM
            sentiment_analysis (Dict): Analyse du sentiment
            
        Returns:
            List[Dict[str, Any]]: Options finales validées
        """
        options = []
        
        # Ajout de la version basée sur les règles
        if rule_based and rule_based.strip():
            options.append({
                'text': rule_based,
                'method': 'rules_based',
                'confidence': 0.8,
                'description': 'Reformulation basée sur les règles d\'apaisement'
            })
        
        # Ajout des versions LLM
        for i, llm_version in enumerate(llm_versions):
            if llm_version and llm_version.strip():
                options.append({
                    'text': llm_version,
                    'method': 'llm_generated',
                    'confidence': 0.9,
                    'description': f'Reformulation IA - Option {i+1}'
                })
        
        # Validation et filtrage
        validated_options = []
        for option in options:
            if self._validate_reformulation(option['text'], sentiment_analysis):
                validated_options.append(option)
        
        # Limitation à 3 options maximum
        return validated_options[:3]
    
    def _validate_reformulation(self, reformulated_text: str, original_analysis: Dict) -> bool:
        """
        Valide qu'une reformulation respecte les critères de qualité.
        
        Args:
            reformulated_text (str): Texte reformulé à valider
            original_analysis (Dict): Analyse du message original
            
        Returns:
            bool: True si la reformulation est valide
        """
        if not reformulated_text or len(reformulated_text.strip()) < 5:
            return False
        
        # Vérification qu'il n'y a pas de mots déclencheurs restants
        text_lower = reformulated_text.lower()
        for trigger in self.trigger_replacements.keys():
            if trigger in text_lower:
                return False
        
        # Vérification de la longueur (pas trop long)
        if len(reformulated_text) > 500:
            return False
        
        # Vérification qu'il n'y a pas d'exclamations multiples
        if '!!' in reformulated_text or '???' in reformulated_text:
            return False
        
        return True
    
    def _generate_usage_recommendation(self, sentiment_analysis: Dict, options: List[Dict]) -> str:
        """
        Génère une recommandation d'usage pour l'utilisateur.
        
        Args:
            sentiment_analysis (Dict): Analyse du sentiment
            options (List[Dict]): Options de reformulation
            
        Returns:
            str: Recommandation d'usage
        """
        if not options:
            return "Aucune reformulation disponible. Le message original peut être envoyé tel quel."
        
        if sentiment_analysis.get('sentiment') == 'hostile':
            return "Votre message contient des éléments de tension. Nous recommandons fortement d'utiliser une des reformulations proposées."
        elif sentiment_analysis.get('emotion_detected'):
            return "Votre message pourrait être mal interprété. Une reformulation pourrait améliorer la communication."
        else:
            return "Votre message est déjà assez neutre. Les reformulations sont optionnelles."
    
    def generate_assisted_responses(self, received_message: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Génère des réponses assistées à un message reçu.
        
        Args:
            received_message (str): Message reçu auquel répondre
            context (Optional[Dict]): Contexte (jugement, historique)
            
        Returns:
            List[Dict[str, Any]]: Liste de réponses suggérées
        """
        try:
            system_prompt = """Tu es un assistant spécialisé dans la médiation parentale. 
            Génère des réponses appropriées à des messages entre parents séparés.
            
            Les réponses doivent être:
            - Centrées sur l'intérêt de l'enfant
            - Neutres et respectueuses
            - Informatives et constructives
            - Courtes et claires"""
            
            user_prompt = f"""Message reçu: "{received_message}"
            
            Propose 3 réponses différentes, numérotées 1., 2., et 3."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Extraction des réponses numérotées
            responses = []
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith(('1.', '2.', '3.')):
                    response_text = line[2:].strip()
                    if response_text:
                        responses.append({
                            'text': response_text,
                            'type': 'assisted_response',
                            'focus': 'child_centered'
                        })
            
            return responses[:3]
            
        except Exception as e:
            print(f"Erreur lors de la génération de réponses assistées: {e}")
            return []

