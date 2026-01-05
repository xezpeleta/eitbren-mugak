#!/usr/bin/env python3
"""
JSON exporter for static website

Exports database content to JSON format for the static website.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from .database import ContentDatabase


class JSONExporter:
    """Export content data to JSON for static website"""
    
    def __init__(self, db: ContentDatabase, output_dir: str = "docs/data"):
        """
        Initialize exporter
        
        Args:
            db: ContentDatabase instance
            output_dir: Output directory for JSON files
        """
        self.db = db
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _extract_from_metadata(self, item: Dict[str, Any], path: str, default: Any = None) -> Any:
        """
        Safely extract a value from metadata JSON using dot notation path
        
        Args:
            item: Content item dictionary
            path: Dot notation path (e.g., 'images[0].file', 'age_rating.label')
            default: Default value if path not found
            
        Returns:
            Extracted value or default
        """
        try:
            metadata_str = item.get('metadata')
            if not metadata_str:
                return default
            
            metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
            
            # Handle array access like images[0].file
            if '[' in path:
                parts = path.split('[')
                key = parts[0]
                array_part = parts[1].split(']')[0]
                rest = ']'.join(parts[1].split(']')[1:]).lstrip('.')
                
                if key in metadata and isinstance(metadata[key], list):
                    idx = int(array_part)
                    if 0 <= idx < len(metadata[key]):
                        value = metadata[key][idx]
                        if rest:
                            # Continue with nested path
                            for part in rest.split('.'):
                                if part:
                                    value = value.get(part) if isinstance(value, dict) else None
                                    if value is None:
                                        return default
                        return value
            else:
                # Simple dot notation path
                value = metadata
                for part in path.split('.'):
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return default
                    if value is None:
                        return default
                return value
        except (json.JSONDecodeError, KeyError, IndexError, ValueError, TypeError):
            return default
    
    def _extract_languages(self, item: Dict[str, Any]) -> list:
        """
        Extract available languages from metadata
        
        Args:
            item: Content item dictionary
            
        Returns:
            List of language codes
        """
        try:
            metadata_str = item.get('metadata')
            if not metadata_str:
                return []
            
            metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
            
            languages = []
            
            # Try audios array
            if 'audios' in metadata and isinstance(metadata['audios'], list):
                for audio in metadata['audios']:
                    if isinstance(audio, dict):
                        code = audio.get('code')
                        if code:
                            languages.append(code)
            
            # If no audios, try subtitle languages
            if not languages and 'subtitle' in metadata and isinstance(metadata['subtitle'], list):
                for sub in metadata['subtitle']:
                    if isinstance(sub, dict) and 'language' in sub:
                        lang = sub['language']
                        if isinstance(lang, dict):
                            code = lang.get('code')
                            if code and code not in languages:
                                languages.append(code)
            
            return sorted(list(set(languages)))  # Remove duplicates and sort
        except (json.JSONDecodeError, KeyError, TypeError):
            return []
    
    def _get_content_url(self, item: Dict[str, Any]) -> str:
        """
        Generate content URL based on platform and content type
        
        Args:
            item: Content item dictionary
            
        Returns:
            Content URL
        """
        platform = item.get('platform', 'primeran.eus')
        slug = item['slug']
        content_type = item.get('type', '')
        
        if platform == 'makusi.eus':
            # Makusi uses /ikusi/m/ for media and /ikusi/s/ for series
            # For episodes, we use the episode slug which should work with /ikusi/w/
            if content_type == 'episode':
                return f"https://makusi.eus/ikusi/w/{slug}"
            elif 'series' in content_type.lower() or item.get('series_slug'):
                # If it's part of a series, check if it's the series itself or an episode
                if item.get('series_slug') and item.get('series_slug') != slug:
                    # It's an episode
                    return f"https://makusi.eus/ikusi/w/{slug}"
                else:
                    # It's a series
                    return f"https://makusi.eus/ikusi/s/{slug}"
            else:
                # Regular media
                return f"https://makusi.eus/ikusi/m/{slug}"
        else:
            # Primeran uses /m/ for all content
            return f"https://primeran.eus/m/{slug}"
    
    def export_all(self) -> Dict[str, Any]:
        """
        Export all content to JSON
        
        Returns:
            Dictionary with export metadata
        """
        print("Exporting content to JSON...")
        
        # Get all content
        all_content = self.db.get_all_content()
        
        # Get statistics
        stats = self.db.get_statistics()
        
        # Prepare export data
        export_data = {
            'export_date': datetime.now().isoformat(),
            'statistics': stats,
            'content': []
        }
        
        # Add content items
        for item in all_content:
            # Convert to JSON-serializable format
            content_item = {
                'slug': item['slug'],
                'title': item['title'],
                'type': item['type'],
                'duration': item['duration'],
                'year': item['year'],
                'genres': json.loads(item['genres']) if item['genres'] else [],
                'series_slug': item['series_slug'],
                'series_title': item['series_title'],
                'season_number': item['season_number'],
                'episode_number': item['episode_number'],
                'is_geo_restricted': bool(item['is_geo_restricted']) if item['is_geo_restricted'] is not None else None,
                'restriction_type': item['restriction_type'],
                'last_checked': item['last_checked'],
                
                # High priority metadata
                'description': self._extract_from_metadata(item, 'description'),
                'thumbnail': self._extract_from_metadata(item, 'images[0].file'),
                'age_rating': self._extract_from_metadata(item, 'age_rating.label') or self._extract_from_metadata(item, 'age_rating.age'),
                'access_restriction': self._extract_from_metadata(item, 'access_restriction'),
                
                # Medium priority metadata
                'available_until': self._extract_from_metadata(item, 'available_until'),
                'languages': self._extract_languages(item),
                'platform': item.get('platform', 'primeran.eus'),
                'content_url': self._get_content_url(item)
            }
            export_data['content'].append(content_item)
        
        # Write to file
        output_file = self.output_dir / "content.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(all_content)} items to {output_file}")
        
        return {
            'file': str(output_file),
            'items_exported': len(all_content),
            'export_date': export_data['export_date']
        }
    
    def export_statistics_only(self) -> Dict[str, Any]:
        """
        Export only statistics (lighter file for dashboard)
        
        Returns:
            Dictionary with statistics
        """
        stats = self.db.get_statistics()
        
        stats_data = {
            'export_date': datetime.now().isoformat(),
            'statistics': stats
        }
        
        output_file = self.output_dir / "statistics.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported statistics to {output_file}")
        
        return stats_data
    
    def export_geo_restricted_only(self) -> Dict[str, Any]:
        """
        Export only geo-restricted content
        
        Returns:
            Dictionary with geo-restricted content
        """
        geo_restricted = self.db.get_all_content(geo_restricted_only=True)
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'count': len(geo_restricted),
            'content': []
        }
        
        for item in geo_restricted:
            content_item = {
                'slug': item['slug'],
                'title': item['title'],
                'type': item['type'],
                'series_title': item['series_title'],
                'season_number': item['season_number'],
                'episode_number': item['episode_number'],
                'last_checked': item['last_checked'],
                
                # Add metadata fields for geo-restricted content too
                'description': self._extract_from_metadata(item, 'description'),
                'thumbnail': self._extract_from_metadata(item, 'images[0].file'),
                'age_rating': self._extract_from_metadata(item, 'age_rating.label') or self._extract_from_metadata(item, 'age_rating.age'),
                'access_restriction': self._extract_from_metadata(item, 'access_restriction'),
                'available_until': self._extract_from_metadata(item, 'available_until'),
                'languages': self._extract_languages(item),
                'platform': item.get('platform', 'primeran.eus'),
                'content_url': self._get_content_url(item)
            }
            export_data['content'].append(content_item)
        
        output_file = self.output_dir / "geo-restricted.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(geo_restricted)} geo-restricted items to {output_file}")
        
        return export_data
