"""
Intent Classification Module
Loads TSV files and classifies user queries by intent
"""

import pandas as pd
import os
from typing import Dict, Tuple, Optional
import re
from difflib import SequenceMatcher

class IntentClassifier:
    """
    Intent classifier that loads training data from TSV files
    and matches user queries to predefined intents
    """
    
    def __init__(self, base_path: str = 'bot_data/synthetic'):
        """
        Initialize intent classifier
        
        Args:
            base_path: Base path to synthetic_data folder
        """
        self.base_path = base_path
        self.training_data = {
            'en': {'employee': [], 'student': [], 'partner': []},
            'de': {'employee': [], 'student': [], 'partner': []}
        }
        self.intent_keywords = {}
        self.loaded = False  # ADD THIS LINE
        self._load_training_data()
    
    def _load_training_data(self):
        """Load all TSV files from en and de folders"""
        languages = ['en', 'de']
        user_types = ['employee', 'student', 'partner']
        
        total_loaded = 0
        
        for lang in languages:
            for user_type in user_types:
                # Try multiple possible paths
                possible_paths = [
                    os.path.join(self.base_path, lang, f"{user_type}_data.tsv"),
                    os.path.join(self.base_path, 'synthetic_data', lang, f"{user_type}_data.tsv"),
                    os.path.join('bot_data', 'synthetic_data', lang, f"{user_type}_data.tsv"),
                    os.path.join('bot_data', 'synthetic', lang, f"{user_type}_data.tsv")
                ]
                
                file_loaded = False
                
                for file_path in possible_paths:
                    try:
                        if os.path.exists(file_path):
                            df = pd.read_csv(file_path, sep='\t')
                            
                            # Ensure correct column names
                            if 'text' in df.columns and 'label' in df.columns:
                                self.training_data[lang][user_type] = df[['text', 'label']].values.tolist()
                                
                                # Extract keywords from intents
                                for _, label in df[['text', 'label']].values:
                                    if label not in self.intent_keywords:
                                        self.intent_keywords[label] = set()
                                    
                                    # Extract meaningful words from label
                                    words = re.findall(r'\w+', label.lower())
                                    self.intent_keywords[label].update(words)
                                
                                print(f"✅ Loaded {len(df)} samples from {file_path}")
                                total_loaded += len(df)
                                file_loaded = True
                                break  # Stop trying other paths
                            else:
                                print(f"⚠️ Invalid columns in {file_path}")
                                
                    except Exception as e:
                        continue  # Try next path
                
                if not file_loaded:
                    print(f"⚠️ Could not load {user_type}_data.tsv for {lang}")
        
        # Set loaded flag
        self.loaded = total_loaded > 0
        
        if self.loaded:
            print(f"✅ Intent Classifier loaded with {total_loaded} total samples")
        else:
            print("⚠️ No training data loaded - using fallback intent detection")
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def _keyword_match_score(self, query: str, intent: str) -> float:
        """Calculate keyword match score"""
        query_lower = query.lower()
        
        if intent not in self.intent_keywords:
            return 0.0
        
        keywords = self.intent_keywords[intent]
        matches = sum(1 for keyword in keywords if keyword in query_lower)
        
        return matches / len(keywords) if keywords else 0.0
    
    def predict_intent(self, query: str, user_type: str, language: str = 'en') -> Tuple[str, float]:
        """
        Classify user query intent
        
        Args:
            query: User query text
            user_type: employee, student, or partner
            language: en or de
        
        Returns:
            Tuple of (intent_label, confidence_score)
        """
        # Normalize inputs
        language = language.lower() if language else 'en'
        user_type = user_type.lower() if user_type else 'employee'
        
        # Handle admin as employee
        if user_type == 'admin':
            user_type = 'employee'
        
        # Validate language and user_type
        if language not in self.training_data:
            language = 'en'
        
        if user_type not in self.training_data[language]:
            user_type = 'employee'
        
        training_samples = self.training_data[language][user_type]
        
        if not training_samples:
            return self._fallback_intent_detection(query, user_type), 0.5
        
        best_match = None
        best_score = 0.0
        
        # Calculate similarity with all training samples
        for text, label in training_samples:
            # Text similarity
            text_similarity = self._calculate_similarity(query, text)
            
            # Keyword matching
            keyword_score = self._keyword_match_score(query, label)
            
            # Combined score (weighted)
            combined_score = (text_similarity * 0.7) + (keyword_score * 0.3)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match = label
        
        # Set minimum confidence threshold
        if best_score < 0.3:
            return self._fallback_intent_detection(query, user_type), best_score
        
        return best_match if best_match else "general_query", round(best_score, 2)
    
    def _fallback_intent_detection(self, text: str, user_type: str) -> str:
        """
        Simple keyword-based fallback intent detection
        """
        text_lower = text.lower()
        
        # Common intent patterns
        if user_type == "employee":
            if any(word in text_lower for word in ['password', 'login', 'access', 'email', 'wifi', 'network', 'vpn', 'slow', 'not working']):
                return "it_support_employee"
            elif any(word in text_lower for word in ['room', 'book', 'reserve', 'meeting']):
                return "room_booking_employee"
            elif any(word in text_lower for word in ['hr', 'leave', 'payroll', 'benefits', 'vacation']):
                return "hr_query_employee"
        
        elif user_type == "student":
            if any(word in text_lower for word in ['enroll', 'register', 'admission', 'apply']):
                return "enrollment_student"
            elif any(word in text_lower for word in ['course', 'class', 'schedule', 'timetable', 'program']):
                return "course_info_student"
            elif any(word in text_lower for word in ['library', 'book', 'research']):
                return "library_student"
            elif any(word in text_lower for word in ['exam', 'grade', 'result', 'test']):
                return "exam_info_student"
        
        elif user_type == "partner":
            if any(word in text_lower for word in ['partnership', 'collaborate', 'cooperation']):
                return "partnership_inquiry"
            elif any(word in text_lower for word in ['facility', 'rent', 'venue', 'space']):
                return "facility_rental_partner"
            elif any(word in text_lower for word in ['research', 'project', 'funding']):
                return "research_collaboration_partner"
        
        return "general_query"
    
    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            # Employee intents
            'it_support_employee': 'IT Support Request',
            'room_booking_employee': 'Room Booking',
            'hr_query_employee': 'HR Query',
            'network_issue_employee': 'Network Issue',
            'email_support_employee': 'Email Support',
            
            # Student intents
            'enrollment_student': 'Enrollment/Registration',
            'course_info_student': 'Course Information',
            'library_student': 'Library Services',
            'exam_info_student': 'Exam/Grade Information',
            'admission_student': 'Admission Inquiry',
            'scholarship_student': 'Scholarship Information',
            
            # Partner intents
            'partnership_inquiry': 'Partnership Inquiry',
            'facility_rental_partner': 'Facility Rental',
            'research_collaboration_partner': 'Research Collaboration',
            'sponsorship_partner': 'Sponsorship Inquiry',
            
            # General
            'general_query': 'General Query',
            'greeting': 'Greeting',
            'complaint': 'Complaint',
            'feedback': 'Feedback'
        }
        
        return descriptions.get(intent, intent.replace('_', ' ').title())
    
    def get_intent_category(self, intent_label: str) -> str:
        """
        Extract high-level category from intent label
        
        Examples:
            it_support_employee -> it_support
            enrollment_student -> enrollment
        """
        # Remove user type suffix
        for suffix in ['_employee', '_student', '_partner']:
            if intent_label.endswith(suffix):
                return intent_label.replace(suffix, '')
        
        return intent_label
    
    def is_negative_sentiment_intent(self, intent_label: str) -> bool:
        """
        Determine if an intent typically indicates negative sentiment
        
        Args:
            intent_label: The classified intent
        
        Returns:
            True if intent suggests problems/complaints
        """
        negative_keywords = [
            'problem', 'issue', 'complaint', 'error', 'support',
            'help', 'trouble', 'cant', 'cannot', 'not_working',
            'slow', 'down', 'outage', 'broken', 'confused',
            'difficult', 'struggling', 'emergency', 'urgent',
            'it_support', 'network_issue', 'email_support'
        ]
        
        intent_lower = intent_label.lower()
        
        # Check if any negative keyword is in the intent
        return any(keyword in intent_lower for keyword in negative_keywords)
    
    def get_statistics(self) -> Dict:
        """Get statistics about loaded training data"""
        stats = {
            'total_samples': 0,
            'by_language': {},
            'by_user_type': {},
            'unique_intents': len(self.intent_keywords),
            'loaded': self.loaded
        }
        
        for lang in self.training_data:
            lang_total = 0
            for user_type in self.training_data[lang]:
                count = len(self.training_data[lang][user_type])
                lang_total += count
                
                if user_type not in stats['by_user_type']:
                    stats['by_user_type'][user_type] = 0
                stats['by_user_type'][user_type] += count
            
            stats['by_language'][lang] = lang_total
            stats['total_samples'] += lang_total
        
        return stats