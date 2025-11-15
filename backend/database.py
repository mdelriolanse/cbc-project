import sqlite3
from datetime import datetime
from typing import Optional, List
import json

DATABASE_FILE = "debate_platform.db"

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            overall_summary TEXT,
            consensus_view TEXT,
            timeline_view TEXT
        )
    """)
    
    # Create arguments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arguments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            side TEXT NOT NULL CHECK(side IN ('pro', 'con')),
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            author TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def get_topic(topic_id: int) -> Optional[dict]:
    """Get a topic by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def create_topic(question: str, created_by: str) -> int:
    """Create a new topic and return its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO topics (question, created_by, created_at) VALUES (?, ?, ?)",
        (question, created_by, datetime.utcnow().isoformat())
    )
    topic_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return topic_id

def get_all_topics() -> list:
    """Get all topics with pro/con counts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.id,
            t.question,
            t.created_by,
            t.created_at,
            COUNT(CASE WHEN a.side = 'pro' THEN 1 END) as pro_count,
            COUNT(CASE WHEN a.side = 'con' THEN 1 END) as con_count
        FROM topics t
        LEFT JOIN arguments a ON t.id = a.topic_id
        GROUP BY t.id, t.question, t.created_by, t.created_at
        ORDER BY t.created_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_topic_with_arguments(topic_id: int) -> Optional[dict]:
    """Get a topic with its arguments, sorted by validity score (highest first)."""
    topic = get_topic(topic_id)
    if not topic:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Sort by validity_score DESC (nulls last), then created_at DESC
    cursor.execute("""
        SELECT * FROM arguments 
        WHERE topic_id = ? 
        ORDER BY 
            CASE WHEN validity_score IS NULL THEN 1 ELSE 0 END,
            validity_score DESC,
            created_at DESC
    """, (topic_id,))
    rows = cursor.fetchall()
    conn.close()
    
    arguments = [dict(row) for row in rows]
    # Parse key_urls JSON for each argument
    for arg in arguments:
        if arg.get('key_urls'):
            try:
                arg['key_urls'] = json.loads(arg['key_urls'])
            except (json.JSONDecodeError, TypeError):
                arg['key_urls'] = []
        else:
            arg['key_urls'] = []
    
    pro_arguments = [arg for arg in arguments if arg['side'] == 'pro']
    con_arguments = [arg for arg in arguments if arg['side'] == 'con']
    
    # Parse timeline_view if it exists
    timeline_view = None
    if topic.get('timeline_view'):
        try:
            timeline_view = json.loads(topic['timeline_view'])
        except (json.JSONDecodeError, TypeError):
            timeline_view = None
    
    return {
        'id': topic['id'],
        'question': topic['question'],
        'created_by': topic['created_by'],
        'created_at': topic['created_at'],
        'pro_arguments': pro_arguments,
        'con_arguments': con_arguments,
        'overall_summary': topic.get('overall_summary'),
        'consensus_view': topic.get('consensus_view'),
        'timeline_view': timeline_view
    }

def create_argument(topic_id: int, side: str, title: str, content: str, author: str, sources: Optional[str] = None) -> int:
    """Create a new argument and return its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO arguments (topic_id, side, title, content, sources, author, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (topic_id, side, title, content, sources, author, datetime.utcnow().isoformat())
    )
    argument_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return argument_id

def get_arguments(topic_id: int, side: Optional[str] = None) -> list:
    """Get arguments for a topic, optionally filtered by side."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if side and side in ['pro', 'con']:
        cursor.execute(
            "SELECT * FROM arguments WHERE topic_id = ? AND side = ? ORDER BY created_at ASC",
            (topic_id, side)
        )
    else:
        cursor.execute(
            "SELECT * FROM arguments WHERE topic_id = ? ORDER BY created_at ASC",
            (topic_id,)
        )
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_argument_counts(topic_id: int) -> dict:
    """Get pro and con argument counts for a topic."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN side = 'pro' THEN 1 END) as pro_count,
            COUNT(CASE WHEN side = 'con' THEN 1 END) as con_count
        FROM arguments
        WHERE topic_id = ?
    """, (topic_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {'pro_count': 0, 'con_count': 0}

def update_topic_analysis(topic_id: int, overall_summary: str, consensus_view: str, timeline_view: list):
    """Update topic with generated analysis."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timeline_json = json.dumps(timeline_view) if timeline_view else None
    cursor.execute(
        """UPDATE topics 
           SET overall_summary = ?, consensus_view = ?, timeline_view = ?
           WHERE id = ?""",
        (overall_summary, consensus_view, timeline_json, topic_id)
    )
    conn.commit()
    conn.close()

def migrate_add_validity_columns():
    """Add validity columns to arguments table if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if columns exist by trying to add them (SQLite doesn't have IF NOT EXISTS for ALTER TABLE)
    try:
        cursor.execute("""
            ALTER TABLE arguments 
            ADD COLUMN validity_score INTEGER
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("""
            ALTER TABLE arguments 
            ADD COLUMN validity_reasoning TEXT
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("""
            ALTER TABLE arguments 
            ADD COLUMN validity_checked_at TIMESTAMP
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("""
            ALTER TABLE arguments 
            ADD COLUMN key_urls TEXT
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()
    conn.close()

def update_argument_validity(argument_id: int, validity_score: int, validity_reasoning: str, key_urls: Optional[List[str]] = None):
    """Update argument with validity check results."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Store key_urls as JSON string
    key_urls_json = json.dumps(key_urls) if key_urls else None
    cursor.execute(
        """UPDATE arguments 
           SET validity_score = ?, validity_reasoning = ?, validity_checked_at = ?, key_urls = ?
           WHERE id = ?""",
        (validity_score, validity_reasoning, datetime.utcnow().isoformat(), key_urls_json, argument_id)
    )
    conn.commit()
    conn.close()

def get_argument(argument_id: int) -> Optional[dict]:
    """Get a single argument by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM arguments WHERE id = ?", (argument_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_arguments_sorted_by_validity(topic_id: int, side: Optional[str] = None) -> list:
    """Get arguments sorted by validity score (highest first, unverified at end)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if side and side in ['pro', 'con']:
        cursor.execute("""
            SELECT * FROM arguments 
            WHERE topic_id = ? AND side = ?
            ORDER BY 
                CASE WHEN validity_score IS NULL THEN 1 ELSE 0 END,
                validity_score DESC,
                created_at ASC
        """, (topic_id, side))
    else:
        cursor.execute("""
            SELECT * FROM arguments 
            WHERE topic_id = ?
            ORDER BY 
                CASE WHEN validity_score IS NULL THEN 1 ELSE 0 END,
                validity_score DESC,
                created_at ASC
        """, (topic_id,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]