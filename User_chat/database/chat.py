"""
Chat Database Module
Simple SQLite persistence for chat sessions and messages
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class ChatDatabase:
    """Handle chat persistence in SQLite"""

    def __init__(self, db_path='database/hnu_users.db'):
        """Initialize database connection"""
        self.db_path = db_path
        self.create_tables()

    def create_tables(self):
        """Create chat tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Chat sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                user_type TEXT NOT NULL,
                is_guest BOOLEAN DEFAULT 0,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Chat messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                is_suggestion BOOLEAN DEFAULT 0,
                intent TEXT,
                sentiment TEXT,
                lead_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
            )
        ''')

        # User stats table for caching analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id TEXT PRIMARY KEY,
                user_type TEXT NOT NULL,
                recent_intents TEXT DEFAULT '[]',
                recent_sentiments TEXT DEFAULT '[]',
                recent_scores TEXT DEFAULT '[]',
                total_chats INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_stats_user ON user_stats(user_id)')

        # Migration: Add new columns if they don't exist
        try:
            cursor.execute("PRAGMA table_info(chat_messages)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'intent' not in columns:
                cursor.execute('ALTER TABLE chat_messages ADD COLUMN intent TEXT')
                print("✅ Added 'intent' column to chat_messages")

            if 'sentiment' not in columns:
                cursor.execute('ALTER TABLE chat_messages ADD COLUMN sentiment TEXT')
                print("✅ Added 'sentiment' column to chat_messages")

            if 'lead_score' not in columns:
                cursor.execute('ALTER TABLE chat_messages ADD COLUMN lead_score INTEGER')
                print("✅ Added 'lead_score' column to chat_messages")
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")

        conn.commit()
        conn.close()

    def create_session(self, session_id: str, user_id: str, user_type: str, is_guest: bool = False,
                      user_name: str = None, user_department: str = None, user_degree: str = None,
                      guest_session_id: str = None) -> bool:
        """Create a new chat session with full user context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO chat_sessions
                (session_id, user_id, user_type, is_guest, title,
                 user_name, user_department, user_degree, guest_session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, user_type, 1 if is_guest else 0, 'New Chat',
                  user_name, user_department, user_degree, guest_session_id))

            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Session already exists
            return False
        except Exception as e:
            print(f"Error creating session: {e}")
            return False

    def save_message(self, session_id: str, role: str, content: str, timestamp: str,
                    is_suggestion: bool = False, intent: str = None,
                    sentiment: str = None, lead_score: int = None) -> bool:
        """Save a message to the database with optional intent/sentiment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO chat_messages (session_id, role, content, timestamp, is_suggestion, intent, sentiment, lead_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, role, content, timestamp, 1 if is_suggestion else 0, intent, sentiment, lead_score))

            # Update session updated_at
            cursor.execute('''
                UPDATE chat_sessions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False

    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title (usually first user message)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE chat_sessions
                SET title = ?
                WHERE session_id = ?
            ''', (title, session_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating title: {e}")
            return False

    def get_user_sessions(self, user_id: str, user_type: str) -> List[Dict[str, Any]]:
        """Get all sessions for an authenticated user (excludes guests)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get sessions for this user (exclude guest sessions)
            cursor.execute('''
                SELECT
                    s.session_id,
                    s.title,
                    s.created_at,
                    s.updated_at,
                    COUNT(m.id) as message_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON s.session_id = m.session_id
                WHERE s.user_id = ? AND s.user_type = ? AND s.is_guest = 0
                GROUP BY s.session_id
                ORDER BY s.updated_at DESC
            ''', (user_id, user_type))

            rows = cursor.fetchall()
            conn.close()

            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row[0],
                    'title': row[1],
                    'created_at': row[2],
                    'updated_at': row[3],
                    'message_count': row[4]
                })

            return sessions
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return []

    def get_guest_sessions(self, guest_session_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a specific guest visit"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get sessions for this guest session ID only
            cursor.execute('''
                SELECT
                    s.session_id,
                    s.title,
                    s.created_at,
                    s.updated_at,
                    COUNT(m.id) as message_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON s.session_id = m.session_id
                WHERE s.guest_session_id = ? AND s.is_guest = 1
                GROUP BY s.session_id
                ORDER BY s.updated_at DESC
            ''', (guest_session_id,))

            rows = cursor.fetchall()
            conn.close()

            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row[0],
                    'title': row[1],
                    'created_at': row[2],
                    'updated_at': row[3],
                    'message_count': row[4]
                })

            return sessions
        except Exception as e:
            print(f"Error getting guest sessions: {e}")
            return []

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT role, content, timestamp, is_suggestion
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY id ASC
            ''', (session_id,))

            rows = cursor.fetchall()
            conn.close()

            messages = []
            for row in rows:
                messages.append({
                    'role': row[0],
                    'content': row[1],
                    'timestamp': row[2],
                    'is_suggestion': bool(row[3]),
                    'avatar': '👤' if row[0] == 'user' else '🤖'
                })

            return messages
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Delete messages first (foreign key constraint)
            cursor.execute('DELETE FROM chat_messages WHERE session_id = ?', (session_id,))

            # Delete session
            cursor.execute('DELETE FROM chat_sessions WHERE session_id = ?', (session_id,))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT 1 FROM chat_sessions WHERE session_id = ? LIMIT 1', (session_id,))
            exists = cursor.fetchone() is not None

            conn.close()
            return exists
        except Exception as e:
            print(f"Error checking session: {e}")
            return False

    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user statistics for personalization"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_type, recent_intents, recent_sentiments, recent_scores, total_chats, updated_at
                FROM user_stats
                WHERE user_id = ?
            ''', (user_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'user_type': row[0],
                    'recent_intents': json.loads(row[1]) if row[1] else [],
                    'recent_sentiments': json.loads(row[2]) if row[2] else [],
                    'recent_scores': json.loads(row[3]) if row[3] else [],
                    'total_chats': row[4],
                    'updated_at': row[5]
                }
            return None
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return None

    def update_user_stats(self, user_id: str, user_type: str, intent: str,
                         sentiment: str, lead_score: int) -> bool:
        """Update user statistics with new interaction"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get existing stats
            stats = self.get_user_stats(user_id)

            if stats:
                # Update existing
                recent_intents = stats['recent_intents']
                recent_sentiments = stats['recent_sentiments']
                recent_scores = stats['recent_scores']

                # Append new values
                recent_intents.append(intent)
                recent_sentiments.append(sentiment)
                recent_scores.append(lead_score)

                # Keep only last 10
                recent_intents = recent_intents[-10:]
                recent_sentiments = recent_sentiments[-10:]
                recent_scores = recent_scores[-10:]

                cursor.execute('''
                    UPDATE user_stats
                    SET recent_intents = ?, recent_sentiments = ?, recent_scores = ?,
                        total_chats = total_chats + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (json.dumps(recent_intents), json.dumps(recent_sentiments),
                     json.dumps(recent_scores), user_id))
            else:
                # Create new
                cursor.execute('''
                    INSERT INTO user_stats (user_id, user_type, recent_intents, recent_sentiments,
                                          recent_scores, total_chats)
                    VALUES (?, ?, ?, ?, ?, 1)
                ''', (user_id, user_type, json.dumps([intent]), json.dumps([sentiment]),
                     json.dumps([lead_score])))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating user stats: {e}")
            return False

    def get_user_previous_chats(self, user_id: str, current_session_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get previous user messages with bot responses from OLD sessions only
        Excludes current session to avoid referencing ongoing conversation
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Exclude current session - only get OLD conversations
            if current_session_id:
                cursor.execute('''
                    SELECT m.content, m.role, m.timestamp, s.session_id, m.created_at
                    FROM chat_messages m
                    JOIN chat_sessions s ON m.session_id = s.session_id
                    WHERE s.user_id = ? AND s.is_guest = 0 AND s.session_id != ?
                    ORDER BY m.created_at DESC
                    LIMIT ?
                ''', (user_id, current_session_id, limit * 2))
            else:
                cursor.execute('''
                    SELECT m.content, m.role, m.timestamp, s.session_id, m.created_at
                    FROM chat_messages m
                    JOIN chat_sessions s ON m.session_id = s.session_id
                    WHERE s.user_id = ? AND s.is_guest = 0
                    ORDER BY m.created_at DESC
                    LIMIT ?
                ''', (user_id, limit * 2))

            rows = cursor.fetchall()
            conn.close()

            # Create conversation pairs (user message + bot response)
            chats = []
            i = 0
            while i < len(rows) - 1:
                # Look for user message followed by assistant response
                if rows[i][1] == 'user' and i + 1 < len(rows):
                    # Find the next assistant response
                    for j in range(i + 1, min(i + 5, len(rows))):  # Look ahead up to 5 messages
                        if rows[j][1] == 'assistant' and rows[j][3] == rows[i][3]:  # Same session
                            chats.append({
                                'user_message': rows[i][0],
                                'bot_response': rows[j][0],
                                'timestamp': rows[i][2],
                                'session_id': rows[i][3],
                                'created_at': rows[i][4]
                            })
                            break
                i += 1

            return chats[:limit]  # Return only requested number
        except Exception as e:
            print(f"Error getting previous chats: {e}")
            return []

    def get_aggregated_session_stats(self, user_id: str, limit_sessions: int = 10) -> Dict[str, Any]:
        """
        Get per-session aggregated statistics for last N sessions
        Each session has: majority intent, majority sentiment, avg lead score
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get last N sessions
            cursor.execute('''
                SELECT s.session_id, s.created_at
                FROM chat_sessions s
                WHERE s.user_id = ? AND s.is_guest = 0
                ORDER BY s.created_at DESC
                LIMIT ?
            ''', (user_id, limit_sessions))

            sessions = cursor.fetchall()

            if not sessions:
                conn.close()
                return {
                    'total_sessions': 0,
                    'session_summaries': []
                }

            session_summaries = []
            from collections import Counter

            # For each session, aggregate intents/sentiments/scores
            for session_id, created_at in sessions:
                cursor.execute('''
                    SELECT intent, sentiment, lead_score, content
                    FROM chat_messages
                    WHERE session_id = ? AND role = 'user' AND intent IS NOT NULL
                    ORDER BY created_at ASC
                ''', (session_id,))

                messages = cursor.fetchall()

                if not messages:
                    continue

                # Extract intents, sentiments, scores
                intents = [m[0] for m in messages if m[0]]
                sentiments = [m[1] for m in messages if m[1]]
                scores = [m[2] for m in messages if m[2] is not None]
                first_message = messages[0][3][:80] if messages else ""

                # Calculate majority intent
                intent_set = list(set(intents))  # Unique intents
                dominant_intent = Counter(intents).most_common(1)[0][0] if intents else 'unknown'

                # Calculate majority sentiment
                dominant_sentiment = Counter(sentiments).most_common(1)[0][0] if sentiments else 'neutral'

                # Calculate average lead score
                avg_score = round(sum(scores) / len(scores), 1) if scores else 50

                session_summaries.append({
                    'session_id': session_id,
                    'created_at': created_at,
                    'message_count': len(messages),
                    'first_message': first_message,
                    'intent_set': intent_set,  # All unique intents in this session
                    'dominant_intent': dominant_intent,  # Most frequent intent
                    'dominant_sentiment': dominant_sentiment,  # Most frequent sentiment
                    'avg_lead_score': avg_score
                })

            conn.close()

            return {
                'total_sessions': len(session_summaries),
                'session_summaries': session_summaries
            }

        except Exception as e:
            print(f"❌ Error getting aggregated session stats: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_sessions': 0,
                'session_summaries': []
            }

    def get_session_level_stats(self, user_id: str, limit_sessions: int = 10) -> Dict[str, Any]:
        """
        Get session-level aggregated statistics for user
        Returns last N sessions with their aggregate intent/sentiment
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get last N sessions with message counts
            cursor.execute('''
                SELECT
                    s.session_id,
                    s.created_at,
                    COUNT(m.id) as message_count
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON s.session_id = m.session_id
                WHERE s.user_id = ? AND s.is_guest = 0
                GROUP BY s.session_id
                ORDER BY s.created_at DESC
                LIMIT ?
            ''', (user_id, limit_sessions))

            sessions = cursor.fetchall()

            session_summaries = []
            all_intents = []
            all_sentiments = []
            all_scores = []
            total_messages = 0

            # For each session, get messages and calculate PER-SESSION aggregates
            for session_id, created_at, msg_count in sessions:
                cursor.execute('''
                    SELECT content, role FROM chat_messages
                    WHERE session_id = ?
                    ORDER BY created_at ASC
                ''', (session_id,))

                messages = cursor.fetchall()
                user_messages = [m[0] for m in messages if m[1] == 'user']
                total_messages += msg_count

                # Get intents/sentiments for THIS session from user_stats
                # (We stored them per message, so we need to map them to this session)
                # For now, use user_stats as proxy - in production, you'd store per session
                old_stats = self.get_user_stats(user_id)
                session_intents = old_stats.get('recent_intents', []) if old_stats else []
                session_sentiments = old_stats.get('recent_sentiments', []) if old_stats else []
                session_scores = old_stats.get('recent_scores', []) if old_stats else []

                # Calculate dominant intent/sentiment for THIS session
                from collections import Counter

                dominant_intent = 'general_query'
                if session_intents:
                    # Take proportional slice (rough estimate based on message count)
                    intent_counts = Counter(session_intents[:len(user_messages)])
                    if intent_counts:
                        dominant_intent = intent_counts.most_common(1)[0][0]

                dominant_sentiment = 'neutral'
                if session_sentiments:
                    sentiment_counts = Counter(session_sentiments[:len(user_messages)])
                    if sentiment_counts:
                        dominant_sentiment = sentiment_counts.most_common(1)[0][0]

                avg_score = sum(session_scores[:len(user_messages)]) / len(user_messages) if session_scores and len(user_messages) > 0 else 50

                # Store session aggregate
                session_summaries.append({
                    'session_id': session_id,
                    'created_at': created_at,
                    'message_count': msg_count,
                    'user_message_count': len(user_messages),
                    'first_message': user_messages[0][:80] if user_messages else "",
                    'dominant_intent': dominant_intent,
                    'dominant_sentiment': dominant_sentiment,
                    'avg_lead_score': round(avg_score, 1)
                })

            conn.close()

            return {
                'total_sessions': len(sessions),
                'total_messages': total_messages,
                'session_summaries': session_summaries,
                'avg_messages_per_session': total_messages / len(sessions) if sessions else 0
            }

        except Exception as e:
            print(f"Error getting session-level stats: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_sessions': 0,
                'total_messages': 0,
                'session_summaries': [],
                'avg_messages_per_session': 0
            }

    def find_similar_messages_with_context(self, current_message: str, user_id: str,
                                          current_session_id: str = None,
                                          limit: int = 5,
                                          min_similarity: float = 0.4) -> List[Dict[str, Any]]:
        """
        Find similar previous user messages with surrounding context (1 before + current + 1 after)

        Args:
            current_message: The message to find similar messages for
            user_id: User ID to search within
            current_session_id: Current session ID to exclude
            limit: Maximum number of similar messages to return (default 5)
            min_similarity: Minimum similarity threshold (0.0 to 1.0, default 0.4)

        Returns:
            List of dicts with structure:
            {
                'similarity_score': 0.85,
                'message_before': {'role': 'assistant', 'content': '...', 'timestamp': '...'},
                'current_message': {
                    'role': 'user',
                    'content': '...',
                    'intent': '...',
                    'sentiment': '...',
                    'lead_score': 75,
                    'timestamp': '...'
                },
                'message_after': {'role': 'assistant', 'content': '...', 'timestamp': '...'},
                'session_id': 'session_xxx'
            }
        """
        try:
            from difflib import SequenceMatcher

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all previous user messages with their IDs, excluding current session
            if current_session_id:
                cursor.execute('''
                    SELECT m.id, m.session_id, m.content, m.intent, m.sentiment,
                           m.lead_score, m.timestamp, m.created_at
                    FROM chat_messages m
                    JOIN chat_sessions s ON m.session_id = s.session_id
                    WHERE s.user_id = ?
                      AND s.is_guest = 0
                      AND m.role = 'user'
                      AND m.session_id != ?
                    ORDER BY m.created_at DESC
                    LIMIT 200
                ''', (user_id, current_session_id))
            else:
                cursor.execute('''
                    SELECT m.id, m.session_id, m.content, m.intent, m.sentiment,
                           m.lead_score, m.timestamp, m.created_at
                    FROM chat_messages m
                    JOIN chat_sessions s ON m.session_id = s.session_id
                    WHERE s.user_id = ?
                      AND s.is_guest = 0
                      AND m.role = 'user'
                    ORDER BY m.created_at DESC
                    LIMIT 200
                ''', (user_id,))

            previous_messages = cursor.fetchall()

            if not previous_messages:
                conn.close()
                return []

            # Calculate similarity for each message
            similarities = []
            current_lower = current_message.lower().strip()

            # Handle very short messages (< 3 chars)
            is_short_message = len(current_lower) < 3

            for msg in previous_messages:
                msg_id, session_id, content, intent, sentiment, lead_score, timestamp, created_at = msg

                # Skip very short messages if current is also short (avoid matching "hi" with "ok")
                if is_short_message and len(content.strip()) < 3:
                    continue

                # Calculate text similarity
                prev_lower = content.lower().strip()
                similarity = SequenceMatcher(None, current_lower, prev_lower).ratio()

                if similarity >= min_similarity:
                    similarities.append({
                        'msg_id': msg_id,
                        'session_id': session_id,
                        'content': content,
                        'intent': intent,
                        'sentiment': sentiment,
                        'lead_score': lead_score,
                        'timestamp': timestamp,
                        'created_at': created_at,
                        'similarity': similarity
                    })

            # Sort by similarity (highest first)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)

            # Take top N
            top_matches = similarities[:limit]

            if not top_matches:
                conn.close()
                return []

            # For each match, get surrounding context (1 before + 1 after)
            results = []

            for match in top_matches:
                msg_id = match['msg_id']
                session_id = match['session_id']

                # Get all messages in this session ordered by created_at
                cursor.execute('''
                    SELECT id, role, content, intent, sentiment, lead_score, timestamp
                    FROM chat_messages
                    WHERE session_id = ?
                    ORDER BY created_at ASC
                ''', (session_id,))

                session_messages = cursor.fetchall()

                # Find the index of our matched message
                match_index = None
                for idx, sm in enumerate(session_messages):
                    if sm[0] == msg_id:  # sm[0] is id
                        match_index = idx
                        break

                if match_index is None:
                    continue

                # Get message before (if exists)
                message_before = None
                if match_index > 0:
                    before = session_messages[match_index - 1]
                    message_before = {
                        'role': before[1],
                        'content': before[2],
                        'timestamp': before[6]
                    }

                # Current message (the matched one)
                current = session_messages[match_index]
                current_msg = {
                    'role': current[1],
                    'content': current[2],
                    'intent': current[3],
                    'sentiment': current[4],
                    'lead_score': current[5],
                    'timestamp': current[6]
                }

                # Get message after (if exists)
                message_after = None
                if match_index < len(session_messages) - 1:
                    after = session_messages[match_index + 1]
                    message_after = {
                        'role': after[1],
                        'content': after[2],
                        'timestamp': after[6]
                    }

                # Build result
                results.append({
                    'similarity_score': round(match['similarity'], 3),
                    'message_before': message_before,
                    'current_message': current_msg,
                    'message_after': message_after,
                    'session_id': session_id,
                    'session_date': match['created_at']
                })

            conn.close()
            return results

        except Exception as e:
            print(f"❌ Error finding similar messages: {e}")
            import traceback
            traceback.print_exc()
            return []
