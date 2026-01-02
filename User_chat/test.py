import sqlite3
import os
from pathlib import Path

# Try multiple path variations
possible_paths = [
    Path(__file__).parent / 'database' / 'hnu_users.db',
    Path('User_chat/database/hnu_users.db'),
    Path('./database/hnu_users.db'),
    Path('database/hnu_users.db'),
]

print(f"Current working directory: {os.getcwd()}\n")

db_path = None
for path in possible_paths:
    print(f"Trying: {path}")
    if path.exists():
        db_path = path
        print(f"✅ Found at: {db_path}\n")
        break
    else:
        print(f"❌ Not found\n")

if db_path is None:
    print("❌ Database not found in any location!")
    exit()

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check tables
    print("=" * 50)
    print("TABLES IN DATABASE:")
    print("=" * 50)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check chat_messages count
    print("\n" + "=" * 50)
    print("CHAT MESSAGES COUNT:")
    print("=" * 50)
    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    count = cursor.fetchone()[0]
    print(f"Total messages: {count}")
    
    # Check chat_sessions count
    print("\n" + "=" * 50)
    print("CHAT SESSIONS COUNT:")
    print("=" * 50)
    cursor.execute("SELECT COUNT(*) FROM chat_sessions")
    count = cursor.fetchone()[0]
    print(f"Total sessions: {count}")
    
    # Show sample data
    if count > 0:
        print("\n" + "=" * 50)
        print("SAMPLE MESSAGES:")
        print("=" * 50)
        cursor.execute("""
            SELECT id, session_id, role, content, intent, sentiment, lead_score 
            FROM chat_messages 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Session: {row[1]}, Role: {row[2]}")
            print(f"  Content: {row[3][:50]}...")
            print(f"  Intent: {row[4]}, Sentiment: {row[5]}, Lead Score: {row[6]}\n")
    
    conn.close()
    print("✅ Database connection successful!")
    
except sqlite3.OperationalError as e:
    print(f"❌ Database error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")