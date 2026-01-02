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
        self.workflow = self._create_workflow()
        
        # Intent patterns for basic classification
        self.intent_patterns = {
            "bachelor_programs": ["bachelor", "undergraduate", "bachelor's", "study programs", "degree programs"],
            "master_programs": ["master", "graduate", "master's", "mba", "postgraduate"],
            "employee_services": ["employee", "staff", "it support", "hr", "payroll", "room booking"],
            "student_services": ["student", "enrollment", "transcript", "library", "courses"],
            "partnership": ["partner", "collaboration", "research", "cooperation"],
            "general_inquiry": ["hello", "hi", "help", "info", "information", "contact"]
        }
        
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
    
    def _classify_intent(self, state: ConversationState) -> ConversationState:
        """Classify user intent"""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]["content"].lower()
        
        if state["context"].get("is_button_response"):
            state["current_intent"] = "button_response"
            state["confidence"] = 0.95
        else:
            # Simple pattern matching for intent classification
            best_intent = "general_inquiry"
            max_score = 0
            
            for intent, patterns in self.intent_patterns.items():
                score = sum(1 for pattern in patterns if pattern in last_message)
                if score > max_score:
                    max_score = score
                    best_intent = intent
            
            state["current_intent"] = best_intent
            state["confidence"] = min(0.9, max_score * 0.3) if max_score > 0 else 0.5
        
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
        """Generate appropriate response"""
        topic = state["conversation_topic"]
        intent = state["current_intent"]
        user_type = state["user_type"]
        language = state["language"]
        
        try:
            if state["context"].get("is_button_response"):
                response = self._handle_button_response(state)
            elif topic == "bachelor_programs":
                response = self._generate_bachelor_response(state)
            elif topic == "master_programs":
                response = self._generate_master_response(state)
            elif topic == "employee_services":
                response = self._generate_employee_response(state)
            elif topic == "student_services":
                response = self._generate_student_response(state)
            else:
                response = self._generate_general_response(state)
            
            # Use OpenAI for enhancement if available and confidence is low
            if self.use_openai and state["confidence"] < 0.6:
                try:
                    enhanced_response = self._enhance_with_openai(state, response)
                    if enhanced_response:
                        response = enhanced_response
                except Exception as e:
                    print(f"OpenAI enhancement failed: {e}")
            
            state["context"]["generated_response"] = response
            
        except Exception as e:
            response = f"I apologize, but I encountered an error processing your request. Please contact our support team at info@hnu.de for assistance. Error details: {str(e)}"
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
        """Enhance response using OpenAI"""
        if not self.use_openai:
            return None
        
        try:
            message = state["messages"][-1]["content"] if state["messages"] else ""
            user_type = state["user_type"]
            language = state["language"]
            
            prompt = f"""
            You are a helpful assistant for HNU (Hochschule Neu-Ulm) university.
            
            User query: {message}
            User type: {user_type}
            Language: {language}
            Base response: {base_response}
            
            Please enhance this response with additional helpful information while keeping it concise and relevant.
            Include specific contact information or next steps when appropriate.
            
            Respond in {"German" if language == "de" else "English"}.
            """
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI enhancement error: {e}")
            return None
    
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
        session_id: str = "default_session"
    ) -> Dict[str, Any]:
        """Process a message through the enhanced workflow"""
        
        # Create initial state
        initial_state = ConversationState(
            messages=[{"role": "user", "content": message, "timestamp": datetime.now().isoformat()}],
            user_type=user_type,
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
            session_id=session_id
        )
        
        try:
            # Configure for session-based memory
            config = {"configurable": {"thread_id": session_id}}
            
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state, config=config)
            
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