# HNU Chatbot - Technical Documentation

**Detailed developer documentation for the HNU Chatbot application**

> **📖 Documentation Structure:**
> - **[Main README](../README.md)**: Quick start, features overview, and user guide
> - **This README**: Detailed technical documentation for developers

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Database Schema](#database-schema)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Session Management](#session-management)
7. [Security Implementation](#security-implementation)
8. [API Reference](#api-reference)
9. [Testing Guide](#testing-guide)
10. [Development Workflow](#development-workflow)

---

## Architecture Overview

### High-Level Design

```
┌─────────────┐
│   Streamlit │  UI Layer (app.py, pages/)
│     UI      │
└──────┬──────┘
       │
┌──────▼──────┐
│   Session   │  State Management (session_manager.py)
│  Manager    │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│          Core Business Logic                │
│  ┌─────────────────────────────────────┐   │
│  │  Chatbot (LangGraph Workflow)       │   │
│  │  - analyze_input                    │   │
│  │  - classify_intent                  │   │
│  │  - gather_context                   │   │
│  │  - generate_response (GPT-4o-mini)  │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  Analyzers                          │   │
│  │  - Intent Classifier                │   │
│  │  - Sentiment Analyzer               │   │
│  │  - ChromaDB Query                   │   │
│  └─────────────────────────────────────┘   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│          Data Layer                          │
│  ┌────────────┐  ┌────────────┐             │
│  │  SQLite DB │  │ ChromaDB   │             │
│  │  (Chats &  │  │ (Knowledge │             │
│  │  Analytics)│  │   Base)    │             │
│  └────────────┘  └────────────┘             │
└──────────────────────────────────────────────┘
```

### Key Technologies

- **Frontend**: Streamlit (web interface)
- **Backend Logic**: LangGraph (state-based workflow)
- **Database**: SQLite (chat history, user stats)
- **Vector Search**: ChromaDB + OpenAI embeddings
- **LLM**: OpenAI GPT-4o-mini
- **Intent/Sentiment**: Custom pattern matching + rule-based
- **Language Detection**: langdetect library

---

## Project Structure

```
User_chat/
├── app.py                          # Application entry point
│   ├── restore_session_from_query_params()
│   ├── save_session_to_query_params()
│   └── main() - Application router
│
├── core/                           # Core business logic
│   ├── __init__.py
│   │
│   ├── session_manager.py         # Session state management
│   │   ├── SessionManager.init_session()
│   │   ├── SessionManager.login_user()
│   │   ├── SessionManager.logout_user()
│   │   ├── SessionManager.create_new_session()
│   │   ├── SessionManager.load_session()
│   │   ├── SessionManager.can_access_session()
│   │   ├── SessionManager.get_chat_history()
│   │   └── SessionManager.save_message()
│   │
│   ├── chatbot.py                 # LangGraph chatbot workflow
│   │   ├── HNUChatbot.__init__()
│   │   ├── _build_graph() - LangGraph workflow
│   │   ├── analyze_input() - Language detection
│   │   ├── classify_intent() - Intent & sentiment
│   │   ├── gather_context() - Aggregate all context
│   │   ├── generate_response() - GPT-4o-mini call
│   │   ├── _analyze_tone() - Detect message tone
│   │   ├── _detect_cultural_context() - Cultural awareness
│   │   ├── _analyze_sentiment_trend() - Sentiment progression
│   │   └── process_message() - Main entry point
│   │
│   └── analyzers.py               # Unified analysis interface
│       ├── UnifiedAnalyzer.__init__()
│       └── analyze_message() - Intent + Sentiment + ChromaDB
│
├── database/                       # Database layer
│   ├── __init__.py
│   │
│   ├── auth.py                    # User authentication
│   │   ├── DatabaseAuth.__init__()
│   │   ├── authenticate_student()
│   │   └── authenticate_employee()
│   │
│   ├── chat.py                    # Chat persistence & analytics
│   │   ├── ChatDatabase.__init__()
│   │   ├── create_tables() - Schema creation & migration
│   │   ├── create_session() - New session
│   │   ├── save_message() - Store message with metadata
│   │   ├── get_user_sessions() - Authenticated user history
│   │   ├── get_guest_sessions() - Guest session history
│   │   ├── get_session_messages() - Load conversation
│   │   ├── get_aggregated_session_stats() - Per-session analytics
│   │   ├── find_similar_messages_with_context() - Text similarity
│   │   ├── update_user_stats() - Update analytics cache
│   │   ├── delete_session() - Remove session
│   │   └── update_session_title() - Set session title
│   │
│   └── hnu_support.db             # SQLite database file
│
└── pages/                          # UI pages
    ├── __init__.py
    │
    ├── admin_dashboard.py                   # Dashboard interface for German
    │   ├── get_db_connection()
    │   ├── fetch_all_messages() 
    │   └── process_dashboard_data()
    |   ├── detect_anomalies()           
    │   ├── predict_sentiment_trend()  
    │   └── render_admin_dashboard() 
    |
    ├── admin_dashboard.py                   # Dashboard interface for English
    │   ├── get_db_connection()
    │   ├── fetch_all_messages() 
    │   └── process_dashboard_data()
    |   ├── detect_anomalies()           
    │   ├── predict_sentiment_trend()  
    │   └── render_admin_dashboard()
    |
    ├── login.py                   # Login interface for English
    │   ├── render_login_page()
    │   ├── handle_authenticated_login()
    │   └── handle_guest_login()
    |
    ├── login_de.py                   # Login interface for German
    │   ├── render_login_page()
    │   ├── handle_authenticated_login()
    │   └── handle_guest_login()
    |
    ├── chat.py                   # Chat interface for English
    │   ├── render_chat_page()
    │   ├── render_sidebar()
    |   |── handle_message_submission()
    │   └── display_messages()
    │
    └── chat_de.py                    # Chat interface for German
        ├── render_chat_page()
        ├── render_sidebar()
        ├── handle_message_submission()
        └── display_messages()

```

---

## Database Schema

### Complete Schema with All Columns

#### 1. `chat_sessions` Table

```sql
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,           -- Unique session identifier
    user_id TEXT NOT NULL,                 -- User ID or "guest_student"
    user_type TEXT NOT NULL,               -- "student", "employee", "partner", "admin"
    is_guest BOOLEAN DEFAULT 0,            -- 1 for guests, 0 for authenticated
    title TEXT,                            -- First message preview (first 10 chars)
    user_name TEXT,                        -- Full name (for admin view)
    user_department TEXT,                  -- Course (students) or Department (employees)
    user_degree TEXT,                      -- Degree program (students only)
    guest_session_id TEXT,                 -- Unique per guest visit (for isolation)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_guest_session ON chat_sessions(guest_session_id);
```

**Key Points:**
- `session_id`: Format `session_YYYYMMDD_HHMMSS_random`
- `user_id`: Actual ID for authenticated, "guest_student"/"guest_employee"/"guest_partner" for guests
- `guest_session_id`: Critical for guest isolation (e.g., "guest_a1b2c3d4e5f6")

#### 2. `chat_messages` Table

```sql
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,              -- FK to chat_sessions.session_id
    role TEXT NOT NULL,                    -- "user" or "assistant"
    content TEXT NOT NULL,                 -- Message text
    timestamp TEXT NOT NULL,               -- HH:MM:SS format
    is_suggestion BOOLEAN DEFAULT 0,       -- 1 if from suggestion button
    intent TEXT,                           -- Classified intent (e.g., "enrollment")
    sentiment TEXT,                        -- "positive", "negative", "neutral"
    lead_score INTEGER,                    -- Engagement score 0-100
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);

CREATE INDEX idx_messages_session ON chat_messages(session_id);
```

**Key Points:**
- `intent`, `sentiment`, `lead_score` added in recent update (auto-migrated)
- Only `role='user'` messages have intent/sentiment (assistant messages have NULL)
- `is_suggestion`: Tracks if message came from quick action button

#### 3. `user_stats` Table

```sql
CREATE TABLE IF NOT EXISTS user_stats (
    user_id TEXT PRIMARY KEY,              -- User identifier
    user_type TEXT NOT NULL,               -- "student", "employee", "partner"
    recent_intents TEXT DEFAULT '[]',      -- JSON array of last 10 intents
    recent_sentiments TEXT DEFAULT '[]',   -- JSON array of last 10 sentiments
    recent_scores TEXT DEFAULT '[]',       -- JSON array of last 10 lead scores
    total_chats INTEGER DEFAULT 0,         -- Total message count
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_stats_user ON user_stats(user_id);
```

**Key Points:**
- Caches analytics for quick retrieval
- Arrays stored as JSON strings
- Updated after each message via `update_user_stats()`

#### 4. `students` Table (Authentication)

```sql
CREATE TABLE students (
    id TEXT PRIMARY KEY,                   -- Student ID (e.g., "S001")
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT,
    nationality TEXT,
    course TEXT,                           -- Course name
    degree TEXT,                           -- Degree program
    password TEXT NOT NULL,                -- Plain text (for demo - use hashing in production!)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. `employees` Table (Authentication)

```sql
CREATE TABLE employees (
    id TEXT PRIMARY KEY,                   -- Employee ID (e.g., "E001")
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT,
    nationality TEXT,
    department TEXT NOT NULL,              -- Department (e.g., "HR", "IT")
    password TEXT NOT NULL,                -- Plain text (for demo)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Database Migration

The system auto-migrates on startup (see [database/chat.py:74-90](database/chat.py#L74-L90)):

```python
# Check if new columns exist
cursor.execute("PRAGMA table_info(chat_messages)")
columns = [column[1] for column in cursor.fetchall()]

if 'intent' not in columns:
    cursor.execute('ALTER TABLE chat_messages ADD COLUMN intent TEXT')
if 'sentiment' not in columns:
    cursor.execute('ALTER TABLE chat_messages ADD COLUMN sentiment TEXT')
if 'lead_score' not in columns:
    cursor.execute('ALTER TABLE chat_messages ADD COLUMN lead_score INTEGER')
```

---

## Core Components

### 1. SessionManager ([core/session_manager.py](core/session_manager.py))

**Purpose**: Manage Streamlit session state and database interactions

#### Key Methods

**`init_session()`** - Initialize session state
```python
@staticmethod
def init_session():
    """Initialize all session_state variables"""
    # Authentication
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    # ... more initialization
```

**`login_user(user_data)`** - Set session after login
```python
@staticmethod
def login_user(user_data: Dict):
    """
    Set session state after successful login
    Generates guest_session_id for guests
    """
    st.session_state.authenticated = True
    st.session_state.user_id = user_data['user_id']
    st.session_state.user_name = user_data.get('name', 'User')
    st.session_state.user_type = user_data['user_type']
    st.session_state.is_guest = user_data.get('is_guest', False)

    # Generate unique guest_session_id for guests
    if st.session_state.is_guest:
        import uuid
        st.session_state.guest_session_id = f"guest_{uuid.uuid4().hex[:12]}"
    else:
        st.session_state.guest_session_id = None
```

**`create_new_session()`** - Create new chat session
```python
@staticmethod
def create_new_session():
    """Create new chat session in database"""
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}"

    # Save to database with full context
    db = ChatDatabase()
    db.create_session(
        session_id=session_id,
        user_id=st.session_state.user_id,
        user_type=st.session_state.user_type,
        is_guest=st.session_state.is_guest,
        user_name=st.session_state.user_name,
        user_department=st.session_state.get('user_department'),
        user_degree=st.session_state.get('user_degree'),
        guest_session_id=st.session_state.get('guest_session_id')
    )

    return session_id
```

**`can_access_session(session_id)`** - Security validation
```python
@staticmethod
def can_access_session(session_id: str) -> bool:
    """
    Check if current user can access this session
    Prevents unauthorized access
    """
    db = ChatDatabase()
    session = db.get_session_info(session_id)

    if not session:
        return False

    session_user_id = session['user_id']
    session_is_guest = session['is_guest']
    session_guest_id = session.get('guest_session_id')

    current_is_guest = st.session_state.get('is_guest', False)
    current_user_id = st.session_state.get('user_id')
    current_guest_id = st.session_state.get('guest_session_id')

    # For guests: must match guest_session_id
    if current_is_guest:
        return (session_is_guest == 1 and
                session_guest_id == current_guest_id)

    # For authenticated: must match user_id and not be guest session
    else:
        return (session_user_id == current_user_id and
                session_is_guest == 0)
```

### 2. HNUChatbot ([core/chatbot.py](core/chatbot.py))

**Purpose**: LangGraph workflow for intelligent conversation

#### LangGraph Workflow

```python
def _build_graph(self):
    """Build LangGraph workflow"""
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("analyze_input", self.analyze_input)
    workflow.add_node("classify_intent", self.classify_intent)
    workflow.add_node("detect_topic", self.detect_topic)
    workflow.add_node("gather_context", self.gather_context)
    workflow.add_node("generate_response", self.generate_response)
    workflow.add_node("add_interactive_elements", self.add_interactive_elements)
    workflow.add_node("finalize_response", self.finalize_response)

    # Define edges (workflow sequence)
    workflow.set_entry_point("analyze_input")
    workflow.add_edge("analyze_input", "classify_intent")
    workflow.add_edge("classify_intent", "detect_topic")
    workflow.add_edge("detect_topic", "gather_context")
    workflow.add_edge("gather_context", "generate_response")
    workflow.add_edge("generate_response", "add_interactive_elements")
    workflow.add_edge("add_interactive_elements", "finalize_response")
    workflow.add_edge("finalize_response", END)

    return workflow.compile()
```

#### Key Nodes

**`gather_context(state)`** - Aggregate all context data
```python
def gather_context(self, state: State) -> State:
    """
    Gather all context from:
    1. Session history (last 10 sessions aggregated)
    2. Similar messages (text similarity search)
    3. Knowledge base (ChromaDB vector search)
    """
    user_id = state.get('user_id')
    message = state['user_message']

    # 1. Get aggregated session stats
    session_stats = self.chat_db.get_aggregated_session_stats(user_id, limit_sessions=10)

    # 2. Find similar messages with context (1 before + current + 1 after)
    similar_messages = self.chat_db.find_similar_messages_with_context(
        current_message=message,
        user_id=user_id,
        current_session_id=state.get('session_id'),
        limit=5,
        min_similarity=0.4
    )

    # 3. ChromaDB knowledge base search
    chromadb_results = state.get('faiss_results', [])

    # Format all context for GPT-4o-mini
    context = self._format_context(session_stats, similar_messages, chromadb_results)

    state['context'] = context
    return state
```

**`generate_response(state)`** - GPT-4o-mini call with personalized prompt
```python
def generate_response(self, state: State) -> State:
    """
    Generate response using GPT-4o-mini with:
    - Tone analysis
    - Cultural context
    - Sentiment trend
    - All gathered context
    """
    message = state['user_message']
    intent = state.get('current_intent', 'general_query')
    sentiment = state.get('sentiment', 'neutral')
    language = state.get('language', 'en')
    user_type = state.get('user_type', 'student')

    # Analyze tone, culture, sentiment trend
    message_tone = self._analyze_tone(message, sentiment)
    cultural_context = self._detect_cultural_context(message, language, similar_messages)
    sentiment_trend = self._analyze_sentiment_trend(similar_messages, sentiment)

    # Build personalized system prompt
    system_prompt = f"""You are a warm, empathetic assistant for HNU...

    **Current User Context:**
    - Tone: {message_tone}
    - Sentiment: {sentiment}
    - Cultural Background: {cultural_context}

    **Sentiment Trend:**
    {sentiment_trend}

    **Personalization Guidelines:**
    1. Reference past conversations naturally
    2. Adapt to emotional state
    3. Match communication style
    ...
    """

    # Call GPT-4o-mini
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        max_tokens=300,
        temperature=0.7
    )

    state['assistant_message'] = response.choices[0].message.content
    return state
```

### 3. ChatDatabase ([database/chat.py](database/chat.py))

**Purpose**: All database operations for chat persistence and analytics

#### Critical Methods

**`get_aggregated_session_stats(user_id, limit_sessions)`**
```python
def get_aggregated_session_stats(self, user_id: str, limit_sessions: int = 10) -> Dict[str, Any]:
    """
    Get per-session aggregated statistics for last N sessions

    Returns:
    {
        'total_sessions': 15,
        'session_summaries': [
            {
                'session_id': 'session_xyz',
                'created_at': '2025-10-14 15:30:00',
                'message_count': 12,
                'intents': ['enrollment', 'deadline', 'courses'],  # Unique intents
                'dominant_intent': 'enrollment',  # Most common
                'dominant_sentiment': 'negative',  # Majority
                'avg_lead_score': 45.5
            },
            ...
        ]
    }
    """
    # Get all sessions for user
    sessions = self.get_user_sessions(user_id)

    session_summaries = []
    for session in sessions[:limit_sessions]:
        # Get all messages with intent/sentiment for this session
        messages = self.get_session_messages_with_metadata(session['session_id'])

        # Aggregate
        intents = [m['intent'] for m in messages if m['intent']]
        sentiments = [m['sentiment'] for m in messages if m['sentiment']]
        scores = [m['lead_score'] for m in messages if m['lead_score'] is not None]

        intent_set = list(set(intents))  # Unique intents
        dominant_intent = Counter(intents).most_common(1)[0][0] if intents else 'unknown'
        dominant_sentiment = Counter(sentiments).most_common(1)[0][0] if sentiments else 'neutral'
        avg_score = round(sum(scores) / len(scores), 1) if scores else 50

        session_summaries.append({
            'session_id': session['session_id'],
            'created_at': session['created_at'],
            'message_count': len(messages),
            'intents': intent_set,
            'dominant_intent': dominant_intent,
            'dominant_sentiment': dominant_sentiment,
            'avg_lead_score': avg_score
        })

    return {
        'total_sessions': len(sessions),
        'session_summaries': session_summaries
    }
```

**`find_similar_messages_with_context(current_message, user_id, ...)`**
```python
def find_similar_messages_with_context(
    self,
    current_message: str,
    user_id: str,
    current_session_id: str = None,
    limit: int = 5,
    min_similarity: float = 0.4
) -> List[Dict[str, Any]]:
    """
    Find similar previous messages with context window

    Context pattern: 1 message before + current + 1 message after

    Returns:
    [
        {
            'similarity_score': 0.745,
            'message_before': {
                'content': 'I need help',
                'role': 'user',
                'timestamp': '14:30:15'
            },
            'current_message': {
                'content': 'How do I enroll?',
                'role': 'user',
                'intent': 'enrollment',
                'sentiment': 'neutral',
                'lead_score': 60,
                'timestamp': '14:30:30'
            },
            'message_after': {
                'content': 'Visit the portal...',
                'role': 'assistant',
                'timestamp': '14:30:45'
            },
            'session_id': 'session_abc',
            'created_at': '2025-10-10 14:30:00'
        },
        ...
    ]
    """
    from difflib import SequenceMatcher

    # Get last 200 user messages (exclude current session)
    cursor.execute('''
        SELECT m.id, m.session_id, m.content, m.intent, m.sentiment,
               m.lead_score, m.timestamp, m.created_at
        FROM chat_messages m
        JOIN chat_sessions s ON m.session_id = s.session_id
        WHERE s.user_id = ? AND m.role = 'user'
          AND m.session_id != ?
        ORDER BY m.created_at DESC
        LIMIT 200
    ''', (user_id, current_session_id or ''))

    messages = cursor.fetchall()

    # Calculate similarity for each
    similarities = []
    for msg in messages:
        similarity = SequenceMatcher(None,
                                    current_message.lower(),
                                    msg['content'].lower()).ratio()

        if similarity >= min_similarity:
            similarities.append((similarity, msg))

    # Sort by similarity desc, take top N
    similarities.sort(key=lambda x: x[0], reverse=True)
    top_matches = similarities[:limit]

    # For each match, get context (before + after)
    results = []
    for score, msg in top_matches:
        # Get message before
        before = cursor.execute('''
            SELECT content, role, timestamp FROM chat_messages
            WHERE session_id = ? AND id < ? ORDER BY id DESC LIMIT 1
        ''', (msg['session_id'], msg['id'])).fetchone()

        # Get message after
        after = cursor.execute('''
            SELECT content, role, timestamp FROM chat_messages
            WHERE session_id = ? AND id > ? ORDER BY id ASC LIMIT 1
        ''', (msg['session_id'], msg['id'])).fetchone()

        results.append({
            'similarity_score': score,
            'message_before': before or None,
            'current_message': {
                'content': msg['content'],
                'intent': msg['intent'],
                'sentiment': msg['sentiment'],
                'lead_score': msg['lead_score'],
                'timestamp': msg['timestamp']
            },
            'message_after': after or None,
            'session_id': msg['session_id'],
            'created_at': msg['created_at']
        })

    return results
```

---

## Data Flow

### Complete Message Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER SENDS MESSAGE                                       │
│    - User types in chat input                               │
│    - Streamlit triggers callback                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ 2. SESSION CHECK (pages/chat.py)                            │
│    - If no current_session_id:                              │
│      └─ SessionManager.create_new_session()                 │
│         └─ Generate session_id                              │
│         └─ Save to chat_sessions table                      │
│         └─ Update URL (authenticated only)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ 3. LANGGRAPH WORKFLOW (core/chatbot.py)                     │
│                                                              │
│  Node 1: analyze_input                                      │
│    - Detect language (en/de) using langdetect               │
│    - Set user_type, session_id in state                     │
│                                                              │
│  Node 2: classify_intent                                    │
│    - Call UnifiedAnalyzer.analyze_message()                 │
│      ├─ IntentClassifier: Pattern match with TSV data       │
│      ├─ SentimentAnalyzer: Rule-based + keywords            │
│      └─ ChromaDB: Vector search (OpenAI embeddings)         │
│    - Update state with intent, sentiment, lead_score        │
│                                                              │
│  Node 3: detect_topic                                       │
│    - Map intent to topic category                           │
│                                                              │
│  Node 4: gather_context                                     │
│    - Call get_aggregated_session_stats()                    │
│      └─ Returns last 10 sessions with:                      │
│         • All intents per session                           │
│         • Dominant intent                                   │
│         • Majority sentiment                                │
│         • Average lead score                                │
│    - Call find_similar_messages_with_context()              │
│      └─ Returns top 5 similar messages with:                │
│         • 1 message before                                  │
│         • Current message + metadata                        │
│         • 1 message after                                   │
│    - ChromaDB results already in state                      │
│    - Format all into context string                         │
│                                                              │
│  Node 5: generate_response                                  │
│    - Analyze tone (_analyze_tone)                           │
│    - Detect cultural context (_detect_cultural_context)     │
│    - Analyze sentiment trend (_analyze_sentiment_trend)     │
│    - Build personalized system prompt                       │
│    - Call OpenAI GPT-4o-mini                                │
│      └─ model: gpt-4o-mini                                  │
│      └─ max_tokens: 300                                     │
│      └─ temperature: 0.7                                    │
│                                                              │
│  Node 6: add_interactive_elements                           │
│    - Add suggested questions                                │
│    - Add quick action buttons                               │
│                                                              │
│  Node 7: finalize_response                                  │
│    - Clean up response text                                 │
│    - Return final state                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ 4. SAVE TO DATABASE (pages/chat.py + session_manager.py)    │
│    - Extract intent, sentiment, lead_score from result      │
│    - SessionManager.save_message(                           │
│        role='user',                                          │
│        content=message,                                      │
│        timestamp=HH:MM:SS,                                   │
│        intent=user_intent,                                   │
│        sentiment=user_sentiment,                             │
│        lead_score=user_lead_score                            │
│      )                                                       │
│      └─ ChatDatabase.save_message() - INSERT into           │
│         chat_messages                                        │
│    - SessionManager.save_message(                           │
│        role='assistant',                                     │
│        content=assistant_response                            │
│      )                                                       │
│      └─ ChatDatabase.save_message()                         │
│    - ChatDatabase.update_user_stats()                       │
│      └─ Append to recent_intents/sentiments/scores arrays   │
│      └─ Keep last 10 only                                   │
│    - If first message:                                      │
│      └─ update_session_title(first 10 chars)                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│ 5. UI UPDATE                                                │
│    - Display assistant message                              │
│    - Update chat history in sidebar                         │
│    - Ready for next message                                 │
└─────────────────────────────────────────────────────────────┘
```

### What Gets Saved vs Calculated

**Saved in Database (Persistent):**
- ✅ User message content
- ✅ Assistant response content
- ✅ Intent (user messages only)
- ✅ Sentiment (user messages only)
- ✅ Lead score (user messages only)
- ✅ Timestamp
- ✅ Session metadata (user_id, user_type, is_guest, guest_session_id)
- ✅ User stats cache (last 10 intents/sentiments/scores)

**Calculated on-the-fly (Not Saved):**
- ❌ Session aggregations (dominant intent, majority sentiment)
- ❌ Similar message matches
- ❌ Similarity scores
- ❌ Tone analysis
- ❌ Cultural context
- ❌ Sentiment trends
- ❌ ChromaDB search results
- ❌ GPT-4o-mini responses (saved after generation)

**Why This Design?**
- Saves storage (don't store redundant aggregations)
- Allows dynamic recalculation with different parameters
- Fresh similarity scores on each query
- User stats cache provides quick access to recent patterns

---

## Session Management

### Authentication vs Guest Sessions

#### Authenticated User Flow

```
1. User enters credentials → DatabaseAuth.authenticate_student/employee()
2. SessionManager.login_user(user_data)
   ├─ Sets st.session_state.authenticated = True
   ├─ Sets st.session_state.user_id = actual ID (e.g., "S001")
   ├─ Sets st.session_state.is_guest = False
   └─ Sets st.session_state.guest_session_id = None
3. User redirected to chat page
4. URL updated with ?auth=base64_encoded_data
5. Chat history loaded:
   └─ get_user_sessions(user_id) WHERE is_guest=0
6. User can see all their previous sessions across logins
```

#### Guest User Flow

```
1. User clicks "Continue as Guest"
2. SessionManager.login_user(guest_data)
   ├─ Sets st.session_state.authenticated = True
   ├─ Sets st.session_state.user_id = "guest_student"
   ├─ Sets st.session_state.is_guest = True
   └─ Generates unique guest_session_id = "guest_abc123xyz"
3. User redirected to chat page
4. NO URL params (guests don't persist across visits)
5. Chat history loaded:
   └─ get_guest_sessions(guest_session_id) WHERE guest_session_id='guest_abc123xyz'
6. User ONLY sees chats from THIS visit
```

### Guest Isolation Mechanism

**Problem**: Multiple guests using the same `user_id` ("guest_student")

**Solution**: Each guest visit gets unique `guest_session_id`

**Implementation**:

```python
# On guest login (session_manager.py:50-55)
if user_data.get('is_guest'):
    import uuid
    st.session_state.guest_session_id = f"guest_{uuid.uuid4().hex[:12]}"
else:
    st.session_state.guest_session_id = None

# On session creation (database/chat.py:95-125)
db.create_session(
    session_id=session_id,
    user_id="guest_student",  # Shared
    is_guest=True,
    guest_session_id="guest_abc123xyz"  # Unique!
)

# On history retrieval (database/chat.py:180-195)
if is_guest:
    # Query by guest_session_id, not user_id
    cursor.execute('''
        SELECT * FROM chat_sessions
        WHERE guest_session_id = ? AND is_guest = 1
        ORDER BY created_at DESC
    ''', (guest_session_id,))
else:
    # Query by user_id
    cursor.execute('''
        SELECT * FROM chat_sessions
        WHERE user_id = ? AND is_guest = 0
        ORDER BY created_at DESC
    ''', (user_id,))
```

**Result**: Guest A and Guest B are completely isolated despite sharing `user_id`.

---

## Security Implementation

### Session Ownership Validation

Every `load_session()` and `delete_session()` call validates ownership:

```python
@staticmethod
def can_access_session(session_id: str) -> bool:
    """
    Security check: Can current user access this session?

    Blocks:
    - Guest A accessing Guest B's session
    - Student S001 accessing Student S002's session
    - Guest accessing authenticated session
    - Authenticated user accessing guest session
    """
    db = ChatDatabase()
    session = db.get_session_info(session_id)

    if not session:
        return False

    # Extract session ownership data
    session_user_id = session['user_id']
    session_is_guest = session['is_guest']
    session_guest_id = session.get('guest_session_id')

    # Extract current user data
    current_is_guest = st.session_state.get('is_guest', False)
    current_user_id = st.session_state.get('user_id')
    current_guest_id = st.session_state.get('guest_session_id')

    # Validation logic
    if current_is_guest:
        # Guest: must match guest_session_id exactly
        return (session_is_guest == 1 and
                session_guest_id == current_guest_id)
    else:
        # Authenticated: must match user_id and not be guest session
        return (session_user_id == current_user_id and
                session_is_guest == 0)
```

### Attack Scenarios Blocked

| Attack | Protection |
|--------|------------|
| Guest A tries to load Guest B's session | `guest_session_id` mismatch → blocked |
| Student S001 tries to load S002's session | `user_id` mismatch → blocked |
| Guest tries to load authenticated session | `is_guest` mismatch → blocked |
| Authenticated tries to load guest session | `is_guest` mismatch → blocked |
| Manual URL manipulation | No `guest_session_id` in URL, generated fresh each visit |
| Session hijacking | URL params only for authenticated, validated on restore |

### URL-Based Session Persistence

**Authenticated Users Only**:

```python
def save_session_to_query_params():
    """Save auth and session to URL for authenticated users"""
    if st.session_state.get('is_guest'):
        return  # Guests don't get URL persistence

    # Encode user data
    user_data = {
        'user_id': st.session_state.user_id,
        'user_name': st.session_state.user_name,
        'user_type': st.session_state.user_type,
        # ... more fields
    }

    token = base64.b64encode(json.dumps(user_data).encode()).decode()

    st.query_params['auth'] = token
    st.query_params['session'] = st.session_state.current_session_id
```

**Restoration**:

```python
def restore_session_from_query_params():
    """Restore session from URL params"""
    if 'auth' in st.query_params:
        token = st.query_params['auth']
        user_data = json.loads(base64.b64decode(token))

        # Restore authentication
        SessionManager.login_user(user_data)

        # Restore session (with ownership validation)
        if 'session' in st.query_params:
            session_id = st.query_params['session']
            if SessionManager.can_access_session(session_id):
                SessionManager.load_session(session_id)
```

---

## API Reference

### SessionManager Static Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `init_session()` | None | None | Initialize all session_state variables |
| `login_user(user_data)` | dict | None | Set session after login, generate guest_session_id |
| `logout_user()` | None | None | Clear all session state |
| `create_new_session()` | None | str | Create new session in DB, return session_id |
| `load_session(session_id)` | str | None | Load session with ownership check |
| `can_access_session(session_id)` | str | bool | Validate session ownership |
| `get_chat_history()` | None | list | Get user/guest-specific sessions |
| `save_message(role, content, ...)` | str, str, ... | None | Save message to DB with metadata |

### ChatDatabase Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `create_session(session_id, ...)` | str, ... | bool | Insert new session |
| `save_message(session_id, role, content, ...)` | str, str, str, ... | bool | Insert message with intent/sentiment |
| `get_user_sessions(user_id, user_type)` | str, str | list | Get authenticated user sessions |
| `get_guest_sessions(guest_session_id)` | str | list | Get guest sessions |
| `get_session_messages(session_id)` | str | list | Load conversation |
| `get_aggregated_session_stats(user_id, limit)` | str, int | dict | Per-session analytics |
| `find_similar_messages_with_context(...)` | str, str, ... | list | Text similarity search |
| `update_user_stats(user_id, ...)` | str, ... | bool | Update analytics cache |
| `delete_session(session_id)` | str | bool | Remove session and messages |
| `update_session_title(session_id, title)` | str, str | bool | Set session title |

### HNUChatbot Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `process_message(message, ...)` | str, ... | dict | Main entry point, returns response |
| `analyze_input(state)` | State | State | Detect language |
| `classify_intent(state)` | State | State | Intent & sentiment analysis |
| `gather_context(state)` | State | State | Aggregate all context |
| `generate_response(state)` | State | State | GPT-4o-mini call |
| `_analyze_tone(message, sentiment)` | str, str | str | Detect message tone |
| `_detect_cultural_context(...)` | str, str, list | str | Cultural awareness |
| `_analyze_sentiment_trend(...)` | list, str | str | Sentiment progression |

---

## Testing Guide

### Test Scenario 1: Guest Isolation

**Objective**: Verify guests cannot see each other's chats

```
1. Open Browser A (Incognito)
   - Navigate to http://localhost:8501
   - Click "Continue as Guest" (Student)
   - Send message: "Hello from Guest A"
   - Check sidebar: Should show 1 chat

2. Open Browser B (Different Incognito)
   - Navigate to http://localhost:8501
   - Click "Continue as Guest" (Student)
   - Check sidebar: Should be EMPTY
   - Send message: "Hello from Guest B"
   - Check sidebar: Should show only 1 chat (Guest B's)

3. Database Verification:
   SELECT session_id, user_id, guest_session_id, title
   FROM chat_sessions
   WHERE is_guest = 1
   ORDER BY created_at DESC
   LIMIT 2;

   Expected:
   - 2 different session_ids
   - Both user_id = "guest_student"
   - 2 different guest_session_ids
```

### Test Scenario 2: Authenticated Persistence

**Objective**: Verify session restoration across logins

```
1. Login as Student S001
   - Create new chat
   - Send messages
   - Copy URL (contains ?auth=xxx&session=yyy)
   - Logout

2. Login as Student S001 again
   - Sidebar should show previous chat
   - Click chat → messages load correctly

3. Paste copied URL
   - Should restore exact session
   - All messages visible

4. Database Verification:
   SELECT * FROM chat_sessions
   WHERE user_id = 'S001' AND is_guest = 0;

   Expected:
   - All sessions visible
   - guest_session_id = NULL
```

### Test Scenario 3: Intent & Sentiment Persistence

**Objective**: Verify metadata saves correctly

```
1. Login as Student
2. Send message: "I'm frustrated with enrollment"
3. Database Check:
   SELECT role, content, intent, sentiment, lead_score
   FROM chat_messages
   WHERE session_id = 'current_session_id';

   Expected:
   - role='user': intent='enrollment', sentiment='negative', lead_score < 50
   - role='assistant': intent=NULL, sentiment=NULL, lead_score=NULL

4. Send another message
5. Check user_stats:
   SELECT recent_intents, recent_sentiments, recent_scores
   FROM user_stats
   WHERE user_id = 'S001';

   Expected:
   - Arrays updated with new data
   - Length ≤ 10
```

### Test Scenario 4: Similar Message Search

**Objective**: Verify text similarity works

```
1. Login as Student S001
2. Create Session 1:
   - Message: "How do I enroll for summer semester?"
   - Wait for response

3. Create Session 2 (new chat):
   - Message: "I want to enroll in the summer term"
   - Check logs or breakpoint in chatbot.py:gather_context()

   Expected:
   - find_similar_messages_with_context() returns ≥1 result
   - Top result has similarity ≥ 40%
   - Context includes message before & after
```

### Test Scenario 5: Session Ownership Validation

**Objective**: Verify security blocks unauthorized access

```
1. Login as Student S001
   - Create session_abc
   - Logout

2. Login as Student S002
   - Try to manually load S001's session:
     st.session_state.current_session_id = 'session_abc'
     SessionManager.load_session('session_abc')

   Expected:
   - can_access_session() returns False
   - Session not loaded
   - No messages visible

3. Database Check:
   SELECT user_id FROM chat_sessions WHERE session_id = 'session_abc';

   Result: user_id = 'S001' (not 'S002')
```

---

## Development Workflow

### Adding a New Feature

1. **Plan**:
   - Update database schema if needed (add columns)
   - Add migration code in `create_tables()`
   - Design API methods

2. **Implement**:
   - Add database methods in `database/chat.py`
   - Update business logic in `core/chatbot.py` or `core/analyzers.py`
   - Modify UI in `pages/chat.py` if needed

3. **Test**:
   - Write test scenarios (see Testing Guide)
   - Verify database changes
   - Check for security implications

4. **Document**:
   - Update this README
   - Add code comments
   - Update main README if user-facing

### Debugging Tips

**Enable Detailed Logging**:

```python
# In chatbot.py:generate_response()
import logging
file_logger = logging.getLogger('openai_data_flow')
file_logger.setLevel(logging.INFO)
handler = logging.FileHandler('openai_data_flow.log')
file_logger.addHandler(handler)
```

**Check Database State**:

```bash
sqlite3 database/hnu_support.db
.tables
.schema chat_sessions
SELECT * FROM chat_sessions WHERE user_id = 'S001';
.quit
```

**Inspect Streamlit Session State**:

```python
# Add to any page
st.write("Session State:", st.session_state)
```

**Verify ChromaDB Collection**:

```python
import chromadb
client = chromadb.PersistentClient(path="../data/chromadb")
collection = client.get_collection("hnu_knowledge_base")
print(f"Total docs: {collection.count()}")
```

---

## Advanced Topics

### Customizing Personalization

**Adjust Tone Detection** ([chatbot.py:1300-1316](core/chatbot.py#L1300-L1316)):

```python
def _analyze_tone(self, message: str, sentiment: str) -> str:
    """Add more tone categories"""
    message_lower = message.lower()

    # Add custom markers
    if 'excited' in message_lower or '!' in message:
        return "Excited/Enthusiastic"

    # Modify existing logic
    # ...
```

**Modify Cultural Context** ([chatbot.py:1318-1361](core/chatbot.py#L1318-L1361)):

```python
def _detect_cultural_context(self, message: str, language: str, similar_messages: List) -> str:
    """Add more cultural patterns"""
    # Add detection for specific regions
    if 'servus' in message.lower():
        return "Bavarian German (Very casual)"
    # ...
```

### Scaling Considerations

**For 10,000+ Users**:

1. **Database**:
   - Migrate to PostgreSQL
   - Add connection pooling
   - Implement archival for old sessions

2. **ChromaDB**:
   - Use hosted Chroma server
   - Add caching layer (Redis)
   - Batch embedding generation

3. **Session Management**:
   - Use Redis for session state
   - Implement distributed sessions
   - Add load balancing

4. **Analytics**:
   - Move to time-series database (InfluxDB)
   - Implement real-time dashboards
   - Add alerting for anomalies

---

## Troubleshooting

See main README for common issues. Additional developer-specific issues:

### LangGraph State Errors

**Issue**: `KeyError` in workflow nodes

**Solution**:
- Check State type definition includes all required keys
- Verify each node returns updated state
- Use `.get()` instead of direct key access for optional fields

### ChromaDB Collection Not Found

**Issue**: `chromadb.errors.InvalidCollectionException`

**Solution**:
```bash
cd ../models
python generate_chromadb_kb.py
```

### Database Lock Errors

**Issue**: `sqlite3.OperationalError: database is locked`

**Solution**:
- SQLite doesn't handle concurrent writes well
- Add `timeout` parameter: `sqlite3.connect(db_path, timeout=10.0)`
- Consider PostgreSQL for production

---

## Contributing

### Code Style

- Use type hints for all functions
- Add docstrings (Google style)
- Keep functions < 50 lines
- Use descriptive variable names
- Add comments for complex logic

### Pull Request Process

1. Create feature branch
2. Implement changes
3. Write tests
4. Update documentation
5. Submit PR with description

---

## Additional Resources

- **[Main README](../README.md)**: User guide & quick start
- **Streamlit Docs**: https://docs.streamlit.io
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **ChromaDB Docs**: https://docs.trychroma.com
- **OpenAI API Docs**: https://platform.openai.com/docs

---

**Last Updated**: Decemeber 25, 2025
**Version**: 2.0.0
**Author**: HNU Development Team- Nishtha
