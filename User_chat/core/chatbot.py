"""
Enhanced HNU Chatbot with LangGraph
Complete implementation with interactive features and multi-turn conversations
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, TypedDict, Any
from dataclasses import dataclass
import asyncio
import logging

# Configure comprehensive logging
# Only log chatbot-related modules, not third-party libraries
logging.basicConfig(
    level=logging.WARNING,  # Set root logger to WARNING to suppress third-party logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('openai_data_flow.log'),
        logging.StreamHandler()
    ]
)

# Create our logger and set it to INFO level
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Our logs will show at INFO level

# Silence noisy third-party loggers
logging.getLogger('fsevents').setLevel(logging.ERROR)
logging.getLogger('watchdog').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)

# LangGraph imports
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    from typing_extensions import Annotated
    LANGGRAPH_AVAILABLE = True
except ImportError:
    print("Installing LangGraph...")
    import subprocess
    subprocess.run(["pip", "install", "langgraph", "langchain", "typing-extensions"], check=True)
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    from typing_extensions import Annotated
    LANGGRAPH_AVAILABLE = True

# Optional dependencies
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

# Enhanced State Definition
class ConversationState(TypedDict):
    messages: List[Dict[str, Any]]
    user_type: str
    user_id: str
    current_intent: str
    confidence: float
    language: str
    context: Dict[str, Any]
    workflow_step: str
    requires_followup: bool
    extracted_info: Dict[str, Any]
    conversation_topic: str
    topic_depth: int
    suggested_queries: List[str]
    interactive_options: Dict[str, Any]
    awaiting_response: bool
    topic_data: Dict[str, Any]
    session_id: str
    # New fields for intelligence
    sentiment: str
    lead_score: int
    analysis_result: Dict[str, Any]
    user_stats: Dict[str, Any]
    faiss_context: List[Dict[str, Any]]

class HNUKnowledgeBase:
    """Knowledge base for HNU information"""
    
    @staticmethod
    def get_bachelor_programs():
        return {
            "total": 15,
            "programs": [
                {"name": "Business Administration", "code": "BWL", "duration": "7 semesters", "language": "German/English", "faculty": "Business"},
                {"name": "International Management", "code": "IM", "duration": "7 semesters", "language": "English", "faculty": "Business"},
                {"name": "Digital Business Management", "code": "DBM", "duration": "7 semesters", "language": "German", "faculty": "Business"},
                {"name": "Marketing Management", "code": "MM", "duration": "7 semesters", "language": "German", "faculty": "Business"},
                {"name": "Logistics Management", "code": "LM", "duration": "7 semesters", "language": "German", "faculty": "Business"},
                {"name": "Information Management", "code": "INM", "duration": "7 semesters", "language": "German", "faculty": "Information"},
                {"name": "Industrial Engineering", "code": "WI", "duration": "7 semesters", "language": "German", "faculty": "Engineering"},
                {"name": "Mechanical Engineering", "code": "MB", "duration": "7 semesters", "language": "German", "faculty": "Engineering"},
                {"name": "Medical Engineering", "code": "MT", "duration": "7 semesters", "language": "German", "faculty": "Engineering"},
                {"name": "Healthcare Management", "code": "GM", "duration": "7 semesters", "language": "German", "faculty": "Health"},
                {"name": "Social Work", "code": "SA", "duration": "7 semesters", "language": "German", "faculty": "Social"},
                {"name": "Digital Health Management", "code": "DHM", "duration": "7 semesters", "language": "German", "faculty": "Health"},
                {"name": "Public Management", "code": "PM", "duration": "6 semesters", "language": "German", "faculty": "Public"},
                {"name": "Tax and Audit", "code": "STP", "duration": "6 semesters", "language": "German", "faculty": "Business"},
                {"name": "Applied Computer Science", "code": "AI", "duration": "7 semesters", "language": "German", "faculty": "Information"}
            ],
            "links": {
                "main_page": "https://www.hnu.de/studium/bachelor",
                "application": "https://www.hnu.de/bewerbung",
                "requirements": "https://www.hnu.de/zulassungsvoraussetzungen"
            }
        }
    
    @staticmethod
    def get_master_programs():
        return {
            "total": 8,
            "programs": [
                {"name": "Business Administration", "code": "MBA", "duration": "3 semesters", "language": "German/English", "faculty": "Business"},
                {"name": "International Management", "code": "MIM", "duration": "3 semesters", "language": "English", "faculty": "Business"},
                {"name": "Digital Enterprise Management", "code": "DEM", "duration": "3 semesters", "language": "German", "faculty": "Business"},
                {"name": "Information Management", "code": "MIM", "duration": "3 semesters", "language": "German", "faculty": "Information"},
                {"name": "Systems Engineering", "code": "MSE", "duration": "3 semesters", "language": "German", "faculty": "Engineering"},
                {"name": "Medical Engineering", "code": "MMT", "duration": "3 semesters", "language": "German", "faculty": "Engineering"},
                {"name": "Healthcare Management", "code": "MHM", "duration": "3 semesters", "language": "German", "faculty": "Health"},
                {"name": "Public Administration", "code": "MPA", "duration": "4 semesters", "language": "German", "faculty": "Public"}
            ],
            "links": {
                "main_page": "https://www.hnu.de/studium/master",
                "application": "https://www.hnu.de/master-bewerbung"
            }
        }
    
    @staticmethod
    def get_employee_services():
        return {
            "it_support": {
                "description": "IT support for employees",
                "contact": "it@hnu.de",
                "phone": "+49 731 9762-1234",
                "services": ["Hardware issues", "Software installation", "Network problems", "Email configuration"]
            },
            "hr_services": {
                "description": "Human Resources support",
                "contact": "hr@hnu.de", 
                "phone": "+49 731 9762-2000",
                "services": ["Payroll", "Benefits", "Leave management", "Training"]
            },
            "facilities": {
                "description": "Room booking and facilities",
                "contact": "facilities@hnu.de",
                "phone": "+49 731 9762-3000",
                "services": ["Room booking", "Equipment requests", "Maintenance", "Event planning"]
            }
        }
    
    @staticmethod
    def get_student_services():
        return {
            "academic_office": {
                "description": "Academic affairs and enrollment",
                "contact": "student@hnu.de",
                "phone": "+49 731 9762-1500",
                "services": ["Course enrollment", "Transcripts", "Certificates", "Academic records"]
            },
            "student_support": {
                "description": "Student counseling and support",
                "contact": "counseling@hnu.de",
                "phone": "+49 731 9762-1600",
                "services": ["Academic counseling", "Career guidance", "Personal support", "Study planning"]
            },
            "library": {
                "description": "Library services",
                "contact": "library@hnu.de",
                "phone": "+49 731 9762-1700",
                "services": ["Book loans", "Research support", "Study spaces", "Digital resources"]
            }
        }
    
    @staticmethod
    def get_suggested_queries(topic: str, depth: int, user_type: str) -> List[str]:
        """Get context-aware suggested queries"""
        suggestions = {
            "bachelor_programs": {
                0: [
                    "Show me all bachelor program names",
                    "What are the admission requirements?", 
                    "Which programs are taught in English?",
                    "How long do bachelor programs take?"
                ],
                1: [
                    "Tell me more about Business Administration",
                    "What are the career prospects?",
                    "How do I apply for these programs?",
                    "What are the semester fees?"
                ]
            },
            "master_programs": {
                0: [
                    "Show me all master program names",
                    "What are the prerequisites for master programs?",
                    "Which master programs are available in English?",
                    "How do master programs differ from bachelor?"
                ]
            },
            "employee_services": {
                0: [
                    "I need IT support",
                    "How do I book a meeting room?",
                    "HR contact information",
                    "Password reset help"
                ]
            },
            "student_services": {
                0: [
                    "How do I enroll in courses?",
                    "I need my transcript",
                    "Library opening hours",
                    "Academic counseling"
                ]
            }
        }
        
        # Get user-type specific suggestions if available
        user_suggestions = {
            "employee": ["IT support contact", "Room booking", "HR services", "VPN setup"],
            "student": ["Course enrollment", "Transcript request", "Library services", "Academic support"],
            "partner": ["Partnership opportunities", "Event planning", "Facility rental", "Collaboration options"]
        }
        
        base_suggestions = suggestions.get(topic, {}).get(depth, suggestions.get(topic, {}).get(0, []))
        user_specific = user_suggestions.get(user_type, [])
        
        return base_suggestions + user_specific[:2]  # Combine base + 2 user-specific

class EnhancedHNUChatbot:
    """Enhanced HNU Chatbot with LangGraph workflow"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.use_openai = openai_api_key is not None and OPENAI_AVAILABLE

        if self.use_openai:
            openai.api_key = openai_api_key

        self.kb = HNUKnowledgeBase()
        self.memory = MemorySaver()

        # Initialize analyzers (can fail independently)
        try:
            from .analyzers import MessageAnalyzer
            self.analyzer = MessageAnalyzer()
            print("✅ Analyzer initialized")
        except Exception as e:
            print(f"⚠️ Analyzer initialization failed: {e}")
            self.analyzer = None

        # Initialize database (separate from analyzer)
        try:
            # Try relative import first, fallback to direct import
            try:
                from ..database.chat import ChatDatabase
            except ImportError:
                from database.chat import ChatDatabase

            self.chat_db = ChatDatabase()
            print("✅ Database initialized")
        except Exception as e:
            print(f"⚠️ Database initialization failed: {e}")
            import traceback
            traceback.print_exc()
            self.chat_db = None

        self.workflow = self._create_workflow()

        print("✅ Enhanced HNU Chatbot initialized successfully!")
    
    def _create_workflow(self) -> StateGraph:
        """Create the enhanced LangGraph workflow"""
        
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("analyze_input", self._analyze_input)
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("detect_topic", self._detect_topic)
        workflow.add_node("gather_context", self._gather_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("add_interactive_elements", self._add_interactive_elements)
        workflow.add_node("finalize_response", self._finalize_response)
        
        # Add edges
        workflow.add_edge(START, "analyze_input")
        workflow.add_edge("analyze_input", "classify_intent")
        workflow.add_edge("classify_intent", "detect_topic")
        workflow.add_edge("detect_topic", "gather_context")
        workflow.add_edge("gather_context", "generate_response")
        workflow.add_edge("generate_response", "add_interactive_elements")
        workflow.add_edge("add_interactive_elements", "finalize_response")
        workflow.add_edge("finalize_response", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    def _detect_language(self, text: str) -> str:
        """Detect language of input text"""
        if not LANGDETECT_AVAILABLE:
            # Simple fallback detection
            german_words = ['der', 'die', 'das', 'ich', 'und', 'mit', 'für', 'haben', 'sein']
            english_words = ['the', 'and', 'or', 'but', 'with', 'for', 'have', 'be', 'do']
            
            text_lower = text.lower()
            german_count = sum(1 for word in german_words if word in text_lower)
            english_count = sum(1 for word in english_words if word in text_lower)
            
            return "de" if german_count > english_count else "en"
        
        try:
            return detect(text)
        except:
            return "en"
    
    def _analyze_input(self, state: ConversationState) -> ConversationState:
        """Analyze user input"""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]["content"]
        
        # Detect language
        state["language"] = self._detect_language(last_message)
        
        # Check if it's a button response
        is_button_response = last_message.startswith("BTN:")
        state["context"]["is_button_response"] = is_button_response
        
        # Extract button action if applicable
        if is_button_response:
            state["context"]["button_action"] = last_message.replace("BTN:", "").strip()
        
        state["workflow_step"] = "input_analyzed"
        return state
    
    # ================================
    # LONG-TERM MEMORY EXTRACTION
    # ================================
    def _extract_historical_topics(self, state):
        """
        Extract topics from:
        - current session chat history
        - similar messages (vector similarity)
        - long-term DB conversation history
        """

        topics = []

        # 1) TOPICS FROM CURRENT SESSION
        for m in state["messages"]:
            txt = m["content"].lower()

            if "bachelor" in txt:
                topics.append("bachelor_programs")
            if "master" in txt:
                topics.append("master_programs")
            if "library" in txt:
                topics.append("library_services")
            if "it" in txt and "support" in txt:
                topics.append("it_support")
            if "admission" in txt or "apply" in txt:
                topics.append("admissions")

        # 2) TOPICS FROM SIMILARITY SEARCH
        sim_msgs = state.get("analysis_result", {}).get("similar_messages", [])
        for sm in sim_msgs:
            t = sm.get("topic", None)
            if t:
                topics.append(t)

        # 3) TOPICS FROM LONG-TERM MEMORY / DB
        if self.chat_db:
            try:
                past_msgs = self.chat_db.get_recent_messages(
                    user_id=state["user_id"],
                    limit=50
                )
                for pm in past_msgs:
                    text = pm.get("content", "").lower()
                    if "bachelor" in text:
                        topics.append("bachelor_programs")
                    if "master" in text:
                        topics.append("master_programs")
                    if "library" in text:
                        topics.append("library_services")
                    if "it" in text and "support" in text:
                        topics.append("it_support")
                    if "admission" in text or "apply" in text:
                        topics.append("admissions")
            except:
                pass

        # Deduplicate
        topics = list(dict.fromkeys(topics))

        return topics[-5:]  # return last 5 topics max
    
    # ================================
    # PREFERRED LANGUAGE DETECTOR
    # ================================
    def _get_user_preferred_language(self, state):
        """
        Detect user's preferred language from long-term history.
        """

        if self.chat_db:
            try:
                past = self.chat_db.get_recent_messages(user_id=state["user_id"], limit=50)
                german = sum(1 for m in past if any(w in m["content"].lower() for w in ["der", "die", "und", "ich", "sein"]))
                english = sum(1 for m in past if any(w in m["content"].lower() for w in ["the", "and", "you", "have", "hello"]))

                if german > english:
                    return "de"
                if english > german:
                    return "en"
            except:
                pass

        return state.get("language", "en")
    
    # ==========================================
    # DETECT FREQUENT TOPICS & USER EMOTIONAL HISTORY
    # ==========================================
    def _get_user_long_term_profile(self, state):
        """
        Analyze user's emotional + topic patterns from last 100 messages.
        """

        profile = {
            "frequent_topics": [],
            "avg_sentiment": "neutral",
            "question_ratio": 0,
        }

        if not self.chat_db:
            return profile

        try:
            msgs = self.chat_db.get_recent_messages(user_id=state["user_id"], limit=100)
            topic_counts = {"bachelor": 0, "master": 0, "it": 0, "library": 0, "admissions": 0}
            sentiment_sum = 0
            question_count = 0

            for m in msgs:
                txt = m.get("content", "").lower()

                if "bachelor" in txt: topic_counts["bachelor"] += 1
                if "master" in txt: topic_counts["master"] += 1
                if "it" in txt: topic_counts["it"] += 1
                if "library" in txt: topic_counts["library"] += 1
                if "admission" in txt: topic_counts["admissions"] += 1
                if "?" in txt: question_count += 1

            # Frequent topics
            profile["frequent_topics"] = sorted(
                [k for k, v in topic_counts.items() if v > 0],
                key=lambda k: topic_counts[k],
                reverse=True
            )[:3]

            # Ratio of messages that are questions
            profile["question_ratio"] = question_count / max(len(msgs), 1)

            return profile

        except:
            return profile

    def _build_smart_greeting(self, state: ConversationState) -> str:
        """
        Smart greeting system using:
        - long-term memory
        - historical topics
        - similarity-based recall
        - preferred language
        - sentiment tone
        - frequent topics
        """

        # Latest user message
        msg = state["messages"][-1]["content"]
        msg_lower = msg.lower()

        # Memory-based info
        preferred_lang = self._get_user_preferred_language(state)
        historical_topics = self._extract_historical_topics(state)
        long_term_profile = self._get_user_long_term_profile(state)
        similar = state.get("analysis_result", {}).get("similar_messages", [])
        sentiment = state.get("sentiment", "neutral")

        # Tone detection
        is_formal = any(w in msg_lower for w in ["dear", "sehr geehrte", "regards"])
        is_casual = any(w in msg_lower for w in ["hi", "hey", "hallo"])

        # Map readable names
        names = {
            "bachelor_programs": "Bachelor programs",
            "master_programs": "Master programs",
            "library_services": "library services",
            "it_support": "IT support",
            "admissions": "admissions",
        }

        hist_readable = [names.get(t, t) for t in historical_topics]
        frequent_readable = [t.replace("_", " ") for t in long_term_profile["frequent_topics"]]

        # ================================
        # GERMAN GREETING
        # ================================
        if preferred_lang == "de":
            greeting = ""

            if similar:
                greeting = "Ich erinnere mich — Sie haben schon einmal etwas Ähnliches gefragt. "
            else:
                greeting = "Hallo! Ich sehe, dass Sie eine neue Frage haben. "

            # Historical
            if historical_topics:
                greeting += f"Früher sprachen Sie über {', '.join(hist_readable)}. "

            # Frequent topics
            if frequent_readable:
                greeting += f"Sie interessieren sich häufig für {', '.join(frequent_readable)}. "

            # Sentiment
            if sentiment == "negative":
                greeting += "Ich verstehe, dass dies frustrierend sein kann — ich unterstütze Sie gern. "
            elif sentiment == "positive":
                greeting += "Schön, wieder von Ihnen zu hören! "

            return greeting + "\n\n"

        # ================================
        # ENGLISH GREETING
        # ================================
        else:
            greeting = ""

            if similar:
                greeting = "I remember — you asked something similar before. "
            else:
                greeting = "Hi! I see you have a new question. "

            # Historical
            if historical_topics:
                greeting += f"Previously, you talked about {', '.join(hist_readable)}. "

            # Frequent topics
            if frequent_readable:
                greeting += f"You often ask about {', '.join(frequent_readable)}. "

            # Sentiment
            if sentiment == "negative":
                greeting += "I understand this might be frustrating — I’m here to help. "
            elif sentiment == "positive":
                greeting += "Great to hear from you again! "

            return greeting + "\n\n"



    def _classify_intent(self, state: ConversationState) -> ConversationState:
        """Classify user intent using analyzer"""
        if not state["messages"]:
            return state

        last_message = state["messages"][-1]["content"]

        # Load user stats for pattern analysis (session-level)
        user_stats = None
        session_stats = None

        user_id = state.get("user_id", "guest")
        print(f"🔍 DEBUG: user_id = {user_id}, chat_db = {self.chat_db is not None}")

        if self.chat_db and user_id and user_id != "guest":
            # Get session-level aggregated stats with per-session intent/sentiment
            try:
                print(f"🔍 Loading aggregated session stats for user: {user_id}")
                session_stats = self.chat_db.get_aggregated_session_stats(user_id, limit_sessions=10)
                print(f"🔍 Loaded session stats: {session_stats.get('total_sessions', 0)} sessions found")
            except Exception as e:
                print(f"⚠️ Error loading session stats: {e}")
                import traceback
                traceback.print_exc()
                session_stats = {}

            user_stats = self.chat_db.get_user_stats(user_id)  # For backward compatibility
            state["user_stats"] = user_stats or {}
            state["session_stats"] = session_stats
        else:
            print(f"⚠️ Skipping session stats load - chat_db: {self.chat_db is not None}, user_id: {user_id}")
            state["user_stats"] = {}
            state["session_stats"] = {}

        # Use analyzer for complete analysis
        if self.analyzer:
            try:
                analysis = self.analyzer.analyze_message(
                    text=last_message,
                    user_type=state["user_type"],
                    language=state["language"],
                    user_stats=user_stats
                )

                # Update state with analysis results
                state["current_intent"] = analysis["intent"]
                state["confidence"] = analysis["intent_confidence"]
                state["sentiment"] = analysis["sentiment"]
                state["lead_score"] = analysis["lead_score"]
                state["analysis_result"] = analysis
                state["faiss_context"] = analysis.get("faiss_results", [])

            except Exception as e:
                print(f"Analysis error: {e}")
                state["current_intent"] = "general_inquiry"
                state["confidence"] = 0.5
                state["sentiment"] = "neutral"
                state["lead_score"] = 50
        else:
            # Fallback
            state["current_intent"] = "general_inquiry"
            state["confidence"] = 0.5
            state["sentiment"] = "neutral"
            state["lead_score"] = 50

        state["workflow_step"] = "intent_classified"
        return state
    
    def _detect_topic(self, state: ConversationState) -> ConversationState:
        """Detect conversation topic"""
        intent = state["current_intent"]
        
        # Map intent to topic
        topic_mapping = {
            "bachelor_programs": "bachelor_programs",
            "master_programs": "master_programs", 
            "employee_services": "employee_services",
            "student_services": "student_services",
            "partnership": "partnership",
            "button_response": state.get("conversation_topic", "general"),
            "general_inquiry": "general"
        }
        
        new_topic = topic_mapping.get(intent, "general")
        
        # Update topic depth
        if state.get("conversation_topic") == new_topic:
            state["topic_depth"] = state.get("topic_depth", 0) + 1
        else:
            state["topic_depth"] = 0
            
        state["conversation_topic"] = new_topic
        state["workflow_step"] = "topic_detected"
        return state
    
    def _gather_context(self, state: ConversationState) -> ConversationState:
        """Gather additional context"""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]["content"]
        
        context_info = {
            "message_length": len(last_message.split()),
            "contains_question": any(word in last_message.lower() for word in ["how", "what", "where", "when", "why", "which", "?"]),
            "contains_greeting": any(word in last_message.lower() for word in ["hello", "hi", "hallo", "guten tag"]),
            "urgency_indicators": any(word in last_message.lower() for word in ["urgent", "asap", "emergency", "dringend"]),
            "user_type": state["user_type"]
        }
        
        state["context"].update(context_info)
        state["workflow_step"] = "context_gathered"
        return state
    
    def _generate_response(self, state: ConversationState) -> ConversationState:
        """Generate appropriate response using GPT-4o-mini"""
        topic = state["conversation_topic"]
        intent = state["current_intent"]
        user_type = state["user_type"]
        language = state["language"]

        logger.info("\n🤖 RESPONSE GENERATION STARTED")
        logger.info(f"   ├─ Topic: {topic}")
        logger.info(f"   ├─ Intent: {intent}")
        logger.info(f"   ├─ User Type: {user_type}")
        logger.info(f"   └─ Language: {language}")

        try:
            # Generate base response for fallback
            if state["context"].get("is_button_response"):
                logger.info("   📍 Response Path: Button Response Handler")
                base_response = self._handle_button_response(state)
            elif topic == "bachelor_programs":
                logger.info("   📍 Response Path: Bachelor Programs")
                base_response = self._generate_bachelor_response(state)
            elif topic == "master_programs":
                logger.info("   📍 Response Path: Master Programs")
                base_response = self._generate_master_response(state)
            elif topic == "employee_services":
                logger.info("   📍 Response Path: Employee Services")
                base_response = self._generate_employee_response(state)
            elif topic == "student_services":
                logger.info("   📍 Response Path: Student Services")
                base_response = self._generate_student_response(state)
            else:
                logger.info("   📍 Response Path: General Response")
                base_response = self._generate_general_response(state)

            logger.info(f"   ✅ Base response generated: {len(base_response)} chars")

            # Use GPT-4o-mini for intelligent, context-aware response
            if self.use_openai:
                logger.info("   🚀 Enhancing with OpenAI GPT-4o-mini...")
                try:
                    gpt_response = self._enhance_with_openai(state, base_response)
                    if gpt_response:
                        logger.info(f"   ✅ GPT-4o-mini response received: {len(gpt_response)} chars")
                        response = gpt_response
                    else:
                        logger.info("   ⚠️ GPT-4o-mini returned None, using base response")
                        response = base_response
                except Exception as e:
                    logger.error(f"   ❌ GPT-4o-mini failed: {e}")
                    print(f"GPT-4o-mini failed, using fallback: {e}")
                    response = base_response
            else:
                logger.info("   ⚠️ OpenAI not enabled, using base response")
                response = base_response

            state["context"]["generated_response"] = response

        except Exception as e:
            response = f"I apologize, but I encountered an error processing your request. Please contact our support team at info@hnu.de for assistance."
            state["context"]["generated_response"] = response

        state["workflow_step"] = "response_generated"
        return state
    
    def _generate_bachelor_response(self, state: ConversationState) -> str:
        """Generate bachelor programs response"""
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        bachelor_data = self.kb.get_bachelor_programs()
        
        if any(keyword in message for keyword in ["how many", "anzahl", "total", "alle"]):
            response = f"🎓 **HNU offers {bachelor_data['total']} bachelor's degree programs**"
            response += "\n📚 **Program Overview:**"
            
            for i, program in enumerate(bachelor_data['programs'], 1):
                response += f"\n{i}. **{program['name']}** ({program['code']})"
                response += f"\n   📅 Duration: {program['duration']} | 🌐 Language: {program['language']}"
            
            response += "\n🔗 **Useful Links:**"
            response += f"\n• [Complete Program Details]({bachelor_data['links']['main_page']})"
            response += f"\n• [Application Process]({bachelor_data['links']['application']})"
            response += f"\n• [Requirements]({bachelor_data['links']['requirements']})"
            
            state["topic_data"] = bachelor_data
            return response
            
        elif any(keyword in message for keyword in ["names", "list", "liste", "which", "welche"]):
            response = "📚 **Bachelor Programs at HNU:**"
            for program in bachelor_data['programs']:
                response += f"\n• **{program['name']}** ({program['code']}) - {program['faculty']} Faculty"
            
            response += f"\n🔗 [Detailed Information]({bachelor_data['links']['main_page']})"
            return response
        
        # Default response
        return f"🎓 HNU offers {bachelor_data['total']} bachelor programs across various fields including Business, Engineering, Information Technology, and Health Sciences. What specific information would you like to know?"
    
    def _generate_master_response(self, state: ConversationState) -> str:
        """Generate master programs response"""
        master_data = self.kb.get_master_programs()
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        
        if any(keyword in message for keyword in ["how many", "anzahl", "total", "alle"]):
            response = f"🎓 **HNU offers {master_data['total']} master's degree programs**"
            response += "\n📚 **Master Programs:**"
            
            for i, program in enumerate(master_data['programs'], 1):
                response += f"\n{i}. **{program['name']}** ({program['code']})"
                response += f"\n   📅 Duration: {program['duration']} | 🌐 Language: {program['language']}"
            
            response += f"\n🔗 [Master Programs Details]({master_data['links']['main_page']})"
            state["topic_data"] = master_data
            return response
        
        return f"🎓 HNU offers {master_data['total']} master programs for advanced studies. Would you like to see the complete list or learn about specific programs?"
    
    def _generate_employee_response(self, state: ConversationState) -> str:
        """Generate employee services response"""
        employee_services = self.kb.get_employee_services()
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        
        if any(keyword in message for keyword in ["it", "computer", "password", "vpn", "network"]):
            it_info = employee_services["it_support"]
            response = f"💻 **IT Support for Employees**"
            response += f"\n**Services available:**"
            for service in it_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Contact:** {it_info['contact']}"
            response += f"\n📞 **Phone:** {it_info['phone']}"
            response += f"\n🎫 [Create Support Ticket](https://helpdesk.hnu.de)"
            return response
            
        elif any(keyword in message for keyword in ["room", "booking", "meeting", "reserve"]):
            facilities_info = employee_services["facilities"]
            response = f"🏢 **Room Booking & Facilities**"
            response += f"\n**Services available:**"
            for service in facilities_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Contact:** {facilities_info['contact']}"
            response += f"\n📞 **Phone:** {facilities_info['phone']}"
            response += f"\n🌐 [Room Booking System](https://rooms.hnu.de)"
            return response
            
        elif any(keyword in message for keyword in ["hr", "payroll", "benefits", "leave", "vacation"]):
            hr_info = employee_services["hr_services"]
            response = f"👥 **Human Resources**"
            response += f"\n**Services available:**"
            for service in hr_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Contact:** {hr_info['contact']}"
            response += f"\n📞 **Phone:** {hr_info['phone']}"
            return response
        
        # General employee services
        response = "👔 **Employee Services at HNU:**"
        response += "\n**Available services:**"
        response += "\n• 💻 IT Support & Technical Issues"
        response += "\n• 🏢 Room Booking & Facilities"
        response += "\n• 👥 HR Services & Payroll"
        response += "\nWhat specific service do you need help with?"
        return response
    
    def _generate_student_response(self, state: ConversationState) -> str:
        """Generate student services response"""
        student_services = self.kb.get_student_services()
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        
        if any(keyword in message for keyword in ["enrollment", "register", "courses", "einschreibung"]):
            academic_info = student_services["academic_office"]
            response = f"📝 **Course Enrollment & Academic Services**"
            response += f"\n**Services available:**"
            for service in academic_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Contact:** {academic_info['contact']}"
            response += f"\n📞 **Phone:** {academic_info['phone']}"
            response += f"\n🌐 [Student Portal](https://portal.hnu.de)"
            return response
            
        elif any(keyword in message for keyword in ["library", "books", "research", "bibliothek"]):
            library_info = student_services["library"]
            response = f"📚 **Library Services**"
            response += f"\n**Services available:**"
            for service in library_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Contact:** {library_info['contact']}"
            response += f"\n📞 **Phone:** {library_info['phone']}"
            response += f"\n🏛️ **Opening Hours:** Mon-Fri 8:00-20:00, Sat 9:00-16:00"
            return response
        
        # General student services
        response = "🎓 **Student Services at HNU:**"
        response += "\n**Available services:**"
        response += "\n• 📝 Course Enrollment & Academic Affairs"
        response += "\n• 🎯 Student Counseling & Support"
        response += "\n• 📚 Library & Research Resources"
        response += "\nWhat do you need help with today?"
        return response
    
    def _generate_general_response(self, state: ConversationState) -> str:
        """Generate general response"""
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        
        if any(greeting in message for greeting in ["hello", "hi", "hallo", "guten tag"]):
            return f"👋 Hello! I'm your HNU support assistant. I can help you with: \n• 🎓 Bachelor & Master programs \n• 👔 Employee services (IT, HR, Facilities) \n• 🎓 Student services (Enrollment, Library) \n• 🤝 Partnership opportunities \nHow can I assist you today?"
        
        return "I'm here to help with information about HNU services. You can ask me about programs, services, or any other university-related topics. What would you like to know?"
    
    def _handle_button_response(self, state: ConversationState) -> str:
        """Handle button click responses"""
        button_action = state["context"]["button_action"]
        topic = state["conversation_topic"]
        
        if button_action == "show_all_programs":
            if topic == "bachelor_programs":
                bachelor_data = self.kb.get_bachelor_programs()
                response = "📚 **All Bachelor Programs:**"
                for program in bachelor_data['programs']:
                    response += f"\n• **{program['name']}** ({program['code']}) - {program['faculty']} Faculty"
                return response
                
        elif button_action == "application_info":
            return "📝 **Application Information:**\n\n**Steps to apply:**\n1. Visit the HNU application portal\n2. Create your account\n3. Submit required documents\n4. Pay application fee (if applicable)\n5. Wait for admission decision\n\n🔗 [Application Portal](https://www.hnu.de/bewerbung)\n📧 **Questions?** Contact admissions@hnu.de"
            
        elif button_action == "contact_info":
            return "📞 **HNU Contact Information:**\n\n**Main Office:**\n📧 info@hnu.de\n📞 +49 731 9762-0\n\n**Student Services:**\n📧 student@hnu.de\n📞 +49 731 9762-1500\n\n**IT Support:**\n📧 it@hnu.de\n📞 +49 731 9762-1234"
            
        elif button_action == "more_details":
            return "I'd be happy to provide more details! Please let me know specifically what you'd like to know more about."
            
        elif button_action == "continue_topic":
            return "Great! Please continue with your questions about this topic. What else would you like to know?"
            
        elif button_action == "change_topic":
            state["conversation_topic"] = "general"
            state["topic_depth"] = 0
            return "Topic changed. What would you like to know about now?"
        
        return "I understand. How else can I help you today?"
    
    def _enhance_with_openai(self, state: ConversationState, base_response: str) -> Optional[str]:
        """Generate response using GPT-4o-mini with full context"""
        logger.info("="*80)
        logger.info("🚀 STARTING OPENAI API CALL - COMPLETE DATA FLOW")
        logger.info("="*80)

        if not self.use_openai:
            logger.warning("⚠️ OpenAI is not enabled (API key missing)")
            return None

        try:
            # Extract basic data from state
            message = state["messages"][-1]["content"] if state["messages"] else ""
            user_type = state["user_type"]
            language = state["language"]
            analysis = state.get("analysis_result", {})
            user_stats = state.get("user_stats", {})
            faiss_context = state.get("faiss_context", [])

            logger.info("📥 INPUT DATA EXTRACTION:")
            logger.info(f"   ├─ User Message: {message}")
            logger.info(f"   ├─ User Type: {user_type}")
            logger.info(f"   ├─ Language: {language}")
            logger.info(f"   ├─ Message Length: {len(message)} chars, {len(message.split())} words")
            logger.info(f"   └─ Base Response Length: {len(base_response)} chars")

            # Build rich context
            context_parts = []

            logger.info("\n🔍 ANALYSIS RESULTS:")
            logger.info(f"   ├─ Intent: {analysis.get('intent', 'N/A')}")
            logger.info(f"   ├─ Intent Confidence: {analysis.get('intent_confidence', 0):.4f}")
            logger.info(f"   ├─ Sentiment: {analysis.get('sentiment', 'N/A')}")
            logger.info(f"   ├─ Sentiment Confidence: {analysis.get('sentiment_confidence', 0):.4f}")
            logger.info(f"   ├─ Lead Score: {analysis.get('lead_score', 50)}")
            logger.info(f"   ├─ Is Negative Intent: {analysis.get('is_negative_intent', False)}")
            logger.info(f"   └─ Bias Level: {analysis.get('bias_level', 'N/A')}")

            # Check for similar previous chat from OLD sessions only
            similar_chat = None
            user_id = state.get("user_id", "guest")
            session_id = state.get("session_id", "")

            logger.info("\n👤 USER IDENTIFICATION:")
            logger.info(f"   ├─ User ID: {user_id}")
            logger.info(f"   ├─ Session ID: {session_id}")
            logger.info(f"   └─ Analyzer Available: {self.analyzer is not None}")

            # NEW: Find similar messages with context (1 before + current + 1 after)
            similar_messages_with_context = []
            if self.chat_db and user_id != "guest":
                logger.info("\n🔄 SEARCHING FOR SIMILAR MESSAGES WITH CONTEXT...")
                similar_messages_with_context = self.chat_db.find_similar_messages_with_context(
                    current_message=message,
                    user_id=user_id,
                    current_session_id=session_id,
                    limit=5,
                    min_similarity=0.4
                )
                if similar_messages_with_context:
                    logger.info(f"   ✅ Found {len(similar_messages_with_context)} similar messages")
                    for i, sm in enumerate(similar_messages_with_context, 1):
                        logger.info(f"      {i}. Similarity: {sm['similarity_score']:.1%} - \"{sm['current_message']['content'][:50]}...\"")
                else:
                    logger.info(f"   ⚠️ No similar messages found")

            # Session-level user personalization WITH PER-SESSION AGGREGATES
            session_stats = state.get("session_stats", {})

            logger.info("\n📊 SESSION STATISTICS:")
            if session_stats and session_stats.get("total_sessions", 0) > 0:
                logger.info(f"   ├─ Total Sessions: {session_stats.get('total_sessions', 0)}")
                logger.info(f"   └─ Sessions Analyzed: {len(session_stats.get('session_summaries', []))}")

                context_parts.append(f"\n**👤 User Profile (Last 10 Sessions Aggregated):**")
                context_parts.append(f"- Total Previous Sessions: {session_stats.get('total_sessions', 0)}")
                context_parts.append(f"- Sessions with Data: {len(session_stats.get('session_summaries', []))}")

                # Show PER-SESSION aggregates with intent set
                summaries = session_stats.get('session_summaries', [])[:5]
                if summaries:
                    logger.info("\n   📋 SESSION SUMMARIES (Last 5 Sessions):")
                    for i, sess in enumerate(summaries, 1):
                        logger.info(f"      Session {i}:")
                        logger.info(f"         ├─ Messages: {sess.get('message_count', 0)}")
                        logger.info(f"         ├─ Intent Set: {sess.get('intent_set', [])}")
                        logger.info(f"         ├─ Dominant Intent: {sess.get('dominant_intent', 'N/A')}")
                        logger.info(f"         ├─ Dominant Sentiment: {sess.get('dominant_sentiment', 'N/A')}")
                        logger.info(f"         ├─ Avg Lead Score: {sess.get('avg_lead_score', 50)}")
                        logger.info(f"         └─ First Topic: {sess.get('first_message', '')[:60]}...")

                    context_parts.append("\n**Session History (Last 5 Sessions - Per-Session Aggregates):**")
                    for i, sess in enumerate(summaries, 1):
                        intent_set = sess.get('intent_set', [])
                        intent_str = f"{intent_set}" if intent_set else sess.get('dominant_intent', 'N/A')
                        context_parts.append(
                            f"{i}. Intents: {intent_str} | " +
                            f"Sentiment: {sess.get('dominant_sentiment', 'neutral')} | " +
                            f"Score: {sess.get('avg_lead_score', 50)} | " +
                            f"Topic: \"{sess.get('first_message', '')[:50]}...\""
                        )

                    # Overall patterns from all sessions
                    from collections import Counter
                    all_intents = [s.get('dominant_intent') for s in summaries if s.get('dominant_intent')]
                    all_sentiments = [s.get('dominant_sentiment') for s in summaries if s.get('dominant_sentiment')]

                    if all_intents:
                        intent_counts = Counter(all_intents)
                        most_common = intent_counts.most_common(2)
                        context_parts.append(f"\n**Most Frequent Session Topics:** {[i[0] for i in most_common]}")

                    if all_sentiments:
                        sentiment_counts = Counter(all_sentiments)
                        if sentiment_counts.get('negative', 0) >= 3:
                            context_parts.append("⚠️ User frustrated in multiple sessions - be extra helpful and empathetic")
                        elif sentiment_counts.get('positive', 0) >= 3:
                            context_parts.append("✅ User generally satisfied across sessions")

            # Add similar messages with context (1 before + current + 1 after)
            if similar_messages_with_context:
                logger.info("\n📝 SIMILAR MESSAGES WITH CONTEXT:")
                context_parts.append("\n**📝 Similar Previous Conversations (with Context):**")

                for i, sm in enumerate(similar_messages_with_context, 1):
                    logger.info(f"\n   Similar Message {i} (Similarity: {sm['similarity_score']:.1%}):")

                    # Log details
                    if sm.get('message_before'):
                        logger.info(f"      Before: [{sm['message_before']['role']}] {sm['message_before']['content'][:80]}...")

                    curr_msg = sm['current_message']
                    logger.info(f"      User: \"{curr_msg['content'][:80]}...\"")
                    logger.info(f"            Intent: {curr_msg.get('intent', 'N/A')} | Sentiment: {curr_msg.get('sentiment', 'N/A')} | Score: {curr_msg.get('lead_score', 'N/A')}")

                    if sm.get('message_after'):
                        logger.info(f"      After: [{sm['message_after']['role']}] {sm['message_after']['content'][:80]}...")

                    # Add to context for OpenAI
                    context_parts.append(f"\n{i}. **Similar Discussion** (Similarity: {sm['similarity_score']:.0%}):")

                    if sm.get('message_before'):
                        context_parts.append(f"   Context Before: [{sm['message_before']['role'].upper()}] \"{sm['message_before']['content'][:100]}...\"")

                    curr_msg = sm['current_message']
                    intent_str = curr_msg.get('intent', 'unknown')
                    sentiment_str = curr_msg.get('sentiment', 'neutral')
                    score_str = curr_msg.get('lead_score', 'N/A')

                    context_parts.append(f"   User Asked: \"{curr_msg['content'][:150]}...\"")
                    context_parts.append(f"   → Intent: {intent_str} | Sentiment: {sentiment_str} | Lead Score: {score_str}")

                    if sm.get('message_after'):
                        context_parts.append(f"   Response Given: \"{sm['message_after']['content'][:150]}...\"")

                context_parts.append("\n**💡 Instructions:** Use these similar conversations to understand user intent and provide consistent responses. If the user's sentiment changed (e.g., negative → positive), note what helped.")
            else:
                logger.info("\n📝 No similar messages found")

            # FAISS knowledge base context
            logger.info("\n📚 FAISS KNOWLEDGE BASE CONTEXT:")
            if faiss_context and len(faiss_context) > 0:
                logger.info(f"   Found {len(faiss_context)} relevant documents:")
                for i, doc in enumerate(faiss_context[:2], 1):
                    logger.info(f"   {i}. Text: {doc['text'][:150]}...")
                    logger.info(f"      Score: {doc.get('score', 'N/A')}")
                    logger.info(f"      Metadata: {doc.get('metadata', {})}")

                context_parts.append("\n**Relevant Information from Knowledge Base:**")
                for i, doc in enumerate(faiss_context[:2], 1):
                    context_parts.append(f"{i}. {doc['text'][:200]}...")
            else:
                logger.info("   No FAISS context available")

            # Intent and sentiment
            intent = analysis.get("intent", "general_query")
            sentiment = analysis.get("sentiment", "neutral")
            lead_score = analysis.get("lead_score", 50)
            context_parts.append(f"\nDetected Intent: {intent}")
            context_parts.append(f"User Sentiment: {sentiment} (Lead Score: {lead_score})")

            print(f"\n{'='*70}")
            print(f"🤖 GPT-4o-mini CONTEXT GENERATION")
            print(f"{'='*70}")
            print(f"📊 ANALYSIS RESULTS:")
            print(f"   Intent: {intent} (confidence: {analysis.get('intent_confidence', 0):.2f})")
            print(f"   Sentiment: {sentiment} (Lead Score: {lead_score})")
            print(f"   User Type: {user_type}")
            print(f"   Language: {language}")

            # Display session-level stats WITH AGGREGATES
            session_stats = state.get("session_stats", {})
            print(f"\n🐛 DEBUG: session_stats = {session_stats}")
            if session_stats and session_stats.get("total_sessions", 0) > 0:
                print(f"\n👤 USER HISTORY (Session-Level Aggregates):")
                print(f"   Total Sessions: {session_stats.get('total_sessions', 0)}")
                print(f"   Sessions with Data: {len(session_stats.get('session_summaries', []))}")

                # Show session summaries WITH PER-SESSION AGGREGATES
                summaries = session_stats.get('session_summaries', [])[:5]  # Last 5 sessions
                if summaries:
                    print(f"\n   📋 Session Aggregates (Last 5 Sessions):")
                    for i, sess in enumerate(summaries, 1):
                        print(f"\n      Session {i}:")
                        print(f"         Messages: {sess.get('message_count', 0)} user messages")
                        print(f"         Intent Set: {sess.get('intent_set', [])}")
                        print(f"         Dominant Intent: {sess.get('dominant_intent', 'N/A')}")
                        print(f"         Dominant Sentiment: {sess.get('dominant_sentiment', 'N/A')}")
                        print(f"         Avg Lead Score: {sess.get('avg_lead_score', 50)}")
                        print(f"         First Topic: \"{sess.get('first_message', '')[:70]}...\"")
                        print(f"         Date: {sess.get('created_at', 'N/A')}")
                else:
                    print("\n   ⚠️ No previous session data found")

            # ALSO show old per-message stats if available
            old_user_stats = state.get("user_stats", {})
            if old_user_stats and old_user_stats.get('total_messages', 0) > 0:
                print(f"\n📊 HISTORICAL MESSAGE-LEVEL STATS:")
                print(f"   Total Historical Messages: {old_user_stats.get('total_messages', 0)}")

                recent_intents = old_user_stats.get('recent_intents', [])
                recent_sentiments = old_user_stats.get('recent_sentiments', [])
                recent_scores = old_user_stats.get('recent_scores', [])

                if recent_intents:
                    print(f"\n   Recent Intents (last {len(recent_intents)} messages):")
                    from collections import Counter
                    intent_counts = Counter(recent_intents[:10])
                    for intent, count in intent_counts.most_common(5):
                        print(f"      • {intent}: {count} times")

                if recent_sentiments:
                    print(f"\n   Recent Sentiments (last {len(recent_sentiments)} messages):")
                    sentiment_counts = Counter(recent_sentiments[:10])
                    for sentiment, count in sentiment_counts.most_common():
                        print(f"      • {sentiment}: {count} times")

                if recent_scores:
                    avg_score = sum(recent_scores[:10]) / min(len(recent_scores), 10)
                    print(f"\n   Avg Recent Lead Score: {avg_score:.1f}")

            if similar_messages_with_context:
                print(f"\n🔄 SIMILAR MESSAGES WITH CONTEXT:")
                print(f"   Found {len(similar_messages_with_context)} similar conversations")
                for i, sm in enumerate(similar_messages_with_context[:3], 1):  # Show first 3
                    print(f"\n   {i}. Similarity: {sm['similarity_score']:.0%}")
                    curr = sm['current_message']
                    print(f"      User: \"{curr['content'][:60]}...\"")
                    print(f"      Intent: {curr.get('intent', 'N/A')} | Sentiment: {curr.get('sentiment', 'N/A')}")
                    if sm.get('message_after'):
                        print(f"      Response: \"{sm['message_after']['content'][:60]}...\"")

            if faiss_context and len(faiss_context) > 0:
                print(f"\n📚 FAISS KNOWLEDGE BASE:")
                for i, doc in enumerate(faiss_context[:2], 1):
                    print(f"   {i}. {doc['text'][:100]}...")

            full_context = "\n".join(context_parts)

            # Build conversation history
            conversation_history = []
            messages = state.get("messages", [])

            logger.info("\n💬 CONVERSATION HISTORY:")
            logger.info(f"   Total messages in current session: {len(messages)}")

            # Add previous messages from current session
            for msg in messages[:-1]:  # Exclude the last message (current one)
                role = msg.get("role", "user")
                content = msg.get("content", "")
                conversation_history.append(f"{role.title()}: {content}")
                logger.debug(f"   {role.title()}: {content[:100]}...")

            # Format conversation history
            if conversation_history:
                history_text = "\n**Current Session Conversation History:**\n" + "\n".join(conversation_history[-10:])  # Last 10 messages
                print(f"\n💬 CURRENT SESSION HISTORY:")
                print(f"   Messages in session: {len(messages)}")
                for i, msg_txt in enumerate(conversation_history[-5:], 1):  # Show last 5
                    print(f"   {i}. {msg_txt[:80]}...")
            else:
                history_text = ""
                print(f"\n💬 CURRENT SESSION HISTORY: First message")

            print(f"{'='*70}\n")

            # Analyze tone and cultural context from message and history
            message_tone = self._analyze_tone(message, sentiment)
            cultural_context = self._detect_cultural_context(message, language, similar_messages_with_context)
            sentiment_trend = self._analyze_sentiment_trend(similar_messages_with_context, sentiment)

            # Build enhanced personalized prompt
            system_prompt = f"""You are a warm, empathetic, and highly personalized assistant for HNU (Hochschule Neu-Ulm University) in Germany. You remember past conversations and build genuine relationships with users.

**🎯 Current User Context:**
- User Type: {user_type}
- Preferred Language: {language}
- Current Tone: {message_tone}
- Sentiment: {sentiment} (Engagement: {analysis.get('lead_score', 50)}/100)
- Cultural Background: {cultural_context}

**📊 User's Journey & Patterns:**
{full_context}

**💬 Current Conversation Flow:**
{history_text}

**🎭 Personalization Guidelines:**

1. **Be Human & Conversational:**
   - Talk like a supportive colleague, NOT a robot
   - Use natural language: "Hey, I see you're asking about..."  
   - Show empathy: Acknowledge their feelings and situation
   - Be warm but professional

2. **Reference Past Interactions Naturally:**
   - If you see similar previous conversations, mention them: "Oh, this reminds me of when you asked about..."
   - Show continuity: "Last time this happened, we solved it by... does that still work for you?"
   - Acknowledge growth: "I see you've been dealing with this before - let's make sure we fix it properly this time"

3. **Adapt to Their Emotional State:**
   {sentiment_trend}
   - Current feeling: {sentiment}
   - If frustrated: Be extra patient, validate feelings, offer step-by-step help
   - If satisfied: Share their enthusiasm, reinforce success
   - If neutral: Be informative but keep it engaging

4. **Cultural & Communication Awareness:**
   {cultural_context}
   - If they use idioms/colloquialisms: Understand the meaning, respond naturally
   - If formal: Match their formality level
   - If casual: Be friendly and approachable
   - Respect cultural communication styles (German directness vs. English politeness)

5. **Resource-Aware Responses:**
   - Use the HNU Resource Database resources.json to provide verified contacts, links, and relevant support information.
   - Always include a short helpful summary, then the contacts and URLs.
   - When users ask about a topic (e.g., accommodation, IT, international office, etc.), the assistant should search within the resource file and return the most relevant items, formatted cleanly.
   - If the user says, ‘I need help with my Wi-Fi’, respond using IT Support info from the database.
   - If no relevant resource is found, politely inform the user and suggest contacting
   
   
6. **Learn from What Worked Before:**
   - Check similar conversations: What responses led to positive outcomes?
   - If their sentiment improved after specific help: Mention that approach
   - If they were frustrated before and got help: Acknowledge and build trust

7. **Personalized Response Strategy:**
   - Keep it concise (2-4 sentences) but meaningful
   - Reference specific details from their history when relevant
   - Offer next steps or ask follow-up questions
   - Include contact info only if they seem stuck: info@hnu.de

8. **Language & Style:**
   - Respond in {"German" if language == "de" else "English"}
   - Mirror their communication style (formal/casual)
   - Avoid jargon unless they use it
   - If they use humor, be lighthearted; if serious, be professional

9. **Continuity & Memory:**
   - Show you remember: "You mentioned last time that..."
   - Build on previous solutions: "Since X worked before, let's try Y now"
   - Acknowledge recurring patterns: "I notice this is the third time - let's find a permanent solution"


**🚫 What NOT to Do:**
- Don't sound robotic or templated
- Don't repeat information they already know from previous chats
- Don't ignore their emotional state
- Don't miss cultural cues or idioms
- Don't give generic responses when you have their history
- Don't be overly formal if they're casual (or vice versa)

**✨ Goal:** Make them feel understood, remembered, and genuinely helped - like talking to a smart, caring friend who actually knows them."""

            # Build messages array for OpenAI
            messages_for_gpt = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]

            # Simplified logging - just the essentials
            logger.info("─" * 80)
            logger.info("📤 SENDING TO OPENAI")
            logger.info(f"User Message: \"{message}\"")
            logger.info(f"System Prompt Length: {len(system_prompt)} chars")

            # Only log full details to file, not console
            import logging
            file_logger = logging.getLogger(__name__ + '.detailed')
            file_logger.info("\n" + "="*80)
            file_logger.info("📤 COMPLETE OPENAI API REQUEST (Detailed)")
            file_logger.info(f"Model: gpt-4o-mini | Tokens: 300 | Temp: 0.7")
            file_logger.info("\nSYSTEM PROMPT:")
            file_logger.info(system_prompt)
            file_logger.info("\nUSER MESSAGE:")
            file_logger.info(message)
            file_logger.info("\nCOMPLETE JSON PAYLOAD:")
            payload_dict = {
                "model": "gpt-4o-mini",
                "messages": messages_for_gpt,
                "max_tokens": 300,
                "temperature": 0.7
            }
            file_logger.info(json.dumps(payload_dict, indent=2))
            file_logger.info("="*80)

            # ==========================================
            # PARALLEL CALLS: Personalized + RAG-Only
            # ==========================================

            logger.info("\n🔀 MAKING TWO PARALLEL OPENAI CALLS...")
            logger.info("   1. Personalized Response (full context)")
            logger.info("   2. RAG-Only Response (history + knowledge base only)")

            # BUILD RAG-ONLY PROMPT (Simple, no personalization)
            rag_only_prompt = f"""You are a helpful assistant for HNU (Hochschule Neu-Ulm University) in Germany.

**Current Conversation:**
{history_text if history_text else "First message in this session."}

**Relevant Knowledge Base Information:**
{chr(10).join([f"{i+1}. {doc['text'][:300]}..." for i, doc in enumerate(faiss_context[:5])]) if faiss_context else "No specific knowledge base results found."}

**Instructions:**
- Answer the user's question based on the conversation history and knowledge base information above
- Respond in {"German" if language == "de" else "English"}
- Be clear, factual, and helpful
- Keep response concise (2-4 sentences)
- If you don't have enough information, say so and suggest contacting info@hnu.de"""

            messages_for_rag = [
                {"role": "system", "content": rag_only_prompt},
                {"role": "user", "content": message}
            ]

            # CALL 1: Personalized Response
            logger.info("\n📤 CALL 1: Personalized (with full context)...")
            response_personalized = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_for_gpt,
                max_tokens=200,  # Reduced to 200 each (total ~400)
                temperature=0.7
            )
            personalized_content = response_personalized.choices[0].message.content
            tokens_personalized = response_personalized.usage.total_tokens if hasattr(response_personalized, 'usage') else 'N/A'

            logger.info(f"   ✅ Personalized response received: {len(personalized_content)} chars")
            logger.info(f"   Tokens: {tokens_personalized}")

            # CALL 2: RAG-Only Response
            logger.info("\n📤 CALL 2: RAG-Only (history + knowledge base)...")
            response_rag = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_for_rag,
                max_tokens=200,  # Reduced to 200 each
                temperature=0.7
            )
            rag_content = response_rag.choices[0].message.content
            tokens_rag = response_rag.usage.total_tokens if hasattr(response_rag, 'usage') else 'N/A'

            logger.info(f"   ✅ RAG-only response received: {len(rag_content)} chars")
            logger.info(f"   Tokens: {tokens_rag}")

            # COMBINE RESPONSES WITH NICE FORMATTING
            combined_response = f"""## 🎯 Personalized Response
{personalized_content}

{'─' * 80}

## 📚 RAG-Only Response
{rag_content}"""

            total_tokens = (tokens_personalized if tokens_personalized != 'N/A' else 0) + (tokens_rag if tokens_rag != 'N/A' else 0)

            # Simplified console output
            logger.info("📥 BOTH RESPONSES RECEIVED")
            logger.info(f"Personalized: {len(personalized_content)} chars")
            logger.info(f"RAG-Only: {len(rag_content)} chars")
            logger.info(f"Combined: {len(combined_response)} chars")
            logger.info(f"Total Tokens Used: {total_tokens}")
            logger.info("─" * 80)

            # Detailed logging to file only
            file_logger.info("\n✅ PERSONALIZED RESPONSE")
            file_logger.info(f"Response ID: {response_personalized.id}")
            file_logger.info(f"Model: {response_personalized.model}")
            file_logger.info(f"Finish Reason: {response_personalized.choices[0].finish_reason}")
            if hasattr(response_personalized, 'usage'):
                file_logger.info(f"Token Usage: {response_personalized.usage.prompt_tokens} prompt + {response_personalized.usage.completion_tokens} completion = {response_personalized.usage.total_tokens} total")
            file_logger.info(f"Content:\n{personalized_content}")

            file_logger.info("\n✅ RAG-ONLY RESPONSE")
            file_logger.info(f"Response ID: {response_rag.id}")
            file_logger.info(f"Model: {response_rag.model}")
            file_logger.info(f"Finish Reason: {response_rag.choices[0].finish_reason}")
            if hasattr(response_rag, 'usage'):
                file_logger.info(f"Token Usage: {response_rag.usage.prompt_tokens} prompt + {response_rag.usage.completion_tokens} completion = {response_rag.usage.total_tokens} total")
            file_logger.info(f"Content:\n{rag_content}")

            file_logger.info(f"\n📦 COMBINED RESPONSE:\n{combined_response}")
            file_logger.info("="*80 + "\n")

            return combined_response

        except Exception as e:
            logger.error("="*80)
            logger.error("❌ OPENAI API CALL FAILED")
            logger.error("="*80)
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            logger.error("="*80)
            logger.info(f"⚠️ Falling back to base response")
            print(f"GPT-4o-mini generation error: {e}")
            return base_response  # Fallback to base response
    
    def _add_interactive_elements(self, state: ConversationState) -> ConversationState:
        """Add interactive elements to the response"""
        topic = state["conversation_topic"]
        intent = state["current_intent"]
        depth = state["topic_depth"]
        user_type = state["user_type"]
        
        interactive_options = {"buttons": [], "continue_conversation": False}
        
        # Add buttons based on context
        if topic == "bachelor_programs" and depth == 0:
            interactive_options["buttons"] = [
                {"text": "📋 Show All Programs", "action": "show_all_programs"},
                {"text": "📝 Application Info", "action": "application_info"},
                {"text": "📞 Contact Admissions", "action": "contact_info"}
            ]
            interactive_options["continue_conversation"] = True
            
        elif topic == "master_programs" and depth == 0:
            interactive_options["buttons"] = [
                {"text": "📋 Show All Programs", "action": "show_all_programs"},
                {"text": "📝 Application Info", "action": "application_info"},
                {"text": "🎓 Prerequisites", "action": "prerequisites_info"}
            ]
            interactive_options["continue_conversation"] = True
            
        elif topic in ["employee_services", "student_services"] and depth == 0:
            interactive_options["buttons"] = [
                {"text": "📞 Contact Info", "action": "contact_info"},
                {"text": "💡 More Services", "action": "more_details"}
            ]
            
        elif depth > 0:  # Follow-up conversation
            interactive_options["buttons"] = [
                {"text": "✅ Continue Topic", "action": "continue_topic"},
                {"text": "🔄 Change Topic", "action": "change_topic"}
            ]
        
        # Generate suggested queries
        suggested_queries = self.kb.get_suggested_queries(topic, depth, user_type)
        
        state["interactive_options"] = interactive_options
        state["suggested_queries"] = suggested_queries
        state["workflow_step"] = "interactive_elements_added"
        return state
    
    def _finalize_response(self, state: ConversationState) -> ConversationState:
        """Finalize the response"""
        response = state["context"]["generated_response"]
        
        # Add response to messages
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "intent": state["current_intent"],
            "confidence": state["confidence"],
            "topic": state["conversation_topic"],
            "workflow_step": state["workflow_step"]
        })
        
        # Set followup requirements
        state["requires_followup"] = (
            state["confidence"] < 0.7 or
            state["interactive_options"].get("continue_conversation", False)
        )
        
        state["awaiting_response"] = state["requires_followup"]
        state["workflow_step"] = "finalized"
        return state
    
    async def process_message(
        self,
        message: str,
        user_type: str = "student",
        user_id: str = "guest",
        session_id: str = "default_session"
    ) -> Dict[str, Any]:
        """Process a message through the enhanced workflow"""

        logger.info("\n" + "="*80)
        logger.info(f"🎯 NEW MESSAGE: \"{message}\" (User: {user_type})")
        logger.info("="*80)

        # Create initial state
        initial_state = ConversationState(
            messages=[{"role": "user", "content": message, "timestamp": datetime.now().isoformat()}],
            user_type=user_type,
            user_id=user_id,
            current_intent="",
            confidence=0.0,
            language="en",
            context={},
            workflow_step="start",
            requires_followup=False,
            extracted_info={},
            conversation_topic="general",
            topic_depth=0,
            suggested_queries=[],
            interactive_options={},
            awaiting_response=False,
            topic_data={},
            session_id=session_id,
            sentiment="neutral",
            lead_score=50,
            analysis_result={},
            user_stats={},
            faiss_context=[]
        )
        
        try:
            # Configure for session-based memory
            config = {"configurable": {"thread_id": session_id}}

            logger.info("🔄 Running LangGraph workflow...")
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state, config=config)

            logger.info(f"✅ COMPLETED | Intent: {final_state.get('current_intent', 'N/A')} | Sentiment: {final_state.get('sentiment', 'N/A')} | Lead: {final_state.get('lead_score', 50)}")
            logger.info("="*80 + "\n")

            return final_state
            
        except Exception as e:
            print(f"Workflow error: {e}")
            # Return error response
            return {
                "messages": [
                    {"role": "user", "content": message, "timestamp": datetime.now().isoformat()},
                    {
                        "role": "assistant", 
                        "content": f"I apologize, but I encountered an error: {str(e)}\n\nPlease contact our support team at info@hnu.de for assistance.",
                        "timestamp": datetime.now().isoformat(),
                        "error": True
                    }
                ],
                "interactive_options": {},
                "suggested_queries": ["Contact support", "Try a different question"],
                "conversation_topic": "error",
                "current_intent": "error_handling",
                "confidence": 0.0
            }
    
    def get_response(self, message: str, user_type: str = "student", session_id: str = "default") -> str:
        """Synchronous wrapper for getting responses"""
        try:
            # Run the async method
            result = asyncio.run(self.process_message(message, user_type, session_id))
            
            # Extract the last assistant message
            assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]
            
            if assistant_messages:
                return assistant_messages[-1]["content"]
            else:
                return "I'm sorry, I couldn't process your request. Please try again or contact support at info@hnu.de"
                
        except Exception as e:
            return f"Error: {str(e)}\n\nPlease contact support at info@hnu.de for assistance."

    def _analyze_tone(self, message: str, sentiment: str) -> str:
        """Analyze message tone from content and sentiment"""
        message_lower = message.lower()

        # Check for urgency/frustration markers
        if any(word in message_lower for word in ['urgent', 'asap', 'immediately', 'now', '!!!', 'please help']):
            return "Urgent/Frustrated"
        elif any(word in message_lower for word in ['thanks', 'thank you', 'appreciate', 'great', 'awesome']):
            return "Grateful/Positive"
        elif '?' in message and sentiment == 'neutral':
            return "Curious/Inquisitive"
        elif sentiment == 'negative':
            return "Frustrated/Concerned"
        elif sentiment == 'positive':
            return "Satisfied/Enthusiastic"
        else:
            return "Neutral/Professional"

    def _detect_cultural_context(self, message: str, language: str, similar_messages: List[Dict]) -> str:
        """Detect cultural communication style and preferences"""
        message_lower = message.lower()

        # Detect formality level
        formal_markers = ['sehr geehrte', 'mit freundlichen grüßen', 'dear sir', 'yours sincerely', 'kindly']
        casual_markers = ['hi', 'hey', 'hallo', 'danke', 'thanks', 'cheers']

        is_formal = any(marker in message_lower for marker in formal_markers)
        is_casual = any(marker in message_lower for marker in casual_markers)

        # Check previous messages for patterns
        previous_style = "balanced"
        if similar_messages:
            casual_count = sum(1 for sm in similar_messages
                             if any(marker in sm['current_message']['content'].lower()
                                   for marker in casual_markers))
            formal_count = sum(1 for sm in similar_messages
                             if any(marker in sm['current_message']['content'].lower()
                                   for marker in formal_markers))
            if casual_count > formal_count:
                previous_style = "casual"
            elif formal_count > casual_count:
                previous_style = "formal"

        # Detect idioms or colloquialisms
        has_idioms = bool(re.search(r'(it\'s|isn\'t|won\'t|can\'t|gonna|wanna)', message_lower))

        if language == 'de':
            if is_formal:
                return "German (Formal) - Expects direct, structured responses with proper formality"
            else:
                return "German (Casual) - Appreciates directness but in a friendly manner"
        else:
            if is_formal:
                return "English (Formal) - Professional, polite communication expected"
            elif is_casual or has_idioms:
                return "English (Casual) - Friendly, conversational style preferred"
            elif previous_style == "casual":
                return "English (Relaxed) - User typically communicates informally"
            elif previous_style == "formal":
                return "English (Professional) - User maintains professional tone"
            else:
                return "English (Balanced) - Adapt to user's style"

    def _analyze_sentiment_trend(self, similar_messages: List[Dict], current_sentiment: str) -> str:
        """Analyze how sentiment changed over previous interactions"""
        if not similar_messages:
            return f"- First interaction or no history - Start positively"

        # Get sentiment progression
        sentiments = []
        for sm in similar_messages:
            msg_sentiment = sm['current_message'].get('sentiment')
            if msg_sentiment:
                sentiments.append(msg_sentiment)

        if not sentiments:
            return f"- No previous sentiment data - Be warm and helpful"

        # Count sentiment types
        negative_count = sentiments.count('negative')
        positive_count = sentiments.count('positive')
        neutral_count = sentiments.count('neutral')

        # Analyze trend
        if negative_count >= 2:
            if current_sentiment == 'positive':
                return f"- 🎉 GREAT NEWS: User was frustrated before ({negative_count}x negative) but now seems better! Acknowledge this positive change!"
            else:
                return f"- ⚠️ RECURRING FRUSTRATION: User has been negative {negative_count} times before. Be EXTRA empathetic, patient, and solution-focused."

        elif positive_count >= 2:
            if current_sentiment == 'negative':
                return f"- 😟 UNEXPECTED ISSUE: User was usually satisfied ({positive_count}x positive) but now upset. Something went wrong - investigate carefully!"
            else:
                return f"- ✅ CONSISTENT SATISFACTION: User generally happy ({positive_count}x positive). Maintain this positive relationship!"

        # Check for improvement/decline
        if len(sentiments) >= 2:
            if sentiments[0] == 'negative' and sentiments[-1] != 'negative':
                return f"- 📈 IMPROVING: Sentiment got better over time. Keep up the good support!"
            elif sentiments[0] != 'negative' and sentiments[-1] == 'negative':
                return f"- 📉 DECLINING: User getting more frustrated. Need to address root cause!"

        return f"- Mixed history ({positive_count} positive, {negative_count} negative, {neutral_count} neutral) - Be adaptive"


# Test function
def test_chatbot():
    """Test the enhanced chatbot"""
    print("🧪 Testing Enhanced HNU Chatbot...")
    
    chatbot = EnhancedHNUChatbot()
    
    test_queries = [
        "How many bachelor programs are there?",
        "I need IT support",
        "Library opening hours",
        "Show me master programs"
    ]
    
    for query in test_queries:
        print(f"❓ Query: {query}")
        response = chatbot.get_response(query, user_type="student")
        print(f"🤖 Response: {response[:200]}...")

if __name__ == "__main__":
    test_chatbot()