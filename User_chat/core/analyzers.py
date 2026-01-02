"""
Analyzers Module
Unified interface for Intent Classification, Sentiment Analysis, and FAISS retrieval
"""

import sys
import os
from typing import Dict, List, Any, Optional
import logging

# Configure logging for analyzers
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set to INFO level for our logs

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../models'))

try:
    from models.intent_classifier import IntentClassifier
    from models.sentiment_analyzer import SentimentAnalyzer
    from models.query_chromadb import query_kb  # Using ChromaDB now instead of FAISS
except ImportError:
    # Fallback for different path structures
    from intent_classifier import IntentClassifier
    from sentiment_analyzer import SentimentAnalyzer
    from query_chromadb import query_kb  # Using ChromaDB now instead of FAISS


class MessageAnalyzer:
    """
    Unified analyzer combining Intent, Sentiment, and FAISS
    Simple wrapper to make chatbot integration clean
    """

    def __init__(self):
        """Initialize all analyzers"""
        print("🔧 Initializing analyzers...")

        try:
            # Use absolute path for intent classifier
            base_dir = os.path.join(os.path.dirname(__file__), '../../data/bot_data/synthetic_data')
            base_dir = os.path.abspath(base_dir)
            print(f"📁 Intent Classifier path: {base_dir}")

            self.intent_classifier = IntentClassifier(base_path=base_dir)
            print("✅ Intent Classifier loaded")
        except Exception as e:
            print(f"⚠️ Intent Classifier failed: {e}")
            import traceback
            traceback.print_exc()
            self.intent_classifier = None

        try:
            self.sentiment_analyzer = SentimentAnalyzer()
            print("✅ Sentiment Analyzer loaded")
        except Exception as e:
            print(f"⚠️ Sentiment Analyzer failed: {e}")
            self.sentiment_analyzer = None

        # ChromaDB paths (replacing old FAISS)
        self.chromadb_dir = os.path.join(os.path.dirname(__file__), '../../data/chromadb')
        self.chromadb_dir = os.path.abspath(self.chromadb_dir)

        if os.path.exists(self.chromadb_dir):
            print(f"✅ ChromaDB found at {self.chromadb_dir}")
        else:
            print(f"⚠️ ChromaDB not found at {self.chromadb_dir}")

    def analyze_message(self, text: str, user_type: str, language: str = 'en',
                       user_stats: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Complete message analysis

        Args:
            text: User message
            user_type: student/employee/partner
            language: en or de
            user_stats: User history stats from database

        Returns:
            Complete analysis dict with intent, sentiment, FAISS results, patterns
        """
        logger.info(f"🔬 Analyzing: \"{text}\" | Type: {user_type} | Lang: {language}")

        result = {
            'text': text,
            'user_type': user_type,
            'language': language
        }

        # 1. Intent Classification
        if self.intent_classifier:
            try:
                intent, confidence = self.intent_classifier.predict_intent(
                    query=text,
                    user_type=user_type,
                    language=language
                )
                is_negative_intent = self.intent_classifier.is_negative_sentiment_intent(intent)
                intent_desc = self.intent_classifier.get_intent_description(intent)

                result['intent'] = intent
                result['intent_confidence'] = confidence
                result['is_negative_intent'] = is_negative_intent
                result['intent_description'] = intent_desc

                logger.info(f"   ✅ Intent: {intent} ({confidence:.2f})")
            except Exception as e:
                logger.error(f"   ❌ Intent error: {e}")
                result['intent'] = 'general_query'
                result['intent_confidence'] = 0.5
                result['is_negative_intent'] = False
                result['intent_description'] = 'General Query'
        else:
            result['intent'] = 'general_query'
            result['intent_confidence'] = 0.5
            result['is_negative_intent'] = False
            result['intent_description'] = 'General Query'

        # 2. Sentiment Analysis
        if self.sentiment_analyzer:
            try:
                sentiment_result = self.sentiment_analyzer.full_analysis(
                    text=text,
                    user_type=user_type,
                    language=language,
                    intent_label=result['intent'],
                    is_negative_intent=result['is_negative_intent']
                )

                result['sentiment'] = sentiment_result['sentiment']
                result['sentiment_confidence'] = sentiment_result['sentiment_confidence']
                result['lead_score'] = sentiment_result['lead_score']
                result['bias_level'] = sentiment_result['bias_level']
                result['bias_score'] = sentiment_result['bias_score']

                logger.info(f"   ✅ Sentiment: {sentiment_result['sentiment']} | Lead: {sentiment_result['lead_score']}")
            except Exception as e:
                logger.error(f"   ❌ Sentiment error: {e}")
                result['sentiment'] = 'neutral'
                result['sentiment_confidence'] = 0.5
                result['lead_score'] = 50
                result['bias_level'] = 'low'
                result['bias_score'] = 0.0
        else:
            result['sentiment'] = 'neutral'
            result['sentiment_confidence'] = 0.5
            result['lead_score'] = 50
            result['bias_level'] = 'low'
            result['bias_score'] = 0.0

        # 3. ChromaDB Semantic Search
        result['faiss_results'] = []
        if os.path.exists(self.chromadb_dir):
            try:
                chromadb_results = query_kb(
                    query=text,
                    chromadb_dir=self.chromadb_dir,
                    top_k=3,
                    filter_language=language,
                    filter_user_type=user_type
                )
                result['faiss_results'] = chromadb_results
                logger.info(f"   ✅ ChromaDB: {len(chromadb_results)} docs found")
            except Exception as e:
                logger.error(f"   ❌ ChromaDB error: {e}")

        # 4. User Pattern Analysis
        if user_stats:
            result['user_patterns'] = self._analyze_patterns(user_stats)
        else:
            result['user_patterns'] = {}

        return result

    def _analyze_patterns(self, user_stats: Dict) -> Dict[str, Any]:
        """Analyze user patterns from history"""
        patterns = {
            'is_returning_user': user_stats.get('total_chats', 0) > 0,
            'interaction_count': user_stats.get('total_chats', 0),
            'has_history': len(user_stats.get('recent_intents', [])) > 0
        }

        # Check for repeated topics
        recent_intents = user_stats.get('recent_intents', [])
        if recent_intents:
            intent_counts = {}
            for intent in recent_intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1

            # Most common intent
            if intent_counts:
                most_common = max(intent_counts.items(), key=lambda x: x[1])
                patterns['most_common_intent'] = most_common[0]
                patterns['repeated_topic'] = most_common[1] >= 3

        # Check sentiment trend
        recent_sentiments = user_stats.get('recent_sentiments', [])
        if len(recent_sentiments) >= 3:
            last_3 = recent_sentiments[-3:]
            negative_count = last_3.count('negative')
            positive_count = last_3.count('positive')

            if negative_count >= 2:
                patterns['sentiment_trend'] = 'declining'
            elif positive_count >= 2:
                patterns['sentiment_trend'] = 'improving'
            else:
                patterns['sentiment_trend'] = 'stable'
        else:
            patterns['sentiment_trend'] = 'stable'

        # Check average lead score
        recent_scores = user_stats.get('recent_scores', [])
        if recent_scores:
            patterns['avg_lead_score'] = sum(recent_scores) / len(recent_scores)
        else:
            patterns['avg_lead_score'] = 50

        return patterns

    def find_similar_previous_chat(self, current_message: str, user_id: str,
                                   current_session_id: str = None,
                                   similarity_threshold: float = 0.6) -> Optional[Dict[str, Any]]:
        """
        Find similar previous chat from OLD sessions using simple string matching

        Args:
            current_message: Current user message
            user_id: User ID to search history
            current_session_id: Current session ID to exclude
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            Dict with similar chat info or None
        """
        try:
            from difflib import SequenceMatcher
            from ..database.chat import ChatDatabase

            chat_db = ChatDatabase()
            # Pass current_session_id to exclude it
            previous_chats = chat_db.get_user_previous_chats(user_id, current_session_id, limit=20)

            if not previous_chats:
                print(f"📝 No previous sessions found for user {user_id}")
                return None

            print(f"📝 Searching through {len(previous_chats)} previous conversations...")
            best_match = None
            best_score = 0.0

            current_lower = current_message.lower().strip()

            for chat in previous_chats:
                prev_message = chat['user_message'].lower().strip()

                # Calculate similarity
                similarity = SequenceMatcher(None, current_lower, prev_message).ratio()

                if similarity > best_score and similarity >= similarity_threshold:
                    best_score = similarity
                    best_match = {
                        'previous_question': chat['user_message'],
                        'previous_answer': chat['bot_response'],
                        'similarity_score': similarity,
                        'timestamp': chat['timestamp']
                    }

            if best_match:
                print(f"📝 SIMILAR CHAT FOUND: {best_score:.2f} similarity")
                return best_match
            else:
                print(f"📝 No similar previous chat found (threshold: {similarity_threshold})")
                return None

        except Exception as e:
            print(f"❌ Error finding similar chat: {e}")
            return None
