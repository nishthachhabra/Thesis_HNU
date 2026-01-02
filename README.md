# HNU Chatbot - Intelligent University Support Assistant

An advanced AI-powered chatbot for Hochschule Neu-Ulm (HNU) University with personalized conversations, intelligent context management, and multi-modal knowledge retrieval.

> **📖 Documentation Structure:**
> - **This README**: Quick start, features overview, and user guide
> - **[User_chat/README.md](User_chat/README.md)**: Detailed technical documentation for developers

---

## 🎯 What This Chatbot Does

The HNU Chatbot provides intelligent, personalized support to students, employees, and partners by:

1. **Understanding Context**: Analyzes user intent, sentiment, and conversation patterns
2. **Remembering Interactions**: Tracks conversation history across sessions for personalized responses
3. **Smart Knowledge Retrieval**: Uses two complementary search methods:
   - **Vector Search (ChromaDB)**: Semantic search through 4,608 HNU knowledge base documents
   - **Text Similarity**: Finds similar previous conversations to learn from past interactions
4. **Natural Conversations**: Generates human-like, empathetic responses using GPT-4o-mini
5. **Adaptive Personalization**: Adapts tone, cultural style, and references based on user history

---

## ✨ Key Features

### 1. Intelligent Intent & Sentiment Analysis
- **Intent Classification**: Automatically categorizes queries (enrollment, IT support, courses, finance, etc.)
- **Sentiment Detection**: Tracks emotional tone (positive, negative, neutral) with lead scores (0-100)
- **Pattern Recognition**: Identifies recurring topics and frustration trends
- **Supports**: English and German

### 2. Advanced Context Management

#### Per-Session Analytics
- Tracks **all intents** and **dominant sentiment** for each chat session
- Aggregates data from last **10 sessions** to understand user journey
- Calculates average lead scores per session

#### Similar Message Search
- Finds **5 most similar** previous conversations using text similarity (SequenceMatcher)
- Includes **context window**: 1 message before + current + 1 message after
- Learns what worked/didn't work in similar situations

### 3. Dual Knowledge Retrieval

#### ChromaDB Vector Search
- **4,608 documents** indexed from HNU knowledge base
- Uses **OpenAI text-embedding-3-small** for semantic embeddings
- Returns top 5 most relevant documents for each query

#### Previous Chat History
- Text-based similarity search through user's message history
- 40% minimum similarity threshold
- Provides conversational continuity

### 4. Personalized Response Generation

Uses GPT-4o-mini with rich context:
- **Tone Analysis**: Detects urgency, gratitude, frustration, curiosity
- **Cultural Awareness**: Adapts to German vs English communication styles (formal/casual)
- **Sentiment Trends**: Celebrates improvements, addresses recurring frustrations
- **Memory & Continuity**: References previous chats naturally ("Hey, I remember we talked about...")
- **Idiom Understanding**: Handles colloquialisms appropriately

### 5. Multi-User Support
- **Students**: Authenticated login with persistent history
- **Employees**: Department-specific support
- **Partners**: Guest access with isolated sessions
- **Admin (HR)**: Special privileges for oversight

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8+ required
# Conda environment recommended
conda create -n hnu_chatbot python=3.10
conda activate hnu_chatbot
```

### Installation

```bash
# Clone/navigate to the project
cd HNUChatbot

# Install dependencies
pip install -r requirements.txt

