"""
Enhanced Sentiment Analysis with Intent-Based Refinement
"""

import re
from typing import Dict, Optional, Tuple
from datetime import datetime
import pandas as pd

class SentimentAnalyzer:
    """Analyze sentiment with intent-aware adjustments"""
    
    def __init__(self):
        # Sentiment keywords
        self.positive_words = {
            'en': ['great', 'excellent', 'good', 'happy', 'love', 'wonderful', 'amazing', 
                   'helpful', 'thank', 'thanks', 'perfect', 'awesome', 'fantastic', 
                   'appreciate', 'satisfied', 'pleased', 'nice'],
            'de': ['großartig', 'ausgezeichnet', 'gut', 'glücklich', 'liebe', 'wunderbar',
                   'erstaunlich', 'hilfreich', 'danke', 'perfekt', 'fantastisch', 'zufrieden']
        }
        
        self.negative_words = {
            'en': ['bad', 'terrible', 'poor', 'hate', 'awful', 'horrible', 'worst',
                   'disappointed', 'frustrat', 'annoyed', 'angry', 'useless', 'slow',
                   'problem', 'issue', 'broken', 'error', 'fail', 'cannot', "can't",
                   'help', 'trouble', 'confused', 'difficult', 'struggling', "won't",
                   "isn't", "doesn't", 'not working', 'outage'],
            'de': ['schlecht', 'schrecklich', 'arm', 'hasse', 'furchtbar', 'grauenhaft',
                   'enttäuscht', 'frustriert', 'verärgert', 'wütend', 'nutzlos', 'langsam',
                   'problem', 'fehler']
        }
        
        # Problem indicators
        self.problem_patterns = [
            r'\bcan\'?t\b', r'\bcannot\b', r'\bwon\'?t\b', r'\bisn\'?t\b',
            r'\bdoesn\'?t\b', r'\bhelp\b', r'\bproblem\b', r'\bissue\b',
            r'\berror\b', r'\bbroken\b', r'\bslow\b', r'\boutage\b',
            r'\bnot working\b', r'\bfailing\b', r'\bwhy\b.*\bso slow\b'
        ]
        
        # Bias indicators
        self.bias_patterns = [
            r'\b(only|just|always|never|must|should)\b',
            r'\b(all|every|none)\b',
            r'\b(obviously|clearly|definitely)\b'
        ]
        
        # Intent keywords for lead scoring
        self.high_intent_keywords = {
            'en': ['enroll', 'apply', 'register', 'admission', 'fee', 'deadline', 
                   'requirement', 'eligibility', 'program', 'course', 'join'],
            'de': ['einschreiben', 'bewerben', 'anmelden', 'zulassung', 'gebühr', 
                   'frist', 'anforderung', 'programm', 'kurs', 'beitreten']
        }
        
        self.medium_intent_keywords = {
            'en': ['information', 'details', 'about', 'tell', 'explain', 'help', 
                   'know', 'understand', 'learn'],
            'de': ['information', 'details', 'über', 'erzählen', 'erklären', 
                   'hilfe', 'wissen', 'verstehen', 'lernen']
        }
    
    def detect_language(self, text: str) -> str:
        """Detect language from text"""
        text_lower = text.lower()
        
        german_words = ['ich', 'der', 'die', 'das', 'und', 'ist', 'ein', 'eine', 
                        'wie', 'was', 'wo', 'wann', 'können', 'möchte']
        english_words = ['the', 'is', 'and', 'or', 'what', 'how', 'when', 
                         'where', 'can', 'would', 'i', 'am']
        
        german_count = sum(1 for word in german_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        return 'de' if german_count > english_count else 'en'
    
    def _detect_problems(self, text: str) -> bool:
        """Detect if text contains problem/complaint indicators"""
        text_lower = text.lower()
        
        for pattern in self.problem_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def analyze_sentiment(self, text: str, language: str = 'en', 
                         intent_label: Optional[str] = None,
                         is_negative_intent: bool = False) -> Tuple[str, float]:
        """
        Analyze sentiment with intent-based refinement
        
        Args:
            text: Input text
            language: Language code
            intent_label: Classified intent (optional)
            is_negative_intent: Whether intent suggests negative sentiment
        
        Returns:
            (sentiment_label, confidence_score)
        """
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in self.positive_words[language] 
                            if word in text_lower)
        negative_count = sum(1 for word in self.negative_words[language] 
                            if word in text_lower)
        
        # Check for problem patterns
        has_problems = self._detect_problems(text)
        
        # Adjust negative count based on context
        if has_problems:
            negative_count += 2
        
        if is_negative_intent:
            negative_count += 1
        
        total = positive_count + negative_count
        
        if total == 0:
            # No sentiment words found
            if has_problems or is_negative_intent:
                return "negative", 0.6
            return "neutral", 0.5
        
        sentiment_score = (positive_count - negative_count) / max(total, 1)
        
        # Determine sentiment with intent consideration
        if sentiment_score > 0.2:
            label = "positive"
            confidence = min(0.5 + (sentiment_score * 0.5), 1.0)
        elif sentiment_score < -0.2 or has_problems or is_negative_intent:
            label = "negative"
            confidence = min(0.6 + (abs(sentiment_score) * 0.4), 1.0)
        else:
            label = "neutral"
            confidence = 0.5 + (abs(sentiment_score) * 0.3)
        
        return label, round(confidence, 2)
    
    def detect_bias(self, text: str) -> Dict[str, any]:
        """Detect potential bias in text"""
        text_lower = text.lower()
        detected_patterns = []
        
        for pattern in self.bias_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                detected_patterns.extend(matches)
        
        bias_score = min(len(detected_patterns) / 5.0, 1.0)
        
        if bias_score > 0.6:
            bias_level = "high"
            mitigation = "Consider rephrasing with more neutral language"
        elif bias_score > 0.3:
            bias_level = "medium"
            mitigation = "Some absolute terms detected; consider alternatives"
        else:
            bias_level = "low"
            mitigation = "Language appears balanced"
        
        return {
            'bias_level': bias_level,
            'bias_score': round(bias_score, 2),
            'detected_patterns': list(set(detected_patterns)),
            'mitigation_suggestion': mitigation
        }
    
    def calculate_lead_score(self, text: str, user_type: str, 
                            sentiment: str, language: str = 'en',
                            intent_category: Optional[str] = None) -> int:
        """
        Calculate lead score with intent consideration
        
        Args:
            text: Query text
            user_type: User type
            sentiment: Detected sentiment
            language: Language code
            intent_category: High-level intent category
        
        Returns:
            Lead score (0-100)
        """
        text_lower = text.lower()
        score = 50  # Base score
        
        # User type impact
        if user_type == 'student':
            score += 10
        elif user_type == 'employee':
            score += 5
        elif user_type == 'partner':
            score += 15
        
        # Sentiment impact
        if sentiment == 'positive':
            score += 15
        elif sentiment == 'negative':
            score -= 10
        
        # Intent category boost
        high_value_intents = ['enrollment', 'admission', 'partnership', 'collaboration']
        if intent_category:
            if any(hvi in intent_category for hvi in high_value_intents):
                score += 20
        
        # Intent keywords
        high_intent = sum(1 for word in self.high_intent_keywords[language] 
                         if word in text_lower)
        medium_intent = sum(1 for word in self.medium_intent_keywords[language] 
                           if word in text_lower)
        
        score += (high_intent * 10)
        score += (medium_intent * 5)
        
        # Question marks (engagement)
        question_count = text.count('?')
        score += min(question_count * 3, 10)
        
        # Length (detailed queries = higher intent)
        word_count = len(text.split())
        if word_count > 20:
            score += 10
        elif word_count > 10:
            score += 5
        
        # Normalize to 0-100
        return max(0, min(100, score))
    
    def full_analysis(self, text: str, user_type: str, 
                 language: Optional[str] = None,
                 intent_label: Optional[str] = None,
                 is_negative_intent: bool = False) -> Dict[str, any]:
        """
        Perform complete analysis on text with optional intent context
    
        Args:
            text: User query text
            user_type: employee, student, partner
            language: Language code (en/de) - auto-detected if None
            intent_label: Pre-classified intent label (optional)
            is_negative_intent: Whether intent suggests negative sentiment
        """
        if not language:
            language = self.detect_language(text)
    
        sentiment, sentiment_confidence = self.analyze_sentiment(text, language)
    
        # Adjust sentiment based on intent if provided
        if is_negative_intent and sentiment != 'negative':
            sentiment = 'negative'
            sentiment_confidence = max(0.7, sentiment_confidence)
    
        bias_info = self.detect_bias(text)
        lead_score = self.calculate_lead_score(text, user_type, sentiment, language)
    
        return {
            'query': text,
            'language': language,
            'sentiment': sentiment,
            'sentiment_confidence': sentiment_confidence,
            'bias_level': bias_info['bias_level'],
            'bias_score': bias_info['bias_score'],
            'bias_patterns': ', '.join(bias_info['detected_patterns']) if bias_info['detected_patterns'] else 'none',
            'bias_mitigation': bias_info['mitigation_suggestion'],
            'lead_score': lead_score,
            'intent': intent_label if intent_label else 'general_query',
            'timestamp': datetime.now()
        }