#!/usr/bin/env python3
"""
Script to clear all data from the debate platform database.
This will delete all topics, arguments, and argument_matches.
"""

import sys
import os

# Add backend directory to path so we can import database module
sys.path.insert(0, os.path.dirname(__file__))

import database

def clear_database():
    """Clear all data from the database tables."""
    
    print("Connecting to database...")
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("Deleting all data from tables...")
        
        # Delete in order to respect foreign key constraints
        # argument_matches references topics (CASCADE will handle it, but explicit is clearer)
        cursor.execute("DELETE FROM argument_matches")
        print("  - Cleared argument_matches table")
        
        # arguments references topics (CASCADE will handle it)
        cursor.execute("DELETE FROM arguments")
        print("  - Cleared arguments table")
        
        # topics is the parent table
        cursor.execute("DELETE FROM topics")
        print("  - Cleared topics table")
        
        # Reset sequences (auto-increment counters) to start from 1
        cursor.execute("ALTER SEQUENCE topics_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE arguments_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE argument_matches_id_seq RESTART WITH 1")
        print("  - Reset auto-increment sequences")
        
        conn.commit()
        print("\n✅ Database cleared successfully!")
        print("All topics, arguments, and matches have been deleted.")
        print("Auto-increment IDs will start from 1 for new entries.")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error clearing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Confirm before proceeding
    response = input("⚠️  This will delete ALL data from the database. Are you sure? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        clear_database()
    else:
        print("Operation cancelled.")