# Additional dependencies for Streamlit
pip install streamlit chromadb sentence-transformers
```

### Environment Setup

Create a `.env` file in the root directory:

```bash
OPENAI_API_KEY=your-api-key-here
or set OPENAI_API_KEY=your-api-key-here (if not creating env)
```

### Run the Application

```bash
cd User_chat
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
HNUChatbot/
├── README.md                      # This file (user guide & quick start)
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables (OpenAI API key)
│
├── User_chat/                    # Main application (see User_chat/README.md for details)
│   ├── app.py                   # Streamlit entry point
│   ├── core/                    # Core business logic
│   │   ├── chatbot.py          # LangGraph chatbot with personalization
│   │   ├── analyzers.py        # Intent, sentiment, and pattern analysis
│   │   └── session_manager.py  # Session state management
│   ├── database/                # Database layer
│   │   ├── auth.py             # User authentication
│   │   ├── chat.py             # Chat persistence & analytics
│   │   └── hnu_support.db      # SQLite database
│   └── pages/                   # UI pages
│       ├── login.py            # Login interface
│       └── chat.py             # Chat interface
│
├── models/                       # ML models & knowledge base tools
│   ├── intent_classifier.py    # Intent classification engine
│   ├── sentiment_analyzer.py   # Sentiment analysis engine
│   ├── query_chromadb.py       # ChromaDB vector search
│   └── generate_chromadb_kb.py # Knowledge base indexing tool
│
├── data/                         # Data storage
│   ├── chromadb/               # Vector database (4,608 documents)
│   ├── kb/                     # FAISS index (legacy - not actively used)
│   ├── bot_data/               # Intent training data (TSV files)
│   │   └── synthetic_data/     # English & German training data
│   │       ├── en/            # English data (student/employee/partner)
│   │       └── de/            # German data (student/employee/partner)
│   └── analytics/              # CSV logs for analytics
│
└── extra/                      # Archived old files
```
For results: 
Complete_cal.py turns the output in matrix_analysis_results.txt: preference score, preference variance, rating correlation matrix, Fleiss’ kappa, Krippendorff’s alpha, confusion matrix (language × system), language bias score, PCA explained variance

and calcultion_main.py returns the outputs in combined_metrics_verification_report.txt: latency metrics, vector relevance score, retrieval hit rate, preference rate, McNemar chi-square, p-value, confidence interval, Cohen’s h, language-wise preference rates, dimension scores (clarity, helpfulness, empathy, personalization)

Data source from survey: ThesisResponses(AB)_tones.xlsx: Survey excel sheet with 50 participants, 21 questions and each questions has 4 dimension tones.
## Login in chatbot

For Student: file can be found in the main directory named as students.xlsx, use ID and Password column to use bot
For Employees: file can be found in the main directory named as employee.xlsx, use ID and Password column to use bot
For Admin: file can be found in the main directory named as employee.xlsx, use ID and Password column ONLY for HR to view dashboard

UI_Naina_HNU_chatbot.pdf contains the images of every page of the chatbot
---

## 🔄 How It Works: Complete Message Flow

### Step 1: User Sends Message

User types a query in the chat interface.

### Step 2: Context Gathering (Parallel Operations)

The system simultaneously:

1. **Analyzes Current Message**
   - Detects language (English/German)
   - Classifies intent (enrollment, IT, courses, etc.)
   - Analyzes sentiment (positive/negative/neutral)
   - Calculates lead score (0-100)

2. **Retrieves Session History**
   - Gets last **10 chat sessions** with aggregated data:
     - All intents per session
     - Dominant intent
     - Majority sentiment
     - Average lead score

3. **Finds Similar Conversations**
   - Searches last 200 user messages
   - Uses text similarity (SequenceMatcher)
   - Returns top 5 matches (≥40% similarity)
   - Includes before/after context for each match

4. **Searches Knowledge Base**
   - Generates OpenAI embedding for query
   - Searches ChromaDB vector database
   - Returns top 5 relevant documents

### Step 3: Context Enrichment

Combines all data into a rich context:

```
📊 User Profile & History
   - User Type: Student | Employee | Partner
   - Language: English | German
   - Total Sessions: 15

📈 Session Analytics (Last 10 Sessions)
   Session 1: Intents: [enrollment, deadline] | Sentiment: negative (40/100)
   Session 2: Intents: [courses] | Sentiment: positive (75/100)
   ...

📝 Similar Previous Conversations (with Context)
   1. Similar Discussion (Similarity: 75%)
      Before: "I need help with enrollment"
      User Asked: "How do I enroll for summer semester?"
      → Intent: enrollment | Sentiment: neutral | Lead Score: 60
      Response Given: "Visit the registration portal at..."
   ...

📚 Relevant Knowledge Base
   1. [Enrollment Process] Summer semester registration opens...
   2. [Important Dates] Key deadlines for 2025...
   ...
