#!/usr/bin/env python3
"""
Database migration script: Add platform column to content table

This script migrates existing databases to support multiple platforms by:
1. Adding a 'platform' column to the content table
2. Setting all existing records to platform = 'primeran.eus'
3. Updating the unique constraint to be composite (slug, platform)

Usage:
    python migrate_add_platform.py [--db PATH]
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str) -> bool:
    """
    Migrate database to add platform column
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        True if migration successful, False otherwise
    """
    if not Path(db_path).exists():
        print(f"✗ Database file not found: {db_path}")
        return False
    
    print(f"Migrating database: {db_path}")
    print("=" * 80)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if platform column exists
        cursor.execute("PRAGMA table_info(content)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'platform' in columns:
            print("✓ Platform column already exists")
            
            # Check if any records have NULL platform
            cursor.execute("SELECT COUNT(*) FROM content WHERE platform IS NULL OR platform = ''")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"  Updating {null_count} records with NULL platform...")
                cursor.execute("""
                    UPDATE content 
                    SET platform = 'primeran.eus' 
                    WHERE platform IS NULL OR platform = ''
                """)
                conn.commit()
                print(f"  ✓ Updated {null_count} records")
            else:
                print("  ✓ All records have platform set")
            
            # Check unique constraint
            cursor.execute("PRAGMA index_list(content)")
            indexes = [row[1] for row in cursor.fetchall()]
            
            # Check if we have the composite unique constraint
            # SQLite stores UNIQUE constraints as indexes
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='content'
            """)
            table_sql = cursor.fetchone()[0]
            
            if 'UNIQUE(slug, platform)' in table_sql or 'UNIQUE(platform, slug)' in table_sql:
                print("  ✓ Composite unique constraint (slug, platform) exists")
            else:
                print("  ⚠️  Composite unique constraint may not be properly set")
                print("     This is OK if the table was created with the new schema")
            
            conn.close()
            return True
        
        # Migration needed
        print("  Adding platform column...")
        
        # Step 1: Add platform column
        cursor.execute("""
            ALTER TABLE content 
            ADD COLUMN platform TEXT NOT NULL DEFAULT 'primeran.eus'
        """)
        print("  ✓ Added platform column")
        
        # Step 2: Update existing records
        cursor.execute("""
            UPDATE content 
            SET platform = 'primeran.eus' 
            WHERE platform IS NULL OR platform = ''
        """)
        updated = cursor.rowcount
        print(f"  ✓ Set platform for {updated} existing records")
        
        # Step 3: Recreate table with composite unique constraint
        print("  Recreating table with composite unique constraint...")
        
        # Create new table
        cursor.execute("""
            CREATE TABLE content_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                platform TEXT NOT NULL DEFAULT 'primeran.eus',
                title TEXT,
                type TEXT NOT NULL,
                duration INTEGER,
                year INTEGER,
                genres TEXT,
                series_slug TEXT,
                series_title TEXT,
                season_number INTEGER,
                episode_number INTEGER,
                is_geo_restricted BOOLEAN,
                restriction_type TEXT,
                last_checked TIMESTAMP,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(slug, platform)
            )
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO content_new 
            SELECT 
                id, slug, 
                COALESCE(platform, 'primeran.eus') as platform,
                title, type, duration, year, genres,
                series_slug, series_title, season_number, episode_number,
                is_geo_restricted, restriction_type, last_checked, metadata,
                created_at, updated_at
            FROM content
        """)
        copied = cursor.rowcount
        print(f"  ✓ Copied {copied} records to new table")
        
        # Drop old table
        cursor.execute("DROP TABLE content")
        
        # Rename new table
        cursor.execute("ALTER TABLE content_new RENAME TO content")
        print("  ✓ Replaced old table with new table")
        
        # Recreate indexes
        print("  Recreating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_type ON content(type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_geo_restricted ON content(is_geo_restricted)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_series_slug ON content(series_slug)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_platform ON content(platform)
        """)
        print("  ✓ Recreated indexes")
        
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 80)
        print("✓ Migration completed successfully!")
        print("=" * 80)
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Migrate database to add platform column'
    )
    parser.add_argument(
        '--db',
        default='platforms/primeran/primeran_content.db',
        help='Path to database file (default: platforms/primeran/primeran_content.db)'
    )
    
    args = parser.parse_args()
    
    success = migrate_database(args.db)
    
    if success:
        print("\n✓ Migration script completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
