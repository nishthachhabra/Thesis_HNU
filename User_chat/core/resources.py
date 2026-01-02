"""
COMPLETE HNU Resource Management System
Comprehensive database of all HNU departments, services, and contacts
Last Updated: October 2025
"""

# ========================= RESOURCE DATABASE =========================
RESOURCE_DATABASE = {
    # ========== ACADEMIC DEPARTMENTS ==========
    "business_economics": {
        "keywords": ["business", "economics", "bwl", "business studies", "department"],
        "resources": [
            {
                "title": "Department of Business and Economics",
                "url": "https://www.hnu.de/en/university/departments/business-and-economics",
                "contact_person": "Dean of Department",
                "email": "business@hnu.de",
                "phone": "+49 731 9762-0",
                "language": ["en", "de"]
            }
        ]
    },
    "information_management": {
        "keywords": ["information management", "im", "it", "computer science", "digital"],
        "resources": [
            {
                "title": "Department of Information Management",
                "url": "https://www.hnu.de/en/university/departments/information-management",
                "contact_person": "Dean of Department",
                "email": "im@hnu.de",
                "phone": "+49 731 9762-0",
                "language": ["en", "de"]
            }
        ]
    },
    "health_management": {
        "keywords": ["health management", "healthcare", "health", "medical", "nursing"],
        "resources": [
            {
                "title": "Department of Health Management",
                "url": "https://www.hnu.de/en/university/departments/health-management",
                "contact_person": "Dean of Studies: Prof. Sandra Krammer",
                "email": "health@hnu.de",
                "phone": "+49 731 9762-0",
                "language": ["en", "de"]
            }
        ]
    },
    "postgraduate_studies": {
        "keywords": ["postgraduate", "professional studies", "executive", "mba", "continuing education"],
        "resources": [
            {
                "title": "Centre for Professional and Postgraduate Studies",
                "url": "https://www.hnu.de/en/university/departments/centre-for-professional-and-postgraduate-studies",
                "contact_person": "Strategic Head: Prof. Sylvia Schafmeister",
                "email": "postgraduate@hnu.de",
                "phone": "+49 731 9762-0",
                "language": ["en", "de"]
            }
        ]
    },

    # ========== STUDENT SERVICES & ADMISSIONS ==========
    "admissions": {
        "keywords": ["admission", "application", "enroll", "registration", "bewerbung", "anmeldung"],
        "resources": [
            {
                "title": "Admissions Office - HNU",
                "url": "https://www.hnu.de/en/study/application",
                "contact_person": "Admissions Team",
                "email": "admissions@hnu.de",
                "phone": "+49 731 9762-0",
                "language": ["en", "de"]
            },
            {
                "title": "Campus Portal - Student Registration",
                "url": "https://campus.hnu.de/qisserver/pages/cs/sys/portal/hisinoneStartPage.faces",
                "contact_person": "IT Support",
                "email": "itsupport@hnu.de",
                "language": ["en", "de"]
            }
        ]
    },
    "international_office": {
    "keywords": ["international", "exchange", "abroad", "incoming", "outgoing", "erasmus"],
    "resources": [
        {
            "title": "International Office - HNU",
            "url": "https://www.hnu.de/en/international",
            "contact_person": "International Office Team",
            "email": "international@hnu.de",
            "phone": "+49 731 9762-2121",
            "room": "Main Building",
            "language": ["en", "de"]
        },
        {
            "title": "Student Exchange Outgoing",
            "url": "https://www.hnu.de/en/international/team-contact",
            "contact_person": "International Office",
            "email": "international@hnu.de",
            "phone": "+49 731 9762-2121",
            "language": ["en", "de"]
        }
    ]
},
"accommodation": {
    "keywords": ["housing", "accommodation", "dorm", "apartment", "wohnen", "studentenwohnheim"],
    "resources": [
        {
            "title": "Student Residences - Studentenwerk Augsburg",
            "url": "https://www.studentenwerk-augsburg.de/en/housing",
            "contact_person": "Studentenwerk Augsburg",
            "email": "wohnen@studentenwerk-augsburg.de",
            "phone": "+49 821 4558-0",
            "language": ["en", "de"]
        },
        {
            "title": "Accommodation Information for International Students",
            "url": "https://www.hnu.de/en/international/international-degree-seeking-students/faq",
            "contact_person": "International Office",
            "email": "incoming@hnu.de",
            "phone": "+49 731 9762-2121",
            "language": ["en"]
        }
    ]
},
"canteen_food": {
    "keywords": ["canteen", "mensa", "cafeteria", "food", "dining", "essen"],
    "resources": [
        {
            "title": "HNU Canteen - Studentenwerk Augsburg",
            "url": "https://www.studentenwerk-augsburg.de/en/catering",
            "contact_person": "Studentenwerk Augsburg",
            "email": "mensa@studentenwerk-augsburg.de",
            "phone": "+49 821 4558-0",
            "language": ["en", "de"]
        }
    ]
},

# ========== STUDENT SUPPORT & COUNSELING ==========
"student_counseling": {
    "keywords": ["counseling", "psychology", "mental health", "beratung", "psychologisch"],
    "resources": [
        {
            "title": "Psychosocial Counseling Service - Studentenwerk Ulm",
            "url": "https://www.studentenwerk-ulm.de/en",
            "contact_person": "Counseling Team",
            "email": "beratung@studentenwerk-ulm.de",
            "phone": "+49 731 50-24000",
            "language": ["en", "de"]
        }
    ]
},
"study_counselor": {
    "keywords": ["study", "advisor", "guidance", "studienfachberatung", "studienberatung"],
    "resources": [
        {
            "title": "Study Counseling - HNU",
            "url": "https://www.hnu.de/en/study/study-counselling",
            "contact_person": "Study Advisors per Department",
            "email": "study@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},
"social_legal_services": {
    "keywords": ["legal", "social", "law", "insurance", "sozial", "rechtliche"],
    "resources": [
        {
            "title": "Social and Legal Counseling - Studentenwerk Ulm",
            "url": "https://www.studentenwerk-ulm.de/en/counseling",
            "contact_person": "Legal Advisor",
            "email": "soziales@studentenwerk-ulm.de",
            "phone": "+49 731 50-24100",
            "language": ["en", "de"]
        }
    ]
},

# ========== CAREER & EMPLOYMENT ==========
"career_services": {
    "keywords": ["career", "job", "employment", "internship", "career service", "praktikum", "stelle"],
    "resources": [
        {
            "title": "Career Service & Alumni Network",
            "url": "https://www.hnu.de/en/career",
            "contact_person": "Career Service Team",
            "email": "career@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        },
        {
            "title": "Alumni & CampusClub - HNU",
            "url": "https://www.hnu.de/en/alumni",
            "contact_person": "Alumni Office",
            "email": "alumni@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},
"welcome_center": {
    "keywords": ["welcome", "welcome center", "job placement", "employment"],
    "resources": [
        {
            "title": "Welcome Center Ulm/Oberschwaben",
            "url": "https://www.welcome-center-ulm.de/",
            "contact_person": "Welcome Center Team",
            "email": "info@welcome-center-ulm.de",
            "language": ["en", "de"]
        },
        {
            "title": "Welcome Center Ostwürttemberg",
            "url": "https://www.welcome-center-ostwuerttemberg.de/",
            "contact_person": "Welcome Center Team",
            "language": ["de"]
        }
    ]
},

# ========== ACADEMIC SUPPORT ==========
"library": {
    "keywords": ["library", "book", "research", "literature", "media", "bibliothek"],
    "resources": [
        {
            "title": "HNU Library Services",
            "url": "https://www.hnu.de/en/university/campus-and-facilities/library",
            "contact_person": "Library Staff",
            "email": "library@hnu.de",
            "phone": "+49 731 9762-4500",
            "language": ["en", "de"]
        }
    ]
},
"it_support": {
    "keywords": ["it", "technical", "computer", "wifi", "network", "it-support", "edv"],
    "resources": [
        {
            "title": "IT Support Desk - HNU",
            "url": "https://www.hnu.de/en/university/campus-and-facilities/it",
            "contact_person": "IT Help Desk",
            "email": "itsupport@hnu.de",
            "phone": "+49 731 9762-0",
            "room": "IT Service Centre",
            "language": ["en", "de"]
        }
    ]
},
"writing_center": {
    "keywords": ["writing", "thesis", "academic writing", "essay", "paper", "schreiben"],
    "resources": [
        {
            "title": "Study Support & Writing Assistance",
            "url": "https://www.hnu.de/en/study/study-counselling",
            "contact_person": "Study Advisors",
            "email": "study@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},

# ========== COURSES & CURRICULUM ==========
"courses": {
    "keywords": ["course", "class", "lecture", "module", "curriculum", "kurs", "vorlesung"],
    "resources": [
        {
            "title": "Course Catalog - HNU",
            "url": "https://www.hnu.de/en/study/programmes",
            "contact_person": "Academic Affairs",
            "email": "academic@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},
"aida": {
    "keywords": ["aida", "course management", "platform", "elearning", "online"],
    "resources": [
        {
            "title": "AIDA Learning Platform",
            "url": "https://aida.hnu.de",
            "contact_person": "E-Learning Support",
            "email": "elearning@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},

# ========== RESEARCH & INNOVATION ==========
"technology_transfer": {
    "keywords": ["technology transfer", "research", "innovation", "startup", "entrepreneurship"],
    "resources": [
        {
            "title": "Technology Transfer Centre (TTZ)",
            "url": "https://www.hnu.de/en/research/technology-transfer",
            "contact_person": "TTZ Director",
            "email": "transfer@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},
"founders_space": {
    "keywords": ["founders", "entrepreneurship", "startup", "incubator", "business idea"],
    "resources": [
        {
            "title": "Founders' Space - HNU",
            "url": "https://www.hnu.de/en/research/innovation/founders-space",
            "contact_person": "Innovation Team",
            "email": "founders@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},

# ========== HEALTH & WELLNESS ==========
"health_wellness": {
    "keywords": ["health", "medical", "wellness", "sports", "fitness", "gesundheit"],
    "resources": [
        {
            "title": "Student Health & Wellness",
            "url": "https://www.studentenwerk-ulm.de/en/counseling",
            "contact_person": "Wellness Coordinator",
            "email": "health@studentenwerk-ulm.de",
            "phone": "+49 731 50-24600",
            "language": ["en", "de"]
        }
    ]
},
"sports": {
    "keywords": ["sports", "exercise", "fitness", "aerobics", "basketball", "sport"],
    "resources": [
        {
            "title": "University of Ulm Sports Centre - Available to HNU Students",
            "url": "https://www.uni-ulm.de/en/university/structure/sport-facilities/",
            "contact_person": "Sports Centre Management",
            "phone": "+49 731 50-22121",
            "language": ["en", "de"]
        }
    ]
},
"health_insurance": {
    "keywords": ["insurance", "health insurance", "krankenkasse", "versicherung"],
    "resources": [
        {
            "title": "Student Health Insurance Information",
            "url": "https://www.hnu.de/en/international/international-degree-seeking-students/faq",
            "contact_person": "International Office",
            "email": "incoming@hnu.de",
            "phone": "+49 731 9762-2121",
            "language": ["en", "de"]
        }
    ]
},

# ========== STUDENT LIFE & ACTIVITIES ==========
"student_union": {
    "keywords": ["student union", "asta", "students", "activity", "event", "studentische"],
    "resources": [
        {
            "title": "Students' Union & Student Life",
            "url": "https://www.hnu.de/en/university/campus-and-facilities/student-life",
            "contact_person": "Student Union",
            "email": "studentenvertretung@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},
"clubs_organizations": {
    "keywords": ["club", "organization", "group", "association", "verein"],
    "resources": [
        {
            "title": "Student Clubs & Organizations",
            "url": "https://www.hnu.de/en/university/campus-and-facilities/student-life",
            "contact_person": "Student Services",
            "email": "studentenvertretung@hnu.de",
            "phone": "+49 731 9762-0",
            "language": ["en", "de"]
        }
    ]
},

# ========== GENERAL INFORMATION ==========
"general_contact": {
    "keywords": ["contact", "info", "information", "help", "support"],
    "resources": [
        {
            "title": "HNU Main Campus",
            "url": "https://www.hnu.de/en/university",
            "contact_person": "HNU Switchboard",
            "email": "info@hnu.de",
            "phone": "+49 731 9762-0",
            "address": "Wileystraße 1, 89231 Neu-Ulm, Germany",
            "hours": "Mo-Th: 8:00-16:00, Fr: 8:00-14:00",
            "language": ["en", "de"]
        }
    ]
},
"voehlinchloss": {
    "keywords": ["vöhlinschloss", "castle", "seminar", "event", "conference"],
    "resources": [
        {
            "title": "Vöhlinschloss - University Seminar Centre",
            "url": "https://www.hochschulschloss.de/en",
            "contact_person": "Vöhlinschloss Management",
            "email": "info@hochschulschloss.de",
            "phone": "+49 8335 96-0",
            "language": ["en", "de"]
        }
    ]
}
}

# ========================= FUNCTIONS =========================

def find_relevant_resources(user_query: str):
    """Match user query to relevant resources"""
    user_query_lower = user_query.lower()
    matched_resources = []
    matched_categories = set()

    for category, data in RESOURCE_DATABASE.items():
        if category in matched_categories:
            continue

        for keyword in data["keywords"]:
            if keyword in user_query_lower:
                matched_resources.extend(data["resources"])
                matched_categories.add(category)
                break

    return matched_resources


def format_resources_for_response(resources, max_resources=3, language="en"):
    """Format resources into readable markdown"""
    if not resources:
        return ""

    filtered_resources = [r for r in resources if language in r.get("language", ["en", "de"])]
    filtered_resources = filtered_resources[:max_resources]

    if not filtered_resources:
        return ""

    header = "📚 Helpful Resources & Contacts:" if language == "en" else "📚 Hilfreiche Ressourcen & Kontakte:"
    formatted = f"\n\n**{header}**\n"

    for i, resource in enumerate(filtered_resources, 1):
        formatted += f"\n{i}. **{resource.get('title', 'Resource')}**"

        if resource.get('url'):
            formatted += f"\n   🔗 {resource['url']}"

        if resource.get('contact_person'):
            formatted += f"\n   👤 {resource['contact_person']}"

        if resource.get('email'):
            formatted += f"\n   ✉️ {resource['email']}"

        if resource.get('phone'):
            formatted += f"\n   📞 {resource['phone']}"

        if resource.get('room'):
            formatted += f"\n   🏢 {resource['room']}"

        if resource.get('address'):
            formatted += f"\n   📍 {resource['address']}"

        if resource.get('hours'):
            formatted += f"\n   ⏰ {resource['hours']}"

    return formatted


# ========================= EXAMPLE USAGE =========================
if __name__ == "__main__":
    test_queries = [
        "who is responsible for aida course",
        "I need accommodation help",
        "tell me about career services",
        "I have health issues",
        "IT problems with wifi"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        resources = find_relevant_resources(query)
        formatted = format_resources_for_response(resources, language="en")
        print(formatted if formatted else "No specific resources found.")
