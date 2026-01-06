#!/usr/bin/env python3
"""
Database layer for storing content and geo-restriction data
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path


class ContentDatabase:
    """SQLite database for content and geo-restriction data (multi-platform)"""
    
    def __init__(self, db_path: str = "platforms/primeran/primeran_content.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._migrate_add_platform()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Main content table
        # Platform is stored as JSON array: ["primeran.eus", "makusi.eus"]
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                platform TEXT NOT NULL DEFAULT '["primeran.eus"]',
                title TEXT,
                type TEXT NOT NULL,  -- 'movie', 'episode', 'documentary', 'concert', etc.
                duration INTEGER,  -- Duration in seconds
                year INTEGER,
                genres TEXT,  -- JSON array
                series_slug TEXT,  -- For episodes, the parent series slug
                series_title TEXT,  -- For episodes, the parent series title
                season_number INTEGER,  -- For episodes
                episode_number INTEGER,  -- For episodes
                is_geo_restricted BOOLEAN,
                restriction_type TEXT,  -- 'manifest_403', 'manifest_404', etc.
                last_checked TIMESTAMP,
                metadata TEXT,  -- JSON blob with full API response
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check history for tracking changes over time
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                was_restricted BOOLEAN,
                status_code INTEGER,
                method_used TEXT,
                error TEXT,
                FOREIGN KEY (slug) REFERENCES content(slug)
            )
        """)
        
        # Indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_type ON content(type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_geo_restricted ON content(is_geo_restricted)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_series_slug ON content(series_slug)
        """)
        # Note: Platform index on JSON array is less efficient, but we can still create it
        # Queries will use json_each() for filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_platform ON content(platform)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_check_history_slug ON check_history(slug)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_check_history_checked_at ON check_history(checked_at)
        """)
        
        self.conn.commit()
    
    def _migrate_add_platform(self):
        """
        Migrate existing database to add platform column.
        This is safe to run multiple times - it checks if migration is needed.
        """
        cursor = self.conn.cursor()
        
        # Check if platform column exists
        cursor.execute("PRAGMA table_info(content)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'platform' not in columns:
            print("Migrating database: Adding platform column...")
            
            # Add platform column with default value
            cursor.execute("""
                ALTER TABLE content 
                ADD COLUMN platform TEXT NOT NULL DEFAULT 'primeran.eus'
            """)
            
            # Update all existing records to have platform = 'primeran.eus'
            cursor.execute("""
                UPDATE content 
                SET platform = 'primeran.eus' 
                WHERE platform IS NULL OR platform = ''
            """)
            
            # Drop old unique constraint on slug (if it exists as a separate constraint)
            # SQLite doesn't support DROP CONSTRAINT directly, so we need to recreate the table
            # However, since we're using UNIQUE in CREATE TABLE, we'll handle this differently
            # For existing databases, we'll need to recreate the table
            
            # Check if we need to recreate table for unique constraint
            # SQLite doesn't enforce UNIQUE constraints added via ALTER TABLE the same way
            # So we'll create a new table with the proper constraint and migrate data
            try:
                # Create new table with composite unique constraint
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
                
                # Copy data from old table
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
                
                # Drop old table
                cursor.execute("DROP TABLE content")
                
                # Rename new table
                cursor.execute("ALTER TABLE content_new RENAME TO content")
                
                # Recreate indexes
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
                
                print("  ✓ Migration complete: Added platform column and composite unique constraint")
            except sqlite3.OperationalError as e:
                # If table recreation fails, at least we have the platform column
                print(f"  ⚠️  Migration partially complete: {e}")
                print("  Note: Unique constraint may need manual update")
            
            self.conn.commit()
        else:
            # Platform column exists, but check if we need to set defaults
            cursor.execute("SELECT COUNT(*) FROM content WHERE platform IS NULL OR platform = ''")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                print(f"Migrating database: Setting platform for {null_count} records...")
                cursor.execute("""
                    UPDATE content 
                    SET platform = 'primeran.eus' 
                    WHERE platform IS NULL OR platform = ''
                """)
                self.conn.commit()
                print("  ✓ Migration complete: Set platform for existing records")
    
    def upsert_content(self, content_data: Dict[str, Any]) -> int:
        """
        Insert or update content record
        
        Args:
            content_data: Dictionary with content information
                - 'platform' can be a string (single platform) or list (multiple platforms)
                - If slug exists, platforms will be merged
            
        Returns:
            Content ID
        """
        cursor = self.conn.cursor()
        
        # Prepare data
        slug = content_data['slug']
        new_platform = content_data.get('platform', 'primeran.eus')
        title = content_data.get('title')
        content_type = content_data.get('type', 'unknown')
        duration = content_data.get('duration')
        year = content_data.get('year')
        genres = json.dumps(content_data.get('genres', [])) if content_data.get('genres') else None
        series_slug = content_data.get('series_slug')
        series_title = content_data.get('series_title')
        season_number = content_data.get('season_number')
        episode_number = content_data.get('episode_number')
        is_geo_restricted = content_data.get('is_geo_restricted')
        restriction_type = content_data.get('restriction_type')
        metadata = content_data.get('metadata', {})
        last_checked = datetime.now().isoformat()
        
        # Normalize platform to JSON array
        # Convert string to list if needed
        def normalize_platform_name(platform_name: str) -> str:
            """
            Normalize platform name to always use .eus suffix.
            Examples: 'makusi' -> 'makusi.eus', 'primeran' -> 'primeran.eus'
            """
            if not platform_name:
                return 'primeran.eus'
            # If it already has .eus, return as is
            if platform_name.endswith('.eus'):
                return platform_name
            # Otherwise, add .eus suffix
            return f'{platform_name}.eus'
        
        if isinstance(new_platform, str):
            # Check if it's already JSON
            try:
                new_platform_list = json.loads(new_platform)
                if not isinstance(new_platform_list, list):
                    new_platform_list = [normalize_platform_name(new_platform_list)]
                else:
                    # Normalize all platform names in the list
                    new_platform_list = [normalize_platform_name(p) for p in new_platform_list]
            except (json.JSONDecodeError, TypeError):
                # Plain string, convert to list and normalize
                new_platform_list = [normalize_platform_name(new_platform)]
        elif isinstance(new_platform, list):
            # Normalize all platform names in the list
            new_platform_list = [normalize_platform_name(p) for p in new_platform_list]
        else:
            new_platform_list = ['primeran.eus']
        
        # Check if content with this slug already exists
        cursor.execute("SELECT platform, metadata FROM content WHERE slug = ?", (slug,))
        existing = cursor.fetchone()
        
        if existing:
            # Merge platforms: combine existing and new, remove duplicates
            existing_platform = existing['platform']
            try:
                existing_platform_list = json.loads(existing_platform) if isinstance(existing_platform, str) else existing_platform
                if not isinstance(existing_platform_list, list):
                    existing_platform_list = [existing_platform_list] if existing_platform_list else []
            except (json.JSONDecodeError, TypeError):
                existing_platform_list = [existing_platform] if existing_platform else []
            
            # Normalize existing platform names (in case old data has 'makusi' instead of 'makusi.eus')
            existing_platform_list = [normalize_platform_name(p) for p in existing_platform_list]
            
            # Merge platforms, preserving order, removing duplicates
            merged_platforms = list(dict.fromkeys(existing_platform_list + new_platform_list))
            platform_json = json.dumps(merged_platforms)
            
            # Merge metadata if needed (store platform-specific URLs)
            existing_metadata = json.loads(existing['metadata']) if existing['metadata'] else {}
            if isinstance(metadata, dict):
                # Store platform-specific URLs in metadata
                if 'platform_urls' not in metadata:
                    metadata['platform_urls'] = {}
                # Merge with existing platform_urls
                if 'platform_urls' in existing_metadata:
                    metadata['platform_urls'].update(existing_metadata.get('platform_urls', {}))
                # Merge other metadata (new takes precedence for non-platform_urls)
                merged_metadata = {**existing_metadata, **metadata}
                merged_metadata['platform_urls'] = metadata.get('platform_urls', existing_metadata.get('platform_urls', {}))
            else:
                merged_metadata = existing_metadata
        else:
            # New content, use new platform list
            platform_json = json.dumps(new_platform_list)
            merged_metadata = metadata if isinstance(metadata, dict) else {}
        
        # Serialize metadata
        metadata_json = json.dumps(merged_metadata)
        
        cursor.execute("""
            INSERT INTO content (
                slug, platform, title, type, duration, year, genres,
                series_slug, series_title, season_number, episode_number,
                is_geo_restricted, restriction_type, last_checked, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                platform = excluded.platform,
                title = COALESCE(excluded.title, title),
                type = excluded.type,
                duration = COALESCE(excluded.duration, duration),
                year = COALESCE(excluded.year, year),
                genres = COALESCE(excluded.genres, genres),
                series_slug = COALESCE(excluded.series_slug, series_slug),
                series_title = COALESCE(excluded.series_title, series_title),
                season_number = COALESCE(excluded.season_number, season_number),
                episode_number = COALESCE(excluded.episode_number, episode_number),
                is_geo_restricted = excluded.is_geo_restricted,
                restriction_type = excluded.restriction_type,
                last_checked = excluded.last_checked,
                metadata = excluded.metadata,
                updated_at = CURRENT_TIMESTAMP
        """, (
            slug, platform_json, title, content_type, duration, year, genres,
            series_slug, series_title, season_number, episode_number,
            is_geo_restricted, restriction_type, last_checked, metadata_json
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_content_status(self, slug: str, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get existing content's geo-restriction status
        
        Args:
            slug: Content slug
            platform: Platform name (optional, if None checks any platform)
            
        Returns:
            Dictionary with is_geo_restricted and restriction_type, or None if not found
        """
        cursor = self.conn.cursor()
        if platform:
            # Check if platform is in the JSON array
            cursor.execute("""
                SELECT is_geo_restricted, restriction_type 
                FROM content 
                WHERE slug = ? AND EXISTS (SELECT 1 FROM json_each(platform) WHERE value = ?)
            """, (slug, platform))
        else:
        cursor.execute("""
            SELECT is_geo_restricted, restriction_type 
            FROM content 
            WHERE slug = ?
                LIMIT 1
        """, (slug,))
        row = cursor.fetchone()
        if row:
            return {
                'is_geo_restricted': row['is_geo_restricted'],
                'restriction_type': row['restriction_type']
            }
        return None
    
    def add_check_history(self, slug: str, check_result: Dict[str, Any]):
        """
        Add a check history record
        
        Args:
            slug: Content slug
            check_result: Result from geo-restriction check
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO check_history (
                slug, was_restricted, status_code, method_used, error
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            slug,
            check_result.get('is_geo_restricted'),
            check_result.get('status_code'),
            'manifest_check',
            check_result.get('error')
        ))
        
        self.conn.commit()
    
    def get_content(self, slug: str, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get content by slug
        
        Args:
            slug: Content slug
            platform: Platform name (optional, if None returns first match)
            
        Returns:
            Content dictionary or None if not found
        """
        cursor = self.conn.cursor()
        if platform:
            # Check if platform is in the JSON array
            cursor.execute("""
                SELECT * FROM content 
                WHERE slug = ? AND EXISTS (SELECT 1 FROM json_each(platform) WHERE value = ?)
            """, (slug, platform))
        else:
            cursor.execute("SELECT * FROM content WHERE slug = ? LIMIT 1", (slug,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_content_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get content by slug (alias for get_content without platform)
        
        Args:
            slug: Content slug
            
        Returns:
            Content dictionary or None if not found
        """
        return self.get_content(slug)
    
    def get_all_content(self, 
                       content_type: Optional[str] = None,
                       geo_restricted_only: bool = False,
                       platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all content with optional filters
        
        Args:
            content_type: Filter by type (e.g., 'episode', 'movie')
            geo_restricted_only: Only return geo-restricted content
            platform: Filter by platform (e.g., 'primeran.eus', 'makusi.eus')
            
        Returns:
            List of content dictionaries
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM content WHERE 1=1"
        params = []
        
        if content_type:
            query += " AND type = ?"
            params.append(content_type)
        
        if geo_restricted_only:
            query += " AND is_geo_restricted = 1"
        
        if platform:
            # Filter by platform in JSON array
            query += " AND EXISTS (SELECT 1 FROM json_each(platform) WHERE value = ?)"
            params.append(platform)
        
        query += " ORDER BY title"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_statistics(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """
        Get database statistics
        
        Args:
            platform: Filter statistics by platform (optional)
        
        Returns:
            Dictionary with statistics
        """
        cursor = self.conn.cursor()
        
        stats = {}
        where_clause = ""
        params = []
        
        if platform:
            # Filter by platform in JSON array
            where_clause = " WHERE EXISTS (SELECT 1 FROM json_each(platform) WHERE value = ?)"
            params = [platform]
        
        # Total content
        cursor.execute(f"SELECT COUNT(*) FROM content{where_clause}", params)
        stats['total_content'] = cursor.fetchone()[0]
        
        # By type
        cursor.execute(f"""
            SELECT type, COUNT(*) as count 
            FROM content 
            {where_clause}
            GROUP BY type
        """, params)
        stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By platform - extract platforms from JSON arrays
        cursor.execute("""
            SELECT json_each.value as platform, COUNT(*) as count
            FROM content, json_each(content.platform)
            GROUP BY json_each.value
        """)
        stats['by_platform'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Geo-restricted
        geo_where = "WHERE is_geo_restricted = 1" if not where_clause else f"{where_clause} AND is_geo_restricted = 1"
        cursor.execute(f"SELECT COUNT(*) FROM content {geo_where}", params)
        stats['geo_restricted_count'] = cursor.fetchone()[0]
        
        accessible_where = "WHERE is_geo_restricted = 0" if not where_clause else f"{where_clause} AND is_geo_restricted = 0"
        cursor.execute(f"SELECT COUNT(*) FROM content {accessible_where}", params)
        stats['accessible_count'] = cursor.fetchone()[0]
        
        unknown_where = "WHERE is_geo_restricted IS NULL" if not where_clause else f"{where_clause} AND is_geo_restricted IS NULL"
        cursor.execute(f"SELECT COUNT(*) FROM content {unknown_where}", params)
        stats['unknown_count'] = cursor.fetchone()[0]
        
        # Percentage
        if stats['total_content'] > 0:
            stats['geo_restricted_percentage'] = (
                stats['geo_restricted_count'] / stats['total_content'] * 100
            )
        else:
            stats['geo_restricted_percentage'] = 0
        
        # Last check
        cursor.execute(f"SELECT MAX(last_checked) FROM content{where_clause}", params)
        stats['last_check'] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.conn.close()