```

### Step 4: Personalized Prompt Generation

The system creates a comprehensive prompt with:

- **Tone Analysis**: "Urgent/Frustrated" | "Grateful/Positive" | "Curious"
- **Cultural Context**: "German (Formal)" | "English (Casual)"
- **Sentiment Trend**:
  - "🎉 User was frustrated but now better! Acknowledge this!"
  - "⚠️ RECURRING FRUSTRATION: Be EXTRA empathetic"
- **Personalization Guidelines**:
  - Reference past conversations naturally
  - Adapt to emotional state
  - Match communication style
  - Learn from what worked before

### Step 5: Response Generation

GPT-4o-mini generates a response using:
- System prompt with all context
- Conversation history
- User query

### Step 6: Database Updates

After response:
- Save message with intent, sentiment, lead_score
- Update user stats (append to last 10 arrays)
- Log to analytics CSV

---

## 🗄️ Database Architecture

### Tables

#### 1. `chat_sessions`
Stores chat session metadata.

| Column | Type | Description |
|--------|------|-------------|
| session_id | TEXT (PK) | Unique session identifier |
| user_id | TEXT | User ID or "guest_student" |
| user_type | TEXT | "student", "employee", "partner", "admin" |
| is_guest | BOOLEAN | 1 for guests, 0 for authenticated |
| title | TEXT | First message preview |
| created_at | TIMESTAMP | Session creation time |

#### 2. `chat_messages`
Stores individual messages.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| session_id | TEXT (FK) | References chat_sessions |
| role | TEXT | "user" or "assistant" |
| content | TEXT | Message text |
| timestamp | TEXT | HH:MM:SS format |
| intent | TEXT | Classified intent (NEW) |
| sentiment | TEXT | Detected sentiment (NEW) |
| lead_score | INTEGER | Engagement score 0-100 (NEW) |
| is_suggestion | BOOLEAN | 1 if from suggestion button |

#### 3. `user_stats`
Caches per-user analytics.

| Column | Type | Description |
|--------|------|-------------|
| user_id | TEXT (PK) | User identifier |
| user_type | TEXT | User type |
| recent_intents | TEXT | JSON array of last 10 intents |
| recent_sentiments | TEXT | JSON array of last 10 sentiments |
| recent_scores | TEXT | JSON array of last 10 lead scores |
| total_chats | INTEGER | Total chat count |
| updated_at | TIMESTAMP | Last update time |

> **📖 For detailed database operations, see [User_chat/README.md](User_chat/README.md)**

---

## 🔍 Technical Details

### Intent Classification
- **Method**: Pattern matching with `difflib.SequenceMatcher`
- **Training Data**: TSV files in `data/bot_data/synthetic_data/`
- **Supported Intents**:
  - Enrollment & Admissions
  - Course Information
  - Academic Calendar
  - IT Support
  - Finance & Tuition
  - Library Services
  - Student Services
  - Career Support
  - General Queries

### Sentiment Analysis
- **Method**: Rule-based + keyword detection
- **Intent-Aware**: Adjusts sentiment based on intent context
- **Bias Detection**: Identifies potentially biased language
- **Lead Scoring**: 0-100 scale (higher = more engaged)

### Vector Search (ChromaDB)
- **Documents**: 4,608 indexed chunks
- **Embedding Model**: OpenAI `text-embedding-3-small`
- **Collection**: `hnu_knowledge_base`
- **Search**: Cosine similarity, top-k retrieval

### Text Similarity (Chat History)
- **Method**: `difflib.SequenceMatcher` (character-level)
- **Threshold**: 40% minimum similarity
- **Scope**: Last 200 user messages
- **Context**: 1 before + current + 1 after pattern

### Response Generation
- **Model**: OpenAI GPT-4o-mini
- **Max Tokens**: 300
- **Temperature**: 0.7
- **Fallback**: Template responses if API fails

---

## 🎨 User Interface

### Login Page
- Role selection (Student/Employee/Partner/Admin)
- Authentication form
- Guest mode button
- Secure session management

### Chat Interface
- **Header**: User name, logout button
- **Sidebar**:
  - New chat button
  - Chat history (session titles)
  - Delete session option
- **Main Area**:
  - Message display with avatars
  - Chat input
  - Suggested questions
  - Quick actions

---

## 📊 Analytics & Monitoring

### CSV Logging
Location: `data/analytics/insights_*.csv`

Separate files for:
- `insights_students.csv`
- `insights_employee.csv`
- `insights_partner.csv`

Tracked Metrics:
- Intent distribution
- Sentiment trends
- Lead scores
- User patterns
- Frustration indicators
- Response quality

### Database Analytics
Query `user_stats` table to:
- Monitor total interactions per user
- Analyze recent intent/sentiment patterns
- Identify users needing support escalation

---

## 🔐 Security Features

### Guest Isolation
- Each guest visit gets unique `guest_session_id`
- Guests cannot see other guests' conversations
- No URL-based session restoration for guests

### Session Ownership Validation
- Every session load/delete validates ownership
- Blocks unauthorized access attempts
- Separate queries for authenticated vs guest users

### Authentication
- Secure password handling
- Session state management
- URL-based session restoration (authenticated only)

> **📖 For detailed security architecture, see [User_chat/README.md](User_chat/README.md)**

---

## 🛠️ Configuration

### OpenAI API
Set in `.env`:
```bash
OPENAI_API_KEY=your-key-here
```

### ChromaDB
- Location: `data/chromadb/`
- Collection: `hnu_knowledge_base`
- Config: `data/chromadb/kb_config.json`

### Intent Training Data
- Location: `data/bot_data/synthetic_data/`
- Format: TSV files (query, intent)
- Languages: `en/` and `de/`

---

## 🐛 Troubleshooting

### Import Errors
**Issue**: `No module named 'database'` or `No module named 'core'`

**Solution**: Always run from `User_chat/` directory:
```bash
cd User_chat
streamlit run app.py
```

### OpenAI API Errors
**Issue**: API calls failing or rate limits hit

**Solution**:
1. Verify `OPENAI_API_KEY` in `.env`
2. Check API quota at platform.openai.com
3. System falls back to template responses automatically

### ChromaDB Not Found
**Issue**: Vector search failing

**Solution**:
1. Check `data/chromadb/` exists
2. Verify `chroma.sqlite3` file is present
3. Re-run `models/generate_chromadb_kb.py` if needed

### Database Errors
**Issue**: SQLite errors or missing tables

**Solution**:
1. Check `User_chat/database/hnu_support.db` exists
2. Database auto-creates tables on first run
3. Migration code auto-adds new columns (intent, sentiment, lead_score)

### Intent/Sentiment Not Saving
**Issue**: Messages saved without intent/sentiment

**Solution**:
1. Check database migration completed (lines 74-90 in `database/chat.py`)
2. Verify `save_message()` includes intent/sentiment parameters
3. Check logs for analysis errors

---

## 📈 Performance

### Typical Response Time
- Profile Load: ~10ms (single SELECT)
- Analysis (Intent + Sentiment): ~50ms
- ChromaDB Vector Search: ~100ms
- Similar Message Search: ~50ms
- GPT-4o-mini API Call: ~1-2 seconds
- Stats Update: ~10ms (single UPDATE)

**Total**: ~1.5-2.5 seconds per message

### Optimization Tips
- Limit session stats to 10 (configurable)
- Similar message search uses 40% threshold (adjustable)
- ChromaDB returns top 5 docs (configurable)
- GPT-4o-mini uses 300 max tokens (adjustable)

---

## 🚧 Future Enhancements

1. **Multi-language Knowledge Base**: Separate vector collections for German docs
2. **Real-time Escalation**: Auto-escalate frustrated users to human agents
3. **Voice Interface**: Speech-to-text integration
4. **Mobile App**: Native iOS/Android support
5. **Advanced Analytics Dashboard**: Real-time insights for admins
6. **File Upload**: Allow document analysis in conversations
7. **Email Integration**: Send chat transcripts
8. **Proactive Suggestions**: Predict user needs based on patterns

---

## 📚 Documentation

- **Main README** (this file): Quick start & features overview
- **[User_chat/README.md](User_chat/README.md)**: Detailed technical documentation
  - Database schema details
  - Session management architecture
  - Security implementation
  - Code structure & API reference
  - Testing scenarios

---

## 📝 License

Internal use only - Hochschule Neu-Ulm (HNU)

---

## 📞 Contact & Support

For questions, issues, or support:
- **Email**: info@hnu.de
- **HNU Website**: [https://www.hnu.de](https://www.hnu.de)

---

**Last Updated**: October 15, 2025
**Version**: 2.0.0
**Author**: HNU Development Team
