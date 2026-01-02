# HNU Support Chat Application

A production-ready AI-powered chat application built with Streamlit, featuring secure session management, SQLite persistence, and guest user isolation.

## Table of Contents
- [Project Structure](#project-structure)
- [Database Architecture](#database-architecture)
- [Session Management](#session-management)
- [Security Features](#security-features)
- [Quick Start](#quick-start)
- [User Types](#user-types)
- [Technical Workflow](#technical-workflow)

---

## Project Structure

```
User_chat/
├── app.py                          # Main application entry point
├── README.md                       # This file
│
├── core/                           # Core business logic
│   ├── __init__.py
│   ├── session_manager.py         # Session & state management
│   └── chatbot.py                 # AI chatbot (LangGraph)
│
├── database/                       # Database layer
│   ├── __init__.py
│   ├── auth.py                    # User authentication
│   ├── chat.py                    # Chat persistence
│   └── hnu_users.db               # SQLite database file
│
├── pages/                          # UI pages
│   ├── __init__.py
│   ├── login.py                   # Login page
│   └── chat.py                    # Chat interface
│
└── archive/                        # Old/deprecated files
    ├── streamlit_up1.py
    └── session_manager_old.py
```

---

## Database Architecture

### Database File
**Location**: `database/hnu_users.db`
**Type**: SQLite3

### Tables

#### 1. **students** (Authentication)
```sql
CREATE TABLE students (
    id TEXT PRIMARY KEY,              -- Student ID (e.g., "S001")
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT,
    nationality TEXT,
    course TEXT,                      -- Course name
    degree TEXT,                      -- Degree program
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. **employees** (Authentication)
```sql
CREATE TABLE employees (
    id TEXT PRIMARY KEY,              -- Employee ID (e.g., "E001")
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    gender TEXT,
    nationality TEXT,
    department TEXT NOT NULL,         -- Department (e.g., "HR", "IT")
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. **chat_sessions** (Chat History)
```sql
CREATE TABLE chat_sessions (
    session_id TEXT PRIMARY KEY,      -- Unique session ID
    user_id TEXT NOT NULL,            -- "S001" OR "guest_student"
    user_type TEXT NOT NULL,          -- "student", "employee", "partner", "admin"
    is_guest BOOLEAN DEFAULT 0,       -- 1 for guests, 0 for authenticated
    title TEXT,                       -- First 10 chars of first message
    user_name TEXT,                   -- Full name for admin view
    user_department TEXT,             -- Course/Department
    user_degree TEXT,                 -- Degree (students only)
    guest_session_id TEXT,            -- Unique per guest visit (isolation)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
- `idx_sessions_user` on `(user_id)`
- `idx_guest_session` on `(guest_session_id)`

#### 4. **chat_messages** (Chat Content)
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,         -- FK to chat_sessions
    role TEXT NOT NULL,               -- "user" or "assistant"
    content TEXT NOT NULL,            -- Message text
    timestamp TEXT NOT NULL,          -- HH:MM:SS
    is_suggestion BOOLEAN DEFAULT 0,  -- 1 if from suggestion button
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);
```

**Indexes**:
- `idx_messages_session` on `(session_id)`

---

## Session Management

### Key Concepts

#### 1. **Authenticated Users**
- Login with credentials from `students` or `employees` table
- Sessions persist across logins
- URL-based session restoration (`?auth=xxx&session=yyy`)
- Can see all their previous chats

#### 2. **Guest Users**
- No authentication required
- Each visit gets unique `guest_session_id`
- **Complete isolation**: Cannot see other guests' chats
- **No URL persistence**: Fresh start each visit
- Chats saved in database for admin review

### Session State Variables

```python
# Authentication
st.session_state.authenticated      # bool
st.session_state.user_id            # "S001" or "guest_student"
st.session_state.user_name          # "John Doe"
st.session_state.user_type          # "student", "employee", "partner", "admin"
st.session_state.user_department    # Course or department
st.session_state.user_degree        # Degree (students only)
st.session_state.is_guest           # bool
st.session_state.is_hr              # bool (admin only)
st.session_state.guest_session_id   # "guest_abc123xyz" (guests only)

# Chat
st.session_state.messages           # Current chat messages
st.session_state.current_session_id # Active session ID
st.session_state.chatbot            # AI chatbot instance
st.session_state.chat_db            # Database instance
```

### Session Flow

**Authenticated User Login**:
```
1. User enters credentials → database/auth.py validates
2. SessionManager.login_user() sets session_state
3. guest_session_id = None (not a guest)
4. User redirected to chat page
5. URL updated with ?auth=xxx
6. Chat history loads from database (user_id + is_guest=0)
```

**Guest User Login**:
```
1. User clicks "Continue as Guest"
2. SessionManager.login_user() sets session_state
3. guest_session_id = "guest_{uuid}" (unique per visit)
4. User redirected to chat page
5. NO URL params (guests don't persist)
6. Chat history loads from database (guest_session_id match)
```

**New Chat Session Creation**:
```
1. User sends first message
2. SessionManager.create_new_session() generates session_id
3. Database row created in chat_sessions with:
   - session_id = "session_20251014_123456_789"
   - user_id = actual ID or "guest_student"
   - is_guest = 1 (guest) or 0 (authenticated)
   - guest_session_id = unique ID (guests only)
   - title = first 10 chars of message
4. Each message saved to chat_messages table
5. URL updated with ?session=xxx (authenticated users only)
```

---

## Security Features

### 1. **Guest Isolation**
Each guest visit generates a unique `guest_session_id` (UUID-based):
```python
guest_session_id = f"guest_{uuid.uuid4().hex[:12]}"
# Example: "guest_a1b2c3d4e5f6"
```

**Database Query for Guest**:
```sql
SELECT * FROM chat_sessions
WHERE guest_session_id = 'guest_a1b2c3d4e5f6' AND is_guest = 1
```

Result: Guest A only sees their own chats. Guest B (with different `guest_session_id`) sees completely different chats.

### 2. **Session Ownership Validation**
Every `load_session()` and `delete_session()` call validates ownership:

```python
def can_access_session(session_id):
    # Get session from database
    session_user_id, session_is_guest, session_guest_id = ...

    # For guests: must match guest_session_id
    if current_is_guest:
        return (session_is_guest == 1 and
                session_guest_id == current_guest_session_id)

    # For authenticated: must match user_id
    else:
        return (session_user_id == current_user_id and
                session_is_guest == 0)
```

**Attack Scenarios Blocked**:
- ❌ Guest A cannot access Guest B's session
- ❌ Student S001 cannot access Student S002's session
- ❌ Guest cannot access authenticated user's session
- ❌ Authenticated user cannot access guest session
- ❌ User cannot delete another user's session

### 3. **URL-Based Persistence (Authenticated Only)**
```python
# app.py - save_session_to_query_params()
if st.session_state.get('is_guest'):
    return  # Guests don't get URL params

# Encode user data in URL
user_data = {user_id, user_name, user_type, ...}
token = base64.encode(json.dumps(user_data))
st.query_params['auth'] = token
st.query_params['session'] = current_session_id
```

Guests cannot restore sessions from URLs, even if they manually add params.

### 4. **Logout Security**
```python
def logout_user():
    # Clear ALL session data
    st.session_state.authenticated = False
    st.session_state.guest_session_id = None  # Critical!
    # ... clear all other fields

# Also clear URL params
if 'auth' in st.query_params:
    del st.query_params['auth']
if 'session' in st.query_params:
    del st.query_params['session']
```

---

## Quick Start

### Prerequisites
```bash
# Python 3.8+
# Conda environment recommended

conda create -n nish python=3.10
conda activate nish
```

### Installation
```bash
cd User_chat
pip install streamlit langchain langgraph langchain-openai sqlite3
```

### Environment Setup
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Run Application
```bash
streamlit run app.py
```

### Access
Open browser: `http://localhost:8501`

---

## User Types

### 1. **Student (Authenticated)**
- **Login**: Student ID + Password
- **user_id**: Actual student ID (e.g., "S001")
- **Sees**: All their own chat sessions across logins
- **URL Persistence**: ✅ Yes

### 2. **Employee (Authenticated)**
- **Login**: Employee ID + Password
- **user_id**: Actual employee ID (e.g., "E001")
- **Sees**: All their own chat sessions across logins
- **URL Persistence**: ✅ Yes

### 3. **Admin (Authenticated HR)**
- **Login**: Employee ID + Password (HR department only)
- **user_id**: Employee ID (e.g., "E003")
- **is_hr**: True
- **Sees**: Their own chat sessions
- **Future**: Can view all guest chats for support/analytics
- **URL Persistence**: ✅ Yes

### 4. **Guest Student**
- **Login**: Click "Continue as Guest"
- **user_id**: "guest_student" (shared)
- **guest_session_id**: Unique per visit
- **Sees**: Only chats from THIS visit
- **URL Persistence**: ❌ No

### 5. **Guest Employee**
- **Login**: Click "Continue as Guest"
- **user_id**: "guest_employee" (shared)
- **guest_session_id**: Unique per visit
- **Sees**: Only chats from THIS visit
- **URL Persistence**: ❌ No

### 6. **Partner (Guest)**
- **Login**: Click "Partner" button (instant guest)
- **user_id**: "guest_partner" (shared)
- **guest_session_id**: Unique per visit
- **Sees**: Only chats from THIS visit
- **URL Persistence**: ❌ No

---

## Technical Workflow

### Application Startup (`app.py`)
```python
1. SessionManager.init_session()
   └─ Initialize all session_state variables

2. restore_session_from_query_params()
   ├─ Check ?auth=xxx → restore authenticated user
   ├─ Check ?session=yyy → load that session (with permission check)
   └─ For guests: Clear URL params

3. Routing:
   ├─ if authenticated → render_chat_page()
   └─ else → render_login_page()
```

### Login Flow (`pages/login.py`)
```python
1. User selects role (Student/Employee/Partner/Admin)

2. Authenticated Login:
   ├─ DatabaseAuth.authenticate_student(user_id, password)
   ├─ Or DatabaseAuth.authenticate_employee(user_id, password)
   └─ SessionManager.login_user(user_data)
       └─ Sets session_state.guest_session_id = None

3. Guest Login:
   ├─ SessionManager.login_user(guest_data)
   └─ Generates unique guest_session_id

4. Redirect to chat page
```

### Chat Flow (`pages/chat.py`)
```python
1. render_chat_page()
   ├─ Initialize chatbot (EnhancedHNUChatbot)
   ├─ render_sidebar() → Show chat history
   └─ Chat input

2. User sends message:
   ├─ If no current_session_id:
   │   └─ SessionManager.create_new_session()
   │       ├─ Generate session_id
   │       ├─ Save to database with full context
   │       └─ Update URL (authenticated only)
   │
   ├─ Save user message to database
   ├─ Process through chatbot
   ├─ Save bot response to database
   └─ Update title (if first message)

3. Sidebar:
   ├─ "New Chat" → Clear session, clear URL param
   ├─ Load old chat → SessionManager.load_session()
   │   └─ Validates ownership first
   └─ Delete chat → SessionManager.delete_session()
       └─ Validates ownership first
```

### Database Operations (`database/chat.py`)
```python
# Save session
db.create_session(
    session_id="session_xyz",
    user_id="S001" or "guest_student",
    user_type="student",
    is_guest=False or True,
    user_name="John Doe",
    user_department="Computer Science",
    user_degree="Bachelor",
    guest_session_id=None or "guest_abc123"
)

# Get authenticated user's history
sessions = db.get_user_sessions(
    user_id="S001",
    user_type="student"
)
# Returns: WHERE user_id='S001' AND is_guest=0

# Get guest's history
sessions = db.get_guest_sessions(
    guest_session_id="guest_abc123"
)
# Returns: WHERE guest_session_id='guest_abc123' AND is_guest=1
```

---

## Data Flow Diagram

```
[User] → [Login Page] → [Database Auth] → [Session Manager]
   ↓                                            ↓
[Chat Page] ← [URL Params] ← [Session State]
   ↓
[User Message] → [Chatbot (LangGraph)] → [Bot Response]
   ↓                                            ↓
[Chat DB] ← Save Message ← [Session Manager]
```

---

## Key Files Explained

### `app.py`
- **Purpose**: Main entry point and routing
- **Key Functions**:
  - `restore_session_from_query_params()`: Restore auth + session from URL
  - `save_session_to_query_params()`: Save auth + session to URL (auth only)
  - `main()`: Application router

### `core/session_manager.py`
- **Purpose**: Manage all session state and database interactions
- **Key Methods**:
  - `login_user()`: Set session after login, generate guest_session_id
  - `logout_user()`: Clear all session data
  - `create_new_session()`: Create new chat session in database
  - `load_session()`: Load session with ownership validation
  - `can_access_session()`: Security check for session access
  - `get_chat_history()`: Get user-specific or guest-specific history
  - `save_message()`: Save message to database, update title

### `database/auth.py`
- **Purpose**: Handle user authentication
- **Key Methods**:
  - `authenticate_student(user_id, password)`: Validate student credentials
  - `authenticate_employee(user_id, password, require_hr)`: Validate employee credentials

### `database/chat.py`
- **Purpose**: Chat persistence layer
- **Key Methods**:
  - `create_session()`: Insert new session with full context
  - `get_user_sessions()`: Get sessions for authenticated user
  - `get_guest_sessions()`: Get sessions for specific guest visit
  - `save_message()`: Insert message into chat_messages
  - `delete_session()`: Remove session and all messages

### `pages/login.py`
- **Purpose**: Login UI
- **Components**:
  - Role selection buttons (Student, Employee, Partner, Admin)
  - Login form
  - Guest mode button
  - Authentication handling

### `pages/chat.py`
- **Purpose**: Chat interface
- **Components**:
  - Header with logout button
  - Sidebar with chat history and "New Chat" button
  - Chat message display
  - Chat input
  - Suggested questions
  - Quick actions
  - Message processing

---

## Testing Scenarios

### Test 1: Guest Isolation
```
1. Open browser A → Guest Student login
2. Send message "Hello from Guest A"
3. Open browser B → Guest Student login
4. Browser B sidebar should be EMPTY
5. Database check: Both sessions exist with different guest_session_ids
```

### Test 2: Authenticated Persistence
```
1. Login as S001
2. Create chat, send messages
3. Logout
4. Login as S001 again
5. Should see previous chat in sidebar
6. Click chat → should load all messages
7. Refresh page → should stay on same chat (URL persistence)
```

### Test 3: Session Ownership
```
1. Login as S001 → Create session_abc
2. Manually try to load S002's session in console
3. Should be blocked by can_access_session()
4. Verify in database: session owner is S002, current user is S001
```

---

## Troubleshooting

### Issue: "No module named 'database'"
**Solution**: Run from User_chat directory
```bash
cd User_chat
streamlit run app.py
```

### Issue: "Database file not found"
**Solution**: Check database path is correct
```bash
ls database/hnu_users.db
```

### Issue: Guest sees other guest's chats
**Solution**: Check `guest_session_id` generation in `SessionManager.login_user()`

### Issue: URL not updating
**Solution**: Check `save_session_to_query_params()` is called after session changes

---

## Future Enhancements

1. **Admin Dashboard**:
   - View all guest chats
   - Analytics on common questions
   - Export chat transcripts

2. **Multi-language Support**:
   - German interface
   - Auto-detect user language

3. **File Upload**:
   - Allow students to upload documents
   - Extract text and add to context

4. **Email Notifications**:
   - Send chat transcript to user email
   - Admin alerts for urgent queries

---

## License

Internal use only - HNU

## Contact

For questions or issues, please contact the development team.

---

**Last Updated**: October 14, 2025
**Version**: 1.0.0
**Author**: HNU Development Team
