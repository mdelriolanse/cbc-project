import psycopg2
from datetime import timezone
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, List
import json
import os
from dotenv import load_dotenv
load_dotenv()

# Database connection parameters from environment variables
# Default values are sample/placeholder - use .env file for real values
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "debate_platform")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_db_connection():
    """Get a database connection."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

def _format_datetime_to_iso(dt) -> Optional[str]:
    """Convert datetime object to ISO format string."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt) if dt else None

def init_db():
    """Initialize the database with tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id SERIAL PRIMARY KEY,
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
            id SERIAL PRIMARY KEY,
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
    cursor.close()
    conn.close()

def ensure_argument_matches_table():
    """Ensure the argument_matches table exists (safe to call repeatedly)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS argument_matches (
            id SERIAL PRIMARY KEY,
            topic_id INTEGER NOT NULL,
            pro_id INTEGER NOT NULL,
            con_id INTEGER NOT NULL,
            reason TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def get_topic(topic_id: int) -> Optional[dict]:
    """Get a topic by ID."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM topics WHERE id = %s", (topic_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if row:
        topic = dict(row)
        topic['created_at'] = _format_datetime_to_iso(topic.get('created_at'))
        return topic
    return None

def create_topic(question: str, created_by: str) -> dict:
    """Create a new topic and return the full topic data."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "INSERT INTO topics (question, created_by, created_at) VALUES (%s, %s, %s) RETURNING *",
        (question, created_by, datetime.now(timezone.utc))
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    if row:
        topic = dict(row)
        topic['created_at'] = _format_datetime_to_iso(topic.get('created_at'))
        return topic
    return None

def get_all_topics() -> list:
    """Get all topics with pro/con counts and validity metrics."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # First get basic topic info with counts
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
    
    topics = [dict(row) for row in cursor.fetchall()]
    
    # Convert datetime to ISO string and calculate validity metrics for each topic
    for topic in topics:
        topic['created_at'] = _format_datetime_to_iso(topic.get('created_at'))
        topic_id = topic['id']
        
        # Get average validity for PRO arguments
        cursor.execute("""
            SELECT AVG(validity_score) as avg_validity
            FROM arguments
            WHERE topic_id = %s AND side = 'pro' AND validity_score IS NOT NULL
        """, (topic_id,))
        pro_avg_result = cursor.fetchone()
        pro_avg = pro_avg_result['avg_validity'] if pro_avg_result and pro_avg_result['avg_validity'] is not None else None
        if pro_avg is not None:
            topic['pro_avg_validity'] = float(round(pro_avg, 1))
        else:
            topic['pro_avg_validity'] = None
        
        # Get average validity for CON arguments
        cursor.execute("""
            SELECT AVG(validity_score) as avg_validity
            FROM arguments
            WHERE topic_id = %s AND side = 'con' AND validity_score IS NOT NULL
        """, (topic_id,))
        con_avg_result = cursor.fetchone()
        con_avg = con_avg_result['avg_validity'] if con_avg_result and con_avg_result['avg_validity'] is not None else None
        if con_avg is not None:
            topic['con_avg_validity'] = float(round(con_avg, 1))
        else:
            topic['con_avg_validity'] = None
        
        # Calculate controversy level
        pro_count = topic['pro_count']
        con_count = topic['con_count']
        total_count = pro_count + con_count
        
        if total_count == 0:
            topic['controversy_level'] = None
        else:
            # Calculate balance ratio (closer to 0.5 = more balanced/contested)
            balance_ratio = min(pro_count, con_count) / total_count if total_count > 0 else 0
            
            if balance_ratio >= 0.4:
                # Highly balanced (40%+ on both sides)
                topic['controversy_level'] = "Highly Contested"
            elif balance_ratio >= 0.25:
                # Moderately balanced (25-40% on smaller side)
                topic['controversy_level'] = "Moderately Contested"
            else:
                # One-sided (less than 25% on smaller side)
                topic['controversy_level'] = "Clear Consensus"
    
    cursor.close()
    conn.close()
    return topics

def get_topic_with_arguments(topic_id: int) -> Optional[dict]:
    """Get a topic with its arguments, sorted by validity score (highest first)."""
    topic = get_topic(topic_id)
    if not topic:
        return None
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    # Sort by validity_score DESC (nulls last), then created_at DESC
    cursor.execute("""
        SELECT * FROM arguments 
        WHERE topic_id = %s 
        ORDER BY 
            CASE WHEN validity_score IS NULL THEN 1 ELSE 0 END,
            validity_score DESC,
            created_at DESC
    """, (topic_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    arguments = [dict(row) for row in rows]
    # Parse key_urls JSON and convert timestamps for each argument
    for arg in arguments:
        if arg.get('key_urls'):
            try:
                arg['key_urls'] = json.loads(arg['key_urls'])
            except (json.JSONDecodeError, TypeError):
                arg['key_urls'] = []
        else:
            arg['key_urls'] = []
        # Convert datetime fields to ISO strings
        arg['created_at'] = _format_datetime_to_iso(arg.get('created_at'))
        arg['validity_checked_at'] = _format_datetime_to_iso(arg.get('validity_checked_at'))
    
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
        'created_at': _format_datetime_to_iso(topic.get('created_at')),
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
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (topic_id, side, title, content, sources, author, datetime.now(timezone.utc))
    )
    argument_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return argument_id

def get_arguments(topic_id: int, side: Optional[str] = None) -> list:
    """Get arguments for a topic, optionally filtered by side."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if side and side in ['pro', 'con']:
        cursor.execute(
            "SELECT * FROM arguments WHERE topic_id = %s AND side = %s ORDER BY created_at ASC",
            (topic_id, side)
        )
    else:
        cursor.execute(
            "SELECT * FROM arguments WHERE topic_id = %s ORDER BY created_at ASC",
            (topic_id,)
        )
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    arguments = [dict(row) for row in rows]
    # Convert datetime to ISO string for each argument
    for arg in arguments:
        arg['created_at'] = _format_datetime_to_iso(arg.get('created_at'))
        arg['validity_checked_at'] = _format_datetime_to_iso(arg.get('validity_checked_at'))
    return arguments

def get_argument_counts(topic_id: int) -> dict:
    """Get pro and con argument counts for a topic."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN side = 'pro' THEN 1 END) as pro_count,
            COUNT(CASE WHEN side = 'con' THEN 1 END) as con_count
        FROM arguments
        WHERE topic_id = %s
    """, (topic_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else {'pro_count': 0, 'con_count': 0}

def update_topic_analysis(topic_id: int, overall_summary: str, consensus_view: str, timeline_view: list):
    """Update topic with generated analysis."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timeline_json = json.dumps(timeline_view) if timeline_view else None
    cursor.execute(
        """UPDATE topics 
           SET overall_summary = %s, consensus_view = %s, timeline_view = %s
           WHERE id = %s""",
        (overall_summary, consensus_view, timeline_json, topic_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def migrate_add_validity_columns():
    """Add validity-related columns to arguments table if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if columns exist using PostgreSQL information_schema
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'arguments' AND table_schema = 'public'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        # Add columns if they don't exist
        if 'validity_score' not in columns:
            cursor.execute("ALTER TABLE arguments ADD COLUMN validity_score INTEGER")
        if 'validity_reasoning' not in columns:
            cursor.execute("ALTER TABLE arguments ADD COLUMN validity_reasoning TEXT")
        if 'validity_checked_at' not in columns:
            cursor.execute("ALTER TABLE arguments ADD COLUMN validity_checked_at TIMESTAMP")
        if 'key_urls' not in columns:
            cursor.execute("ALTER TABLE arguments ADD COLUMN key_urls TEXT")
        
        conn.commit()
    except Exception as e:
        # If error occurs, rollback
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def migrate_add_votes_column():
    """Add votes column to arguments table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'arguments' AND table_schema = 'public'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        if 'votes' not in columns:
            cursor.execute("ALTER TABLE arguments ADD COLUMN votes INTEGER DEFAULT 0")
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def get_argument(argument_id: int) -> Optional[dict]:
    """Get a single argument by ID."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM arguments WHERE id = %s", (argument_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if row:
        arg = dict(row)
        # Parse key_urls JSON if it exists
        if arg.get('key_urls'):
            try:
                arg['key_urls'] = json.loads(arg['key_urls'])
            except (json.JSONDecodeError, TypeError):
                arg['key_urls'] = []
        else:
            arg['key_urls'] = []
        # Convert datetime fields to ISO strings
        arg['created_at'] = _format_datetime_to_iso(arg.get('created_at'))
        arg['validity_checked_at'] = _format_datetime_to_iso(arg.get('validity_checked_at'))
        return arg
    return None

def update_argument(argument_id: int, title: str, content: str, sources: Optional[str] = None):
    """Update an argument's title, content, and sources."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE arguments 
           SET title = %s, content = %s, sources = %s
           WHERE id = %s""",
        (title, content, sources, argument_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def update_argument_validity(argument_id: int, validity_score: int, validity_reasoning: str, key_urls: Optional[List[str]] = None):
    """Update argument validity fields."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Convert key_urls list to JSON string
    key_urls_json = json.dumps(key_urls) if key_urls else None
    
    cursor.execute(
        """UPDATE arguments 
           SET validity_score = %s, validity_reasoning = %s, validity_checked_at = %s, key_urls = %s
           WHERE id = %s""",
        (validity_score, validity_reasoning, datetime.now(timezone.utc), key_urls_json, argument_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_arguments_sorted_by_validity(topic_id: int, side: Optional[str] = None) -> list:
    """Get arguments sorted by validity score (highest first, unverified at end)."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if side and side in ['pro', 'con']:
        cursor.execute("""
            SELECT * FROM arguments 
            WHERE topic_id = %s AND side = %s
            ORDER BY 
                CASE WHEN validity_score IS NULL THEN 1 ELSE 0 END,
                validity_score DESC,
                created_at DESC
        """, (topic_id, side))
    else:
        cursor.execute("""
            SELECT * FROM arguments 
            WHERE topic_id = %s
            ORDER BY 
                CASE WHEN validity_score IS NULL THEN 1 ELSE 0 END,
                validity_score DESC,
                created_at DESC
        """, (topic_id,))
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    arguments = [dict(row) for row in rows]
    # Parse key_urls JSON and convert timestamps for each argument
    for arg in arguments:
        if arg.get('key_urls'):
            try:
                arg['key_urls'] = json.loads(arg['key_urls'])
            except (json.JSONDecodeError, TypeError):
                arg['key_urls'] = []
        else:
            arg['key_urls'] = []
        # Convert datetime fields to ISO strings
        arg['created_at'] = _format_datetime_to_iso(arg.get('created_at'))
        arg['validity_checked_at'] = _format_datetime_to_iso(arg.get('validity_checked_at'))
    
    return arguments

def get_argument_matches(topic_id: int) -> list:
    """Get persisted argument matches for a topic."""
    ensure_argument_matches_table()
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT pro_id, con_id, reason FROM argument_matches WHERE topic_id = %s",
        (topic_id,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(row) for row in rows]

def save_argument_matches(topic_id: int, matches: list):
    """Save argument matches to database."""
    ensure_argument_matches_table()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing matches for this topic
    cursor.execute("DELETE FROM argument_matches WHERE topic_id = %s", (topic_id,))
    
    # Insert new matches
    for match in matches:
        cursor.execute(
            """INSERT INTO argument_matches (topic_id, pro_id, con_id, reason)
               VALUES (%s, %s, %s, %s)""",
            (topic_id, match['pro_id'], match['con_id'], match.get('reason'))
        )
    
    conn.commit()
    cursor.close()
    conn.close()

def delete_argument_matches_for_topic(topic_id: int):
    """Delete all argument matches for a topic."""
    ensure_argument_matches_table()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM argument_matches WHERE topic_id = %s", (topic_id,))
    conn.commit()
    cursor.close()
    conn.close()

def upvote_argument(argument_id: int) -> int:
    """Increment vote count for an argument and return new count."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE arguments SET votes = votes + 1 WHERE id = %s RETURNING votes",
        (argument_id,)
    )
    result = cursor.fetchone()
    votes = result[0] if result else 0
    
    conn.commit()
    cursor.close()
    conn.close()
    return votes

def downvote_argument(argument_id: int) -> int:
    """Decrement vote count for an argument and return new count."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE arguments SET votes = votes - 1 WHERE id = %s RETURNING votes",
        (argument_id,)
    )
    result = cursor.fetchone()
    votes = result[0] if result else 0
    
    conn.commit()
    cursor.close()
    conn.close()
    return votes
