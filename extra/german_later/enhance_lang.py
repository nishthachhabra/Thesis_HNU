"""
Erweiterter HNU Chatbot mit LangGraph
Vollständige Implementierung mit interaktiven Features und Multi-Turn-Gesprächen
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
    print("Installiere LangGraph...")
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
    """Wissensdatenbank für HNU-Informationen"""
    
    @staticmethod
    def get_bachelor_programs():
        return {
            "total": 15,
            "programs": [
                {"name": "Betriebswirtschaft", "code": "BWL", "duration": "7 Semester", "language": "Deutsch/Englisch", "faculty": "Wirtschaft"},
                {"name": "Internationales Management", "code": "IM", "duration": "7 Semester", "language": "Englisch", "faculty": "Wirtschaft"},
                {"name": "Digitales Business Management", "code": "DBM", "duration": "7 Semester", "language": "Deutsch", "faculty": "Wirtschaft"},
                {"name": "Marketing Management", "code": "MM", "duration": "7 Semester", "language": "Deutsch", "faculty": "Wirtschaft"},
                {"name": "Logistik Management", "code": "LM", "duration": "7 Semester", "language": "Deutsch", "faculty": "Wirtschaft"},
                {"name": "Informationsmanagement", "code": "INM", "duration": "7 Semester", "language": "Deutsch", "faculty": "Information"},
                {"name": "Wirtschaftsingenieurwesen", "code": "WI", "duration": "7 Semester", "language": "Deutsch", "faculty": "Ingenieurwesen"},
                {"name": "Maschinenbau", "code": "MB", "duration": "7 Semester", "language": "Deutsch", "faculty": "Ingenieurwesen"},
                {"name": "Medizintechnik", "code": "MT", "duration": "7 Semester", "language": "Deutsch", "faculty": "Ingenieurwesen"},
                {"name": "Gesundheitsmanagement", "code": "GM", "duration": "7 Semester", "language": "Deutsch", "faculty": "Gesundheit"},
                {"name": "Soziale Arbeit", "code": "SA", "duration": "7 Semester", "language": "Deutsch", "faculty": "Soziales"},
                {"name": "Digitales Gesundheitsmanagement", "code": "DHM", "duration": "7 Semester", "language": "Deutsch", "faculty": "Gesundheit"},
                {"name": "Public Management", "code": "PM", "duration": "6 Semester", "language": "Deutsch", "faculty": "Öffentliches"},
                {"name": "Steuern und Prüfung", "code": "STP", "duration": "6 Semester", "language": "Deutsch", "faculty": "Wirtschaft"},
                {"name": "Angewandte Informatik", "code": "AI", "duration": "7 Semester", "language": "Deutsch", "faculty": "Information"}
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
                {"name": "Betriebswirtschaft", "code": "MBA", "duration": "3 Semester", "language": "Deutsch/Englisch", "faculty": "Wirtschaft"},
                {"name": "Internationales Management", "code": "MIM", "duration": "3 Semester", "language": "Englisch", "faculty": "Wirtschaft"},
                {"name": "Digitales Enterprise Management", "code": "DEM", "duration": "3 Semester", "language": "Deutsch", "faculty": "Wirtschaft"},
                {"name": "Informationsmanagement", "code": "MIM", "duration": "3 Semester", "language": "Deutsch", "faculty": "Information"},
                {"name": "Systemingenieurwesen", "code": "MSE", "duration": "3 Semester", "language": "Deutsch", "faculty": "Ingenieurwesen"},
                {"name": "Medizintechnik", "code": "MMT", "duration": "3 Semester", "language": "Deutsch", "faculty": "Ingenieurwesen"},
                {"name": "Gesundheitsmanagement", "code": "MHM", "duration": "3 Semester", "language": "Deutsch", "faculty": "Gesundheit"},
                {"name": "Public Administration", "code": "MPA", "duration": "4 Semester", "language": "Deutsch", "faculty": "Öffentliches"}
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
                "description": "IT-Support für Mitarbeiter",
                "contact": "it@hnu.de",
                "phone": "+49 731 9762-1234",
                "services": ["Hardware-Probleme", "Software-Installation", "Netzwerkprobleme", "E-Mail-Konfiguration"]
            },
            "hr_services": {
                "description": "Personalabteilung Support",
                "contact": "hr@hnu.de", 
                "phone": "+49 731 9762-2000",
                "services": ["Lohnabrechnung", "Leistungen", "Urlaubsmanagement", "Schulungen"]
            },
            "facilities": {
                "description": "Raumbuchung und Einrichtungen",
                "contact": "facilities@hnu.de",
                "phone": "+49 731 9762-3000",
                "services": ["Raumbuchung", "Ausrüstungsanfragen", "Wartung", "Veranstaltungsplanung"]
            }
        }
    
    @staticmethod
    def get_student_services():
        return {
            "academic_office": {
                "description": "Studienangelegenheiten und Einschreibung",
                "contact": "student@hnu.de",
                "phone": "+49 731 9762-1500",
                "services": ["Kurseinschreibung", "Zeugnisse", "Bescheinigungen", "Studienakten"]
            },
            "student_support": {
                "description": "Studienberatung und Support",
                "contact": "counseling@hnu.de",
                "phone": "+49 731 9762-1600",
                "services": ["Studienberatung", "Karriereberatung", "Persönlicher Support", "Studienplanung"]
            },
            "library": {
                "description": "Bibliotheksdienste",
                "contact": "library@hnu.de",
                "phone": "+49 731 9762-1700",
                "services": ["Buchausleihe", "Forschungsunterstützung", "Lernräume", "Digitale Ressourcen"]
            }
        }
    
    @staticmethod
    def get_suggested_queries(topic: str, depth: int, user_type: str) -> List[str]:
        """Kontextbewusste vorgeschlagene Anfragen abrufen"""
        suggestions = {
            "bachelor_programs": {
                0: [
                    "Zeig mir alle Bachelor-Programmnamen",
                    "Was sind die Zulassungsvoraussetzungen?", 
                    "Welche Programme werden auf Englisch unterrichtet?",
                    "Wie lange dauern Bachelor-Programme?"
                ],
                1: [
                    "Erzähl mir mehr über Betriebswirtschaft",
                    "Was sind die Berufsaussichten?",
                    "Wie bewerbe ich mich für diese Programme?",
                    "Was sind die Semestergebühren?"
                ]
            },
            "master_programs": {
                0: [
                    "Zeig mir alle Master-Programmnamen",
                    "Was sind die Voraussetzungen für Master-Programme?",
                    "Welche Master-Programme gibt es auf Englisch?",
                    "Wie unterscheiden sich Master- von Bachelor-Programmen?"
                ]
            },
            "employee_services": {
                0: [
                    "Ich brauche IT-Support",
                    "Wie buche ich einen Besprechungsraum?",
                    "Personalabteilung Kontaktinformationen",
                    "Passwort zurücksetzen Hilfe"
                ]
            },
            "student_services": {
                0: [
                    "Wie melde ich mich für Kurse an?",
                    "Ich brauche mein Zeugnis",
                    "Bibliotheksöffnungszeiten",
                    "Studienberatung"
                ]
            }
        }
        
        # Nutzertyp-spezifische Vorschläge
        user_suggestions = {
            "employee": ["IT-Support Kontakt", "Raumbuchung", "Personalabteilung Dienste", "VPN-Setup"],
            "student": ["Kurseinschreibung", "Zeugnisanfrage", "Bibliotheksdienste", "Studienunterstützung"],
            "partner": ["Partnerschaftsmöglichkeiten", "Veranstaltungsplanung", "Einrichtungsvermietung", "Zusammenarbeitsoptionen"]
        }
        
        base_suggestions = suggestions.get(topic, {}).get(depth, suggestions.get(topic, {}).get(0, []))
        user_specific = user_suggestions.get(user_type, [])
        
        return base_suggestions + user_specific[:2]  # Basis + 2 nutzerspezifisch kombinieren

class EnhancedHNUChatbot:
    """Erweiterter HNU Chatbot mit LangGraph-Workflow"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.use_openai = openai_api_key is not None and OPENAI_AVAILABLE
        
        if self.use_openai:
            openai.api_key = openai_api_key
        
        self.kb = HNUKnowledgeBase()
        self.memory = MemorySaver()
        self.workflow = self._create_workflow()
        
        # Intent-Muster für grundlegende Klassifikation (mit deutschen Keywords hinzugefügt)
        self.intent_patterns = {
            "bachelor_programs": ["bachelor", "undergraduate", "bachelor's", "study programs", "degree programs", "bachelor", "grundstudium", "studienprogramme", "studiengänge"],
            "master_programs": ["master", "graduate", "master's", "mba", "postgraduate", "master", "aufbaustudium", "mba"],
            "employee_services": ["employee", "staff", "it-support", "hr", "payroll", "room booking", "mitarbeiter", "personal", "it-support", "personalabteilung", "lohnabrechnung", "raumbuchung"],
            "student_services": ["student", "enrollment", "transcript", "library", "courses", "student", "einschreibung", "zeugnis", "bibliothek", "kurse"],
            "partnership": ["partner", "collaboration", "research", "cooperation", "partner", "zusammenarbeit", "forschung", "kooperation"],
            "general_inquiry": ["hello", "hi", "help", "info", "information", "contact", "hallo", "guten tag", "hilfe", "info", "informationen", "kontakt"]
        }
        
        print("✅ Erweiterter HNU Chatbot erfolgreich initialisiert!")
    
    def _create_workflow(self) -> StateGraph:
        """Den erweiterten LangGraph-Workflow erstellen"""
        
        workflow = StateGraph(ConversationState)
        
        # Knoten hinzufügen
        workflow.add_node("analyze_input", self._analyze_input)
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("detect_topic", self._detect_topic)
        workflow.add_node("gather_context", self._gather_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("add_interactive_elements", self._add_interactive_elements)
        workflow.add_node("finalize_response", self._finalize_response)
        
        # Kanten hinzufügen
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
        """Sprache des Eingabetexts erkennen"""
        if not LANGDETECT_AVAILABLE:
            # Einfache Fallback-Erkennung
            german_words = ['der', 'die', 'das', 'ich', 'und', 'mit', 'für', 'haben', 'sein']
            english_words = ['the', 'and', 'or', 'but', 'with', 'for', 'have', 'be', 'do']
            
            text_lower = text.lower()
            german_count = sum(1 for word in german_words if word in text_lower)
            english_count = sum(1 for word in english_words if word in text_lower)
            
            return "de" if german_count > english_count else "en"
        
        try:
            return detect(text)
        except:
            return "de"  # Standard auf Deutsch setzen für deutschen Bot
    
    def _analyze_input(self, state: ConversationState) -> ConversationState:
        """Benutzereingabe analysieren"""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]["content"]
        
        # Sprache erkennen
        state["language"] = self._detect_language(last_message)
        
        # Überprüfen, ob es eine Button-Antwort ist
        is_button_response = last_message.startswith("BTN:")
        state["context"]["is_button_response"] = is_button_response
        
        # Button-Aktion extrahieren, falls zutreffend
        if is_button_response:
            state["context"]["button_action"] = last_message.replace("BTN:", "").strip()
        
        state["workflow_step"] = "input_analyzed"
        return state
    
    def _classify_intent(self, state: ConversationState) -> ConversationState:
        """Benutzerintent klassifizieren"""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]["content"].lower()
        
        if state["context"].get("is_button_response"):
            state["current_intent"] = "button_response"
            state["confidence"] = 0.95
        else:
            # Einfache Musterabgleich für Intent-Klassifikation
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
        """Gesprächsthema erkennen"""
        intent = state["current_intent"]
        
        # Intent zu Thema zuordnen
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
        
        # Thementiefe aktualisieren
        if state.get("conversation_topic") == new_topic:
            state["topic_depth"] = state.get("topic_depth", 0) + 1
        else:
            state["topic_depth"] = 0
            
        state["conversation_topic"] = new_topic
        state["workflow_step"] = "topic_detected"
        return state
    
    def _gather_context(self, state: ConversationState) -> ConversationState:
        """Zusätzlichen Kontext sammeln"""
        if not state["messages"]:
            return state
            
        last_message = state["messages"][-1]["content"]
        
        context_info = {
            "message_length": len(last_message.split()),
            "contains_question": any(word in last_message.lower() for word in ["wie", "was", "wo", "wann", "warum", "welche", "?"]),
            "contains_greeting": any(word in last_message.lower() for word in ["hallo", "hi", "guten tag"]),
            "urgency_indicators": any(word in last_message.lower() for word in ["dringend", "asap", "notfall"]),
            "user_type": state["user_type"]
        }
        
        state["context"].update(context_info)
        state["workflow_step"] = "context_gathered"
        return state
    
    def _generate_response(self, state: ConversationState) -> ConversationState:
        """Passende Antwort generieren"""
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
            
            # OpenAI für Verbesserung nutzen, falls verfügbar und Konfidenz niedrig
            if self.use_openai and state["confidence"] < 0.6:
                try:
                    enhanced_response = self._enhance_with_openai(state, response)
                    if enhanced_response:
                        response = enhanced_response
                except Exception as e:
                    print(f"OpenAI-Verbesserung fehlgeschlagen: {e}")
            
            state["context"]["generated_response"] = response
            
        except Exception as e:
            response = f"Es tut mir leid, aber ich habe einen Fehler bei der Verarbeitung Ihrer Anfrage festgestellt. Bitte kontaktieren Sie unser Support-Team unter info@hnu.de für Unterstützung. Fehlerdetails: {str(e)}"
            state["context"]["generated_response"] = response
        
        state["workflow_step"] = "response_generated"
        return state
    
    def _generate_bachelor_response(self, state: ConversationState) -> str:
        """Antwort für Bachelor-Programme generieren"""
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        bachelor_data = self.kb.get_bachelor_programs()
        
        if any(keyword in message for keyword in ["wie viele", "anzahl", "total", "alle"]):
            response = f"🎓 **HNU bietet {bachelor_data['total']} Bachelor-Studiengänge an**"
            response += "\n📚 **Programmübersicht:**"
            
            for i, program in enumerate(bachelor_data['programs'], 1):
                response += f"\n{i}. **{program['name']}** ({program['code']})"
                response += f"\n   📅 Dauer: {program['duration']} | 🌐 Sprache: {program['language']}"
            
            response += "\n🔗 **Nützliche Links:**"
            response += f"\n• [Vollständige Programmdetails]({bachelor_data['links']['main_page']})"
            response += f"\n• [Bewerbungsprozess]({bachelor_data['links']['application']})"
            response += f"\n• [Voraussetzungen]({bachelor_data['links']['requirements']})"
            
            state["topic_data"] = bachelor_data
            return response
            
        elif any(keyword in message for keyword in ["namen", "liste", "welche"]):
            response = "📚 **Bachelor-Programme an der HNU:**"
            for program in bachelor_data['programs']:
                response += f"\n• **{program['name']}** ({program['code']}) - {program['faculty']} Fakultät"
            
            response += f"\n🔗 [Detaillierte Informationen]({bachelor_data['links']['main_page']})"
            return response
        
        # Standardantwort
        return f"🎓 HNU bietet {bachelor_data['total']} Bachelor-Programme in verschiedenen Bereichen wie Wirtschaft, Ingenieurwesen, Informationstechnologie und Gesundheitswissenschaften an. Welche spezifischen Informationen möchten Sie wissen?"
    
    def _generate_master_response(self, state: ConversationState) -> str:
        """Antwort für Master-Programme generieren"""
        master_data = self.kb.get_master_programs()
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        
        if any(keyword in message for keyword in ["wie viele", "anzahl", "total", "alle"]):
            response = f"🎓 **HNU bietet {master_data['total']} Master-Studiengänge an**"
            response += "\n📚 **Master-Programme:**"
            
            for i, program in enumerate(master_data['programs'], 1):
                response += f"\n{i}. **{program['name']}** ({program['code']})"
                response += f"\n   📅 Dauer: {program['duration']} | 🌐 Sprache: {program['language']}"
            
            response += f"\n🔗 [Master-Programme Details]({master_data['links']['main_page']})"
            state["topic_data"] = master_data
            return response
        
        return f"🎓 HNU bietet {master_data['total']} Master-Programme für fortgeschrittene Studien an. Möchten Sie die vollständige Liste sehen oder mehr über spezifische Programme erfahren?"
    
    def _generate_employee_response(self, state: ConversationState) -> str:
        """Antwort für Mitarbeiter-Dienste generieren"""
        employee_services = self.kb.get_employee_services()
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        
        if any(keyword in message for keyword in ["it", "computer", "passwort", "vpn", "netzwerk"]):
            it_info = employee_services["it_support"]
            response = f"💻 **IT-Support für Mitarbeiter**"
            response += f"\n**Verfügbare Dienste:**"
            for service in it_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Kontakt:** {it_info['contact']}"
            response += f"\n📞 **Telefon:** {it_info['phone']}"
            response += f"\n🎫 [Support-Ticket erstellen](https://helpdesk.hnu.de)"
            return response
            
        elif any(keyword in message for keyword in ["raum", "buchung", "meeting", "reservieren"]):
            facilities_info = employee_services["facilities"]
            response = f"🏢 **Raumbuchung & Einrichtungen**"
            response += f"\n**Verfügbare Dienste:**"
            for service in facilities_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Kontakt:** {facilities_info['contact']}"
            response += f"\n📞 **Telefon:** {facilities_info['phone']}"
            response += f"\n🌐 [Raumbuchungssystem](https://rooms.hnu.de)"
            return response
            
        elif any(keyword in message for keyword in ["personal", "lohnabrechnung", "leistungen", "urlaub"]):
            hr_info = employee_services["hr_services"]
            response = f"👥 **Personalabteilung**"
            response += f"\n**Verfügbare Dienste:**"
            for service in hr_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Kontakt:** {hr_info['contact']}"
            response += f"\n📞 **Telefon:** {hr_info['phone']}"
            return response
        
        # Allgemeine Mitarbeiter-Dienste
        response = "👔 **Mitarbeiter-Dienste an der HNU:**"
        response += "\n**Verfügbare Dienste:**"
        response += "\n• 💻 IT-Support & Technische Probleme"
        response += "\n• 🏢 Raumbuchung & Einrichtungen"
        response += "\n• 👥 Personalabteilung & Lohnabrechnung"
        response += "\nWomit benötigen Sie Hilfe?"
        return response
    
    def _generate_student_response(self, state: ConversationState) -> str:
        """Antwort für Studenten-Dienste generieren"""
        student_services = self.kb.get_student_services()
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        
        if any(keyword in message for keyword in ["einschreibung", "anmelden", "kurse"]):
            academic_info = student_services["academic_office"]
            response = f"📝 **Kurseinschreibung & Studienangelegenheiten**"
            response += f"\n**Verfügbare Dienste:**"
            for service in academic_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Kontakt:** {academic_info['contact']}"
            response += f"\n📞 **Telefon:** {academic_info['phone']}"
            response += f"\n🌐 [Studentenportal](https://portal.hnu.de)"
            return response
            
        elif any(keyword in message for keyword in ["bibliothek", "bücher", "forschung"]):
            library_info = student_services["library"]
            response = f"📚 **Bibliotheksdienste**"
            response += f"\n**Verfügbare Dienste:**"
            for service in library_info["services"]:
                response += f"\n• {service}"
            response += f"\n📧 **Kontakt:** {library_info['contact']}"
            response += f"\n📞 **Telefon:** {library_info['phone']}"
            response += f"\n🏛️ **Öffnungszeiten:** Mo-Fr 8:00-20:00, Sa 9:00-16:00"
            return response
        
        # Allgemeine Studenten-Dienste
        response = "🎓 **Studenten-Dienste an der HNU:**"
        response += "\n**Verfügbare Dienste:**"
        response += "\n• 📝 Kurseinschreibung & Studienangelegenheiten"
        response += "\n• 🎯 Studienberatung & Support"
        response += "\n• 📚 Bibliothek & Forschungsressourcen"
        response += "\nWomit können wir Ihnen heute helfen?"
        return response
    
    def _generate_general_response(self, state: ConversationState) -> str:
        """Allgemeine Antwort generieren"""
        message = state["messages"][-1]["content"].lower() if state["messages"] else ""
        
        if any(greeting in message for greeting in ["hallo", "hi", "guten tag"]):
            return f"👋 Hallo! Ich bin Ihr HNU-Support-Assistent. Ich kann Ihnen helfen mit: \n• 🎓 Bachelor- & Master-Programme \n• 👔 Mitarbeiter-Dienste (IT, Personal, Einrichtungen) \n• 🎓 Studenten-Dienste (Einschreibung, Bibliothek) \n• 🤝 Partnerschaftsmöglichkeiten \nWie kann ich Ihnen heute helfen?"
        
        return "Ich bin hier, um Ihnen mit Informationen zu HNU-Diensten zu helfen. Sie können mich zu Programmen, Diensten oder anderen universitätsbezogenen Themen fragen. Was möchten Sie wissen?"
    
    def _handle_button_response(self, state: ConversationState) -> str:
        """Button-Klick-Antworten handhaben"""
        button_action = state["context"]["button_action"]
        topic = state["conversation_topic"]
        
        if button_action == "show_all_programs":
            if topic == "bachelor_programs":
                bachelor_data = self.kb.get_bachelor_programs()
                response = "📚 **Alle Bachelor-Programme:**"
                for program in bachelor_data['programs']:
                    response += f"\n• **{program['name']}** ({program['code']}) - {program['faculty']} Fakultät"
                return response
                
        elif button_action == "application_info":
            return "📝 **Bewerbungsinformationen:**\n\n**Schritte zur Bewerbung:**\n1. Besuchen Sie das HNU-Bewerbungsportal\n2. Erstellen Sie Ihr Konto\n3. Reichen Sie die erforderlichen Dokumente ein\n4. Zahlen Sie die Bewerbungsgebühr (falls zutreffend)\n5. Warten Sie auf die Zulassungsentscheidung\n\n🔗 [Bewerbungsportal](https://www.hnu.de/bewerbung)\n📧 **Fragen?** Kontaktieren Sie admissions@hnu.de"
            
        elif button_action == "contact_info":
            return "📞 **HNU-Kontaktinformationen:**\n\n**Hauptbüro:**\n📧 info@hnu.de\n📞 +49 731 9762-0\n\n**Studenten-Dienste:**\n📧 student@hnu.de\n📞 +49 731 9762-1500\n\n**IT-Support:**\n📧 it@hnu.de\n📞 +49 731 9762-1234"
            
        elif button_action == "more_details":
            return "Gerne gebe ich mehr Details! Bitte lassen Sie mich wissen, worüber Sie speziell mehr wissen möchten."
            
        elif button_action == "continue_topic":
            return "Super! Fahren Sie mit Ihren Fragen zu diesem Thema fort. Was möchten Sie sonst noch wissen?"
            
        elif button_action == "change_topic":
            state["conversation_topic"] = "general"
            state["topic_depth"] = 0
            return "Thema geändert. Worüber möchten Sie jetzt sprechen?"
        
        return "Verstanden. Wie kann ich Ihnen sonst noch helfen?"
    
    def _enhance_with_openai(self, state: ConversationState, base_response: str) -> Optional[str]:
        """Antwort mit OpenAI verbessern"""
        if not self.use_openai:
            return None
        
        try:
            message = state["messages"][-1]["content"] if state["messages"] else ""
            user_type = state["user_type"]
            language = state["language"]
            
            prompt = f"""
            Sie sind ein hilfreicher Assistent für die HNU (Hochschule Neu-Ulm) Universität.
            
            Benutzeranfrage: {message}
            Nutzertyp: {user_type}
            Sprache: {language}
            Basisantwort: {base_response}
            
            Bitte verbessern Sie diese Antwort mit zusätzlichen hilfreichen Informationen und halten Sie sie prägnant und relevant.
            Fügen Sie bei Bedarf spezifische Kontaktinformationen oder nächste Schritte hinzu.
            
            Antworten Sie auf {"Deutsch" if language == "de" else "Englisch"}.
            """
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI-Verbesserungsfehler: {e}")
            return None
    
    def _add_interactive_elements(self, state: ConversationState) -> ConversationState:
        """Interaktive Elemente zur Antwort hinzufügen"""
        topic = state["conversation_topic"]
        intent = state["current_intent"]
        depth = state["topic_depth"]
        user_type = state["user_type"]
        
        interactive_options = {"buttons": [], "continue_conversation": False}
        
        # Buttons basierend auf Kontext hinzufügen
        if topic == "bachelor_programs" and depth == 0:
            interactive_options["buttons"] = [
                {"text": "📋 Alle Programme anzeigen", "action": "show_all_programs"},
                {"text": "📝 Bewerbungsinfos", "action": "application_info"},
                {"text": "📞 Zulassung kontaktieren", "action": "contact_info"}
            ]
            interactive_options["continue_conversation"] = True
            
        elif topic == "master_programs" and depth == 0:
            interactive_options["buttons"] = [
                {"text": "📋 Alle Programme anzeigen", "action": "show_all_programs"},
                {"text": "📝 Bewerbungsinfos", "action": "application_info"},
                {"text": "🎓 Voraussetzungen", "action": "prerequisites_info"}
            ]
            interactive_options["continue_conversation"] = True
            
        elif topic in ["employee_services", "student_services"] and depth == 0:
            interactive_options["buttons"] = [
                {"text": "📞 Kontaktinfos", "action": "contact_info"},
                {"text": "💡 Mehr Dienste", "action": "more_details"}
            ]
            
        elif depth > 0:  # Folgegespräch
            interactive_options["buttons"] = [
                {"text": "✅ Thema fortsetzen", "action": "continue_topic"},
                {"text": "🔄 Thema wechseln", "action": "change_topic"}
            ]
        
        # Vorgeschlagene Anfragen generieren
        suggested_queries = self.kb.get_suggested_queries(topic, depth, user_type)
        
        state["interactive_options"] = interactive_options
        state["suggested_queries"] = suggested_queries
        state["workflow_step"] = "interactive_elements_added"
        return state
    
    def _finalize_response(self, state: ConversationState) -> ConversationState:
        """Die Antwort finalisieren"""
        response = state["context"]["generated_response"]
        
        # Antwort zu Nachrichten hinzufügen
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "intent": state["current_intent"],
            "confidence": state["confidence"],
            "topic": state["conversation_topic"],
            "workflow_step": state["workflow_step"]
        })
        
        # Folgeanforderungen setzen
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
        """Eine Nachricht durch den erweiterten Workflow verarbeiten"""
        
        # Initialen Zustand erstellen
        initial_state = ConversationState(
            messages=[{"role": "user", "content": message, "timestamp": datetime.now().isoformat()}],
            user_type=user_type,
            current_intent="",
            confidence=0.0,
            language="de",  # Standard auf Deutsch
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
            # Für sessionbasierte Speicherung konfigurieren
            config = {"configurable": {"thread_id": session_id}}
            
            # Workflow ausführen
            final_state = await self.workflow.ainvoke(initial_state, config=config)
            
            return final_state
            
        except Exception as e:
            print(f"Workflow-Fehler: {e}")
            # Fehlerantwort zurückgeben
            return {
                "messages": [
                    {"role": "user", "content": message, "timestamp": datetime.now().isoformat()},
                    {
                        "role": "assistant", 
                        "content": f"Es tut mir leid, aber ich habe einen Fehler festgestellt: {str(e)}\n\nBitte kontaktieren Sie unser Support-Team unter info@hnu.de für Unterstützung.",
                        "timestamp": datetime.now().isoformat(),
                        "error": True
                    }
                ],
                "interactive_options": {},
                "suggested_queries": ["Support kontaktieren", "Eine andere Frage versuchen"],
                "conversation_topic": "error",
                "current_intent": "error_handling",
                "confidence": 0.0
            }
    
    def get_response(self, message: str, user_type: str = "student", session_id: str = "default") -> str:
        """Synchroner Wrapper für Antworten"""
        try:
            # Die asynchrone Methode ausführen
            result = asyncio.run(self.process_message(message, user_type, session_id))
            
            # Die letzte Assistentennachricht extrahieren
            assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]
            
            if assistant_messages:
                return assistant_messages[-1]["content"]
            else:
                return "Es tut mir leid, ich konnte Ihre Anfrage nicht verarbeiten. Bitte versuchen Sie es erneut oder kontaktieren Sie den Support unter info@hnu.de"
                
        except Exception as e:
            return f"Fehler: {str(e)}\n\nBitte kontaktieren Sie den Support unter info@hnu.de für Unterstützung."

# Testfunktion
def test_chatbot():
    """Den erweiterten Chatbot testen"""
    print("🧪 Erweiterten HNU Chatbot testen...")
    
    chatbot = EnhancedHNUChatbot()
    
    test_queries = [
        "Wie viele Bachelor-Programme gibt es?",
        "Ich brauche IT-Support",
        "Bibliotheksöffnungszeiten",
        "Zeig mir Master-Programme"
    ]
    
    for query in test_queries:
        print(f"❓ Anfrage: {query}")
        response = chatbot.get_response(query, user_type="student")
        print(f"🤖 Antwort: {response[:200]}...")

if __name__ == "__main__":
    test_chatbot()