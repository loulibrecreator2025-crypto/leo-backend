"""
Module OCR et NLP juridique pour l'application Léo.
Traite les documents juridiques (jugements, ordonnances) pour extraire
les informations clés de manière structurée.
"""

import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import spacy
from spacy.matcher import Matcher

class LegalProcessor:
    def __init__(self):
        """
        Initialise le module de traitement juridique.
        """
        try:
            # Chargement du modèle spaCy français
            self.nlp = spacy.load("fr_core_news_sm")
        except OSError:
            print("Modèle spaCy français non trouvé. Installation requise: python -m spacy download fr_core_news_sm")
            self.nlp = None
        
        # Patterns pour l'extraction d'informations juridiques
        self.patterns = {
            'garde_alternee': [
                r'garde\s+alternée?',
                r'résidence\s+alternée?',
                r'une\s+semaine\s+sur\s+deux'
            ],
            'jours_garde': [
                r'(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)',
                r'week-?end',
                r'vacances?\s+scolaires?'
            ],
            'horaires': [
                r'\d{1,2}h\d{0,2}',
                r'\d{1,2}:\d{2}',
                r'à\s+\d{1,2}\s*heures?'
            ],
            'lieux': [
                r'domicile\s+(maternel|paternel)',
                r'école\s+de\s+l\'enfant',
                r'lieu\s+de\s+résidence'
            ],
            'interdictions': [
                r'interdit\s+de',
                r'ne\s+peut\s+pas',
                r'défense\s+de',
                r'prohibition\s+de'
            ],
            'obligations': [
                r'à\s+charge\s+pour',
                r'devra',
                r'est\s+tenu\s+de',
                r'obligation\s+de'
            ]
        }
        
        # Mots-clés juridiques français
        self.legal_keywords = [
            'juge aux affaires familiales', 'JAF', 'ordonnance', 'jugement',
            'garde', 'résidence', 'droit de visite', 'hébergement',
            'pension alimentaire', 'contribution', 'autorité parentale'
        ]
    
    def process_document(self, text: str) -> Dict[str, Any]:
        """
        Traite un document juridique et extrait les informations structurées.
        
        Args:
            text (str): Texte du document juridique
            
        Returns:
            Dict[str, Any]: Informations extraites de manière structurée
        """
        if not text or not text.strip():
            return {
                'success': False,
                'error': 'Document vide',
                'extracted_data': {}
            }
        
        try:
            # Nettoyage du texte
            cleaned_text = self._clean_text(text)
            
            # Extraction des informations
            extracted_data = {
                'document_type': self._identify_document_type(cleaned_text),
                'parties': self._extract_parties(cleaned_text),
                'jours_garde': self._extract_garde_days(cleaned_text),
                'horaires': self._extract_horaires(cleaned_text),
                'lieux_remise': self._extract_lieux(cleaned_text),
                'interdits': self._extract_interdictions(cleaned_text),
                'obligations': self._extract_obligations(cleaned_text),
                'vacances_scolaires': self._extract_vacances(cleaned_text),
                'pension_alimentaire': self._extract_pension(cleaned_text),
                'dates_importantes': self._extract_dates(cleaned_text)
            }
            
            # Validation et nettoyage des données extraites
            extracted_data = self._validate_extracted_data(extracted_data)
            
            return {
                'success': True,
                'extracted_data': extracted_data,
                'processing_date': datetime.utcnow().isoformat(),
                'confidence_score': self._calculate_confidence(extracted_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors du traitement: {str(e)}',
                'extracted_data': {}
            }
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie le texte du document pour améliorer l'extraction.
        
        Args:
            text (str): Texte brut
            
        Returns:
            str: Texte nettoyé
        """
        # Suppression des caractères de contrôle et normalisation
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
        
        # Normalisation des espaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Suppression des en-têtes/pieds de page courants
        cleaned = re.sub(r'page\s+\d+\s+sur\s+\d+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'tribunal\s+de\s+grande\s+instance', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def _identify_document_type(self, text: str) -> str:
        """
        Identifie le type de document juridique.
        
        Args:
            text (str): Texte du document
            
        Returns:
            str: Type de document identifié
        """
        text_lower = text.lower()
        
        if 'ordonnance' in text_lower and 'référé' in text_lower:
            return 'ordonnance_refere'
        elif 'jugement' in text_lower:
            return 'jugement'
        elif 'ordonnance' in text_lower:
            return 'ordonnance'
        elif 'convention' in text_lower and 'homolog' in text_lower:
            return 'convention_homologuee'
        else:
            return 'document_juridique'
    
    def _extract_parties(self, text: str) -> Dict[str, str]:
        """
        Extrait les noms des parties (père, mère).
        
        Args:
            text (str): Texte du document
            
        Returns:
            Dict[str, str]: Noms des parties
        """
        parties = {'pere': '', 'mere': ''}
        
        # Patterns pour identifier les parties
        patterns = [
            r'M\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Mme\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Monsieur\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'Madame\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Logique simple: premier nom = père, deuxième = mère
                if not parties['pere'] and matches:
                    parties['pere'] = matches[0]
                elif not parties['mere'] and len(matches) > 1:
                    parties['mere'] = matches[1]
        
        return parties
    
    def _extract_garde_days(self, text: str) -> List[str]:
        """
        Extrait les jours de garde.
        
        Args:
            text (str): Texte du document
            
        Returns:
            List[str]: Liste des jours de garde
        """
        jours = []
        text_lower = text.lower()
        
        # Jours de la semaine
        jours_semaine = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        for jour in jours_semaine:
            if jour in text_lower:
                jours.append(jour)
        
        # Patterns spéciaux
        if 'week-end' in text_lower or 'weekend' in text_lower:
            jours.extend(['samedi', 'dimanche'])
        
        if 'une semaine sur deux' in text_lower or 'garde alternée' in text_lower:
            jours.append('garde_alternee')
        
        return list(set(jours))  # Suppression des doublons
    
    def _extract_horaires(self, text: str) -> List[str]:
        """
        Extrait les horaires mentionnés.
        
        Args:
            text (str): Texte du document
            
        Returns:
            List[str]: Liste des horaires
        """
        horaires = []
        
        # Pattern pour les heures (18h, 18h30, 18:30)
        pattern_heures = r'\b\d{1,2}(?:h\d{0,2}|:\d{2})\b'
        matches = re.findall(pattern_heures, text)
        horaires.extend(matches)
        
        # Pattern pour "à X heures"
        pattern_heures_text = r'à\s+(\d{1,2})\s*heures?'
        matches = re.findall(pattern_heures_text, text, re.IGNORECASE)
        horaires.extend([f"{h}h" for h in matches])
        
        return list(set(horaires))
    
    def _extract_lieux(self, text: str) -> List[str]:
        """
        Extrait les lieux de remise/récupération.
        
        Args:
            text (str): Texte du document
            
        Returns:
            List[str]: Liste des lieux
        """
        lieux = []
        text_lower = text.lower()
        
        lieux_patterns = [
            'domicile maternel',
            'domicile paternel',
            'école de l\'enfant',
            'lieu de résidence',
            'domicile de la mère',
            'domicile du père'
        ]
        
        for lieu in lieux_patterns:
            if lieu in text_lower:
                lieux.append(lieu)
        
        return lieux
    
    def _extract_interdictions(self, text: str) -> List[str]:
        """
        Extrait les interdictions mentionnées.
        
        Args:
            text (str): Texte du document
            
        Returns:
            List[str]: Liste des interdictions
        """
        interdictions = []
        
        # Recherche de phrases contenant des interdictions
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in ['interdit', 'défense', 'prohibition', 'ne peut pas']):
                interdictions.append(sentence.strip())
        
        return interdictions[:5]  # Limitation à 5 interdictions max
    
    def _extract_obligations(self, text: str) -> List[str]:
        """
        Extrait les obligations mentionnées.
        
        Args:
            text (str): Texte du document
            
        Returns:
            List[str]: Liste des obligations
        """
        obligations = []
        
        # Recherche de phrases contenant des obligations
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(phrase in sentence_lower for phrase in ['à charge pour', 'devra', 'est tenu de', 'obligation de']):
                obligations.append(sentence.strip())
        
        return obligations[:5]  # Limitation à 5 obligations max
    
    def _extract_vacances(self, text: str) -> Dict[str, Any]:
        """
        Extrait les informations sur les vacances scolaires.
        
        Args:
            text (str): Texte du document
            
        Returns:
            Dict[str, Any]: Informations sur les vacances
        """
        vacances = {
            'alternance': False,
            'details': []
        }
        
        text_lower = text.lower()
        
        if 'vacances scolaires' in text_lower:
            if 'alternance' in text_lower or 'une année sur deux' in text_lower:
                vacances['alternance'] = True
            
            # Extraction des détails sur les vacances
            sentences = re.split(r'[.!?]', text)
            for sentence in sentences:
                if 'vacances' in sentence.lower():
                    vacances['details'].append(sentence.strip())
        
        return vacances
    
    def _extract_pension(self, text: str) -> Dict[str, Any]:
        """
        Extrait les informations sur la pension alimentaire.
        
        Args:
            text (str): Texte du document
            
        Returns:
            Dict[str, Any]: Informations sur la pension
        """
        pension = {
            'montant': '',
            'periodicite': '',
            'details': []
        }
        
        # Pattern pour les montants (123€, 123 euros)
        montant_pattern = r'(\d+(?:,\d{2})?)\s*(?:€|euros?)'
        matches = re.findall(montant_pattern, text, re.IGNORECASE)
        if matches:
            pension['montant'] = matches[0] + '€'
        
        # Recherche de la périodicité
        text_lower = text.lower()
        if 'par mois' in text_lower or 'mensuel' in text_lower:
            pension['periodicite'] = 'mensuelle'
        elif 'par an' in text_lower or 'annuel' in text_lower:
            pension['periodicite'] = 'annuelle'
        
        return pension
    
    def _extract_dates(self, text: str) -> List[str]:
        """
        Extrait les dates importantes du document.
        
        Args:
            text (str): Texte du document
            
        Returns:
            List[str]: Liste des dates
        """
        dates = []
        
        # Pattern pour les dates (DD/MM/YYYY, DD-MM-YYYY)
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',
            r'\b\d{1,2}\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et nettoie les données extraites.
        
        Args:
            data (Dict[str, Any]): Données extraites
            
        Returns:
            Dict[str, Any]: Données validées
        """
        # Suppression des valeurs vides
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = [item for item in value if item and item.strip()]
            elif isinstance(value, str):
                data[key] = value.strip() if value else ''
        
        return data
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """
        Calcule un score de confiance basé sur la quantité d'informations extraites.
        
        Args:
            data (Dict[str, Any]): Données extraites
            
        Returns:
            float: Score de confiance entre 0 et 1
        """
        total_fields = len(data)
        filled_fields = 0
        
        for value in data.values():
            if isinstance(value, list) and value:
                filled_fields += 1
            elif isinstance(value, dict) and any(value.values()):
                filled_fields += 1
            elif isinstance(value, str) and value.strip():
                filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def simulate_ocr(self, file_path: str) -> str:
        """
        Simule un traitement OCR (pour les tests).
        Dans un environnement de production, ceci serait remplacé par AWS Textract ou Tesseract.
        
        Args:
            file_path (str): Chemin vers le fichier
            
        Returns:
            str: Texte extrait simulé
        """
        # Simulation d'un texte de jugement pour les tests
        return """
        TRIBUNAL DE GRANDE INSTANCE
        JUGEMENT
        
        Entre M. MARTIN Pierre et Mme DURAND Marie
        
        Il est ordonné que:
        - La garde de l'enfant sera exercée en résidence alternée
        - L'enfant sera remis tous les vendredis à 18h au domicile maternel
        - Les vacances scolaires seront partagées par alternance
        - Une pension alimentaire de 300€ par mois sera versée
        - Il est interdit de dénigrer l'autre parent devant l'enfant
        """

