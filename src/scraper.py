#!/usr/bin/env python3
"""
Content scraper for EITB platforms (Primeran, Makusi, etc.)

Discovers all content and checks for geo-restrictions.
"""

import time
import requests
from typing import List, Dict, Any, Set, Optional, Union
from .primeran_api import PrimeranAPI
from .makusi_api import MakusiAPI
from .database import ContentDatabase


class ContentScraper:
    """Scraper for discovering and checking content from EITB platforms"""
    
    def __init__(self, api: Union[PrimeranAPI, MakusiAPI], db: ContentDatabase, delay: float = 0.5, disable_geo_check: bool = False):
        """
        Initialize scraper
        
        Args:
            api: API instance (PrimeranAPI or MakusiAPI)
            db: ContentDatabase instance
            delay: Delay between requests in seconds (to avoid rate limiting)
            disable_geo_check: If True, skip geo-restriction checks (useful when using VPN to update metadata)
        """
        self.api = api
        self.db = db
        self.delay = delay
        self.disable_geo_check = disable_geo_check
        self.platform = api.platform  # Get platform from API object
        self.discovered_slugs: Set[str] = set()
        self.stats = {
            'total_discovered': 0,
            'total_checked': 0,
            'geo_restricted': 0,
            'accessible': 0,
            'errors': 0
        }
    
    def _generate_platform_url(self, slug: str, content_type: str, series_slug: Optional[str] = None) -> str:
        """
        Generate platform-specific URL for content
        
        Args:
            slug: Content slug
            content_type: Content type (e.g., 'episode', 'vod')
            series_slug: Series slug if episode
            
        Returns:
            Platform-specific content URL
        """
        if self.platform == 'makusi.eus':
            if content_type == 'episode' or series_slug:
                return f"https://makusi.eus/ikusi/w/{slug}"
            elif 'series' in content_type.lower():
                return f"https://makusi.eus/ikusi/s/{slug}"
            else:
                return f"https://makusi.eus/ikusi/m/{slug}"
        else:
            # Primeran uses /m/ for all content
            return f"https://primeran.eus/m/{slug}"
    
    def _add_platform_url_to_metadata(self, metadata: Dict[str, Any], slug: str, content_type: str, series_slug: Optional[str] = None) -> Dict[str, Any]:
        """
        Add platform-specific URL to metadata
        
        Args:
            metadata: Metadata dictionary
            slug: Content slug
            content_type: Content type
            series_slug: Series slug if episode
            
        Returns:
            Updated metadata dictionary
        """
        if not isinstance(metadata, dict):
            metadata = {}
        
        # Initialize platform_urls if not exists
        if 'platform_urls' not in metadata:
            metadata['platform_urls'] = {}
        
        # Add URL for current platform
        url = self._generate_platform_url(slug, content_type, series_slug)
        metadata['platform_urls'][self.platform] = url
        
        return metadata
    
    def _sleep(self):
        """Sleep to avoid rate limiting"""
        if self.delay > 0:
            time.sleep(self.delay)
    
    def discover_content_from_home(self) -> List[Dict[str, Any]]:
        """
        Discover content from home page
        
        Returns:
            List of content items found
        """
        print("Discovering content from home page...")
        home_data = self.api.get_home_content()
        
        content_items = []
        
        # Parse home page structure to find content
        # This will depend on the actual structure of /api/v1/home
        # For now, we'll need to explore the structure
        
        return content_items
    
    def _extract_slugs_from_children(self, children: List[Dict], slugs: Set[str], series_slugs: Set[str]):
        """
        Recursively extract slugs from children structure
        
        Args:
            children: List of child items
            slugs: Set to add media slugs to
            series_slugs: Set to add series slugs to
        """
        for child in children:
            # Check if this is a content item with slug
            if 'slug' in child:
                slug = child['slug']
                media_type = child.get('media_type', '').lower()
                collection = child.get('collection', '').lower()
                
                # Determine if it's a series or media
                if media_type == 'series' or collection == 'series' or 'series' in str(child.get('series', '')).lower():
                    series_slugs.add(slug)
                else:
                    slugs.add(slug)
            
            # Recursively check nested children
            if 'children' in child:
                self._extract_slugs_from_children(child['children'], slugs, series_slugs)
            if 'menu_links' in child:
                self._extract_slugs_from_children(child['menu_links'], slugs, series_slugs)
    
    def discover_media_from_sections(self) -> List[str]:
        """
        Discover media slugs from various sections
        
        Returns:
            List of media slugs
        """
        print("Discovering media from sections...")
        slugs = set()
        
        try:
            # Method 1: Use search API with empty query to get all content (Primeran only)
            if self.platform == 'primeran.eus':
            try:
                response = self.api.session.get('https://primeran.eus/api/v1/search?q=')
                if response.status_code == 200:
                    search_data = response.json()
                    self._sleep()
                    if 'data' in search_data and isinstance(search_data['data'], list):
                        for item in search_data['data']:
                            if 'slug' in item:
                                media_type = item.get('media_type', '').lower()
                                collection = item.get('collection', '').lower()
                                # Only include actual media items (not pages, collections, etc.)
                                if media_type != 'series' and collection in ['media', 'vod', 'movie', 'documentary', 'concert']:
                                    slugs.add(item['slug'])
                        print(f"  Found {len(slugs)} items from search API")
            except Exception as e:
                print(f"  Search API failed: {e}")
            
            # Method 2: Parse category pages (Primeran only)
            if self.platform == 'primeran.eus':
            categories = ['/telesailak', '/zinema', '/dokumentalak-p', '/generoak-musika']
            for cat in categories:
                try:
                    response = self.api.session.get(f'https://primeran.eus/api/v1/pages{cat}')
                    if response.status_code == 200:
                        page_data = response.json()
                        self._sleep()
                        if 'children' in page_data:
                            series_slugs = set()
                            self._extract_slugs_from_children(page_data['children'], slugs, series_slugs)
                except Exception as e:
                    pass
            
            # Method 3: Get home content (works for both platforms)
            try:
                home_data = self.api.get_home_content()
                self._sleep()
                if 'children' in home_data:
                    series_slugs = set()
                    self._extract_slugs_from_children(home_data['children'], slugs, series_slugs)
            except Exception as e:
                pass
            
        except Exception as e:
            print(f"  Error discovering media: {e}")
        
        return list(slugs)
    
    def discover_series_from_sections(self) -> List[str]:
        """
        Discover series slugs from various sections
        
        Returns:
            List of series slugs
        """
        print("Discovering series from sections...")
        series_slugs = set()
        
        try:
            # Method 1: Use search API with empty query (Primeran only)
            if self.platform == 'primeran.eus':
            try:
                response = self.api.session.get('https://primeran.eus/api/v1/search?q=')
                if response.status_code == 200:
                    search_data = response.json()
                    self._sleep()
                    if 'data' in search_data and isinstance(search_data['data'], list):
                        for item in search_data['data']:
                            if 'slug' in item:
                                media_type = item.get('media_type', '').lower()
                                collection = item.get('collection', '').lower()
                                # Only include actual series
                                if media_type == 'series' or collection == 'series':
                                    series_slugs.add(item['slug'])
                        print(f"  Found {len(series_slugs)} series from search API")
            except Exception as e:
                print(f"  Search API failed: {e}")
            
            # Method 2: Parse category pages (Primeran only)
            if self.platform == 'primeran.eus':
            categories = ['/telesailak', '/zinema', '/dokumentalak-p']
            for cat in categories:
                try:
                    response = self.api.session.get(f'https://primeran.eus/api/v1/pages{cat}')
                    if response.status_code == 200:
                        page_data = response.json()
                        self._sleep()
                        if 'children' in page_data:
                            media_slugs = set()
                            self._extract_slugs_from_children(page_data['children'], media_slugs, series_slugs)
                except Exception as e:
                    pass
            
            # Method 3: Get home content (works for both platforms)
            try:
                home_data = self.api.get_home_content()
                self._sleep()
                if 'children' in home_data:
                    media_slugs = set()
                    self._extract_slugs_from_children(home_data['children'], media_slugs, series_slugs)
            except Exception as e:
                pass
            
        except Exception as e:
            print(f"  Error discovering series: {e}")
        
        return list(series_slugs)
    
    def check_media(self, slug: str) -> Dict[str, Any]:
        """
        Check a single media item for geo-restrictions
        
        Args:
            slug: Media slug
            
        Returns:
            Content data dictionary or None if item doesn't exist
        """
        print(f"  Checking media: {slug}")
        
        try:
            # Get media details
            # Note: Use /api/v1/media/{slug} for Makusi, but base_url already includes /api/v1
            # So we need to check if base_url ends with /api/v1 and adjust accordingly
            api_endpoint = f"{self.api.base_url}/media/{slug}"
            response = self.api.session.get(api_endpoint)
            self._sleep()
            
            # Handle different response codes BEFORE raise_for_status()
            if response.status_code == 404:
                # Item doesn't exist (might be a collection/page, not actual media)
                print(f"    ⚠️  Skipping {slug}: Not found (likely not a media item)")
                return None
            
            if response.status_code == 403:
                # Geo-restricted at API level
                print(f"    🚫 {slug}: Geo-restricted at API level (403)")
                # Initialize variables
                content_type = 'unknown'
                series_slug_from_metadata = None
                series_title_from_metadata = None
                
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Geo-restricted')
                    # Try to get metadata from error response if available
                    # Some APIs return partial metadata even on 403
                    if 'season_data' in error_data:
                        # This might be an episode - check season_data
                        season_data = error_data.get('season_data', {})
                        if isinstance(season_data, dict) and season_data.get('series_slug'):
                            content_type = 'episode'
                            series_slug_from_metadata = season_data.get('series_slug')
                            series_title_from_metadata = season_data.get('series_title')
                        else:
                            content_type = 'unknown'
                    elif error_data.get('collection') == 'series':
                        content_type = 'series'
                    else:
                        content_type = 'unknown'
                except:
                    error_msg = 'Geo-restricted'
                    content_type = 'unknown'
                
                # Create content data with limited info
                metadata = {'error': error_msg, 'api_restricted': True}
                metadata = self._add_platform_url_to_metadata(metadata, slug, content_type)
                
                content_data = {
                    'slug': slug,
                    'platform': self.platform,
                    'title': slug.replace('-', ' ').title(),  # Best guess from slug
                    'type': content_type,
                    'is_geo_restricted': True,
                    'restriction_type': 'api_403',
                    'metadata': metadata
                }
                
                # Add series information if this is an episode
                if content_type == 'episode' and series_slug_from_metadata:
                    content_data['series_slug'] = series_slug_from_metadata
                    if series_title_from_metadata:
                        content_data['series_title'] = series_title_from_metadata
                
                # Save to database
                self.db.upsert_content(content_data)
                self.db.add_check_history(slug, {
                    'is_geo_restricted': True,
                    'status_code': 403,
                    'error': error_msg
                })
                
                # Update stats
                self.stats['total_checked'] += 1
                self.stats['geo_restricted'] += 1
                
                return content_data
            
            if response.status_code == 500:
                # Server error - often indicates geo-restriction when accessing from restricted regions
                print(f"    🚫 {slug}: Server error (500) - likely geo-restricted")
                # Initialize variables
                content_type = 'unknown'
                series_slug_from_metadata = None
                series_title_from_metadata = None
                
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Server error - likely geo-restricted')
                    # Try to get metadata from error response if available
                    if 'season_data' in error_data:
                        # This might be an episode - check season_data
                        season_data = error_data.get('season_data', {})
                        if isinstance(season_data, dict) and season_data.get('series_slug'):
                            content_type = 'episode'
                            series_slug_from_metadata = season_data.get('series_slug')
                            series_title_from_metadata = season_data.get('series_title')
                        else:
                            content_type = 'unknown'
                    elif error_data.get('collection') == 'series':
                        content_type = 'series'
                    else:
                        content_type = 'unknown'
                except:
                    error_msg = response.text[:200] if response.text else 'Server error - likely geo-restricted'
                    content_type = 'unknown'
                
                # Create content data with limited info
                metadata = {'error': error_msg, 'api_restricted': True, 'status_code': 500}
                metadata = self._add_platform_url_to_metadata(metadata, slug, content_type)
                
                content_data = {
                    'slug': slug,
                    'platform': self.platform,
                    'title': slug.replace('-', ' ').title(),  # Best guess from slug
                    'type': content_type,
                    'is_geo_restricted': True,
                    'restriction_type': 'api_500',
                    'metadata': metadata
                }
                
                # Add series information if this is an episode
                if content_type == 'episode' and series_slug_from_metadata:
                    content_data['series_slug'] = series_slug_from_metadata
                    if series_title_from_metadata:
                        content_data['series_title'] = series_title_from_metadata
                
                # Save to database
                self.db.upsert_content(content_data)
                self.db.add_check_history(slug, {
                    'is_geo_restricted': True,
                    'status_code': 500,
                    'error': error_msg
                })
                
                # Update stats
                self.stats['total_checked'] += 1
                self.stats['geo_restricted'] += 1
                
                return content_data
            
            # 200 OK - proceed normally
            response.raise_for_status()
            media_data = response.json()
            
            # Determine content type based on metadata
            # Check season_data first (indicates episode)
            content_type = media_data.get('type', 'unknown')
            series_slug_from_metadata = None
            series_title_from_metadata = None
            
            if 'season_data' in media_data and isinstance(media_data['season_data'], dict):
                # This is an episode - has season_data with series information
                content_type = 'episode'
                season_data = media_data['season_data']
                series_slug_from_metadata = season_data.get('series_slug')
                series_title_from_metadata = season_data.get('series_title')
            elif media_data.get('collection') == 'series':
                # This is a series
                content_type = 'series'
            # Otherwise, use the type from API (vod for standalone media)
            
            # Extract media_type (audio/video) from metadata
            media_type = media_data.get('media_type', '').lower() if media_data.get('media_type') else None
            
            # Check if geo-check is disabled
            if self.disable_geo_check:
                print(f"    ℹ️  Geo-check disabled - fetching metadata only")
                # Get existing status from DB if available
                existing_status = self.db.get_content_status(slug, self.platform)
                
                # Prepare content data
                # Add platform URL to metadata
                metadata = media_data.copy() if isinstance(media_data, dict) else {}
                metadata = self._add_platform_url_to_metadata(metadata, slug, content_type)
                
                # Add media_type to metadata if present
                if media_type:
                    metadata['media_type'] = media_type
                
                content_data = {
                    'slug': slug,
                    'platform': self.platform,
                    'title': media_data.get('title'),
                    'type': content_type,
                    'duration': media_data.get('duration'),
                    'year': media_data.get('production_year') or media_data.get('year'),
                    'genres': [g.get('name') for g in media_data.get('genres', [])],
                    'metadata': metadata
                }
                
                # Add series information if this is an episode
                if content_type == 'episode' and series_slug_from_metadata:
                    content_data['series_slug'] = series_slug_from_metadata
                    if series_title_from_metadata:
                        content_data['series_title'] = series_title_from_metadata
                    # Extract episode/season numbers from season_data if available
                    if 'season_data' in media_data and isinstance(media_data['season_data'], dict):
                        season_data = media_data['season_data']
                        # Try to get episode number from next_episode or other sources
                        # Note: episode_number might not be in season_data, it's usually in the episode list
                        if 'season_number' in season_data:
                            content_data['season_number'] = season_data.get('season_number')
                
                # Preserve existing geo-restriction status if it was marked as restricted
                if existing_status and existing_status['is_geo_restricted'] is True:
                    content_data['is_geo_restricted'] = True
                    content_data['restriction_type'] = existing_status['restriction_type']
                    print(f"    ✓ Preserved existing geo-restricted status")
                else:
                    # Don't set status - leave it as None or existing value
                    if existing_status:
                        content_data['is_geo_restricted'] = existing_status['is_geo_restricted']
                        content_data['restriction_type'] = existing_status['restriction_type']
                    else:
                        content_data['is_geo_restricted'] = None
                        content_data['restriction_type'] = None
                
                # Save to database
                self.db.upsert_content(content_data)
                
                # Update stats (don't count as geo-check)
                self.stats['total_checked'] += 1
                
                return content_data
            else:
                # Normal flow - check geo-restriction via manifest or audio file
                # Pass media_data so API can detect audio content and check appropriate URL
                geo_check = self.api.check_geo_restriction(slug, media_metadata=media_data)
                self._sleep()
                
                # Determine restriction type based on media type
                if geo_check.get('media_type') == 'audio':
                    restriction_type = f"audio_{geo_check.get('status_code')}"
                else:
                    restriction_type = f"manifest_{geo_check.get('status_code')}"
                
                # Prepare content data
                # Add platform URL to metadata
                metadata = media_data.copy() if isinstance(media_data, dict) else {}
                metadata = self._add_platform_url_to_metadata(metadata, slug, content_type)
                
                # Ensure media_type is in metadata
                if media_type:
                    metadata['media_type'] = media_type
                
                # Handle case where geo_check returns None for is_geo_restricted
                # This can happen if manifest check fails or returns unexpected status
                is_geo_restricted = geo_check.get('is_geo_restricted')
                if is_geo_restricted is None:
                    # If status_code is 403 or 500, treat as geo-restricted
                    status_code = geo_check.get('status_code')
                    if status_code in [403, 500]:
                        is_geo_restricted = True
                        print(f"    ⚠️  Manifest check returned None but status_code={status_code}, treating as geo-restricted")
                    else:
                        # For other cases (404, network errors, etc.), log warning but keep as None
                        print(f"    ⚠️  Geo-restriction status unclear for {slug}: {geo_check.get('error', 'Unknown error')}")
                
                content_data = {
                    'slug': slug,
                    'platform': self.platform,
                    'title': media_data.get('title'),
                    'type': content_type,
                    'duration': media_data.get('duration'),
                    'year': media_data.get('production_year') or media_data.get('year'),
                    'genres': [g.get('name') for g in media_data.get('genres', [])],
                    'is_geo_restricted': is_geo_restricted,
                    'restriction_type': restriction_type if is_geo_restricted is not None else None,
                    'metadata': metadata
                }
                
                # Add series information if this is an episode
                if content_type == 'episode' and series_slug_from_metadata:
                    content_data['series_slug'] = series_slug_from_metadata
                    if series_title_from_metadata:
                        content_data['series_title'] = series_title_from_metadata
                    # Extract episode/season numbers from season_data if available
                    if 'season_data' in media_data and isinstance(media_data['season_data'], dict):
                        season_data = media_data['season_data']
                        if 'season_number' in season_data:
                            content_data['season_number'] = season_data.get('season_number')
                
                # Save to database
                self.db.upsert_content(content_data)
                self.db.add_check_history(slug, geo_check)
                
                # Update stats
                self.stats['total_checked'] += 1
                if geo_check.get('is_geo_restricted') is True:
                    self.stats['geo_restricted'] += 1
                elif geo_check.get('is_geo_restricted') is False:
                    self.stats['accessible'] += 1
                
                return content_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"    ⚠️  Skipping {slug}: Not found")
                return None
            elif e.response.status_code == 403:
                # Already handled above, but just in case
                print(f"    🚫 {slug}: Geo-restricted (403)")
                return None
            elif e.response.status_code == 500:
                # Already handled above, but just in case
                print(f"    🚫 {slug}: Geo-restricted (500)")
                return None
            else:
                print(f"    ✗ Error checking {slug}: {e}")
                self.stats['errors'] += 1
                return None
        except Exception as e:
            print(f"    ✗ Error checking {slug}: {e}")
            self.stats['errors'] += 1
            return None
    
    def check_series(self, series_slug: str) -> List[Dict[str, Any]]:
        """
        Check all episodes in a series for geo-restrictions
        
        Args:
            series_slug: Series slug
            
        Returns:
            List of episode content data dictionaries
        """
        print(f"Checking series: {series_slug}")
        
        try:
            # Get series metadata first
            series_metadata = None
            series_title = None
            try:
                series_data = self.api.get_series(series_slug)
                self._sleep()
                series_metadata = series_data
                series_title = series_data.get('title')
            except Exception as e:
                print(f"  ⚠️  Could not fetch series metadata: {e}")
            
            # Get all episodes
            episodes = self.api.get_all_episodes_from_series(series_slug)
            self._sleep()
            
            if not episodes:
                print(f"  No episodes found in series {series_slug}")
                # Still create series record even if no episodes
                if series_metadata:
                    self._create_series_record(series_slug, series_metadata, episodes)
                return []
            
            print(f"  Found {len(episodes)} episodes")
            
            # Create series record before processing episodes
            if series_metadata:
                self._create_series_record(series_slug, series_metadata, episodes)
            
            episode_data_list = []
            
            for episode in episodes:
                episode_slug = episode['episode_slug']
                print(f"    Checking episode: {episode_slug}")
                
                try:
                    # Try to get full episode metadata (includes images, description, etc.)
                    episode_metadata = episode  # Default to transformed episode data
                    api_restricted = False
                    api_status_code = None
                    
                    try:
                        full_episode_data = self.api.get_media(episode_slug)
                        self._sleep()
                        # Use full metadata if available
                        episode_metadata = full_episode_data
                    except requests.exceptions.HTTPError as e:
                        # Handle 403/500 at API level - mark as geo-restricted immediately
                        if e.response.status_code == 403:
                            api_restricted = True
                            api_status_code = 403
                            print(f"      🚫 {episode_slug}: Geo-restricted at API level (403)")
                        elif e.response.status_code == 500:
                            api_restricted = True
                            api_status_code = 500
                            print(f"      🚫 {episode_slug}: Server error (500) - likely geo-restricted")
                        else:
                            # For 404 or other errors, use the transformed episode data
                            print(f"      ⚠️  Could not fetch full metadata for {episode_slug}: {e.response.status_code}")
                    except Exception as e:
                        # For other exceptions (network errors, etc.), use the transformed episode data
                        print(f"      ⚠️  Could not fetch full metadata for {episode_slug}: {e}")
                    
                    # Check if geo-check is disabled
                    if self.disable_geo_check:
                        print(f"      ℹ️  Geo-check disabled - fetching metadata only")
                        # Get existing status from DB if available
                        existing_status = self.db.get_content_status(episode_slug, self.platform)
                        
                        # Extract media_type from episode metadata
                        episode_media_type = None
                        if isinstance(episode_metadata, dict):
                            episode_media_type = episode_metadata.get('media_type', '').lower() if episode_metadata.get('media_type') else None
                        
                        # Prepare content data
                        # Add platform URL to metadata
                        metadata = episode_metadata.copy() if isinstance(episode_metadata, dict) else {}
                        metadata = self._add_platform_url_to_metadata(metadata, episode_slug, 'episode', series_slug)
                        
                        # Ensure media_type is in metadata
                        if episode_media_type:
                            metadata['media_type'] = episode_media_type
                        
                        content_data = {
                            'slug': episode_slug,
                            'platform': self.platform,
                            'title': episode_metadata.get('title') if isinstance(episode_metadata, dict) else episode.get('episode_title'),
                            'type': 'episode',
                            'duration': episode_metadata.get('duration') if isinstance(episode_metadata, dict) else episode.get('duration'),
                            'year': episode_metadata.get('production_year') or (episode_metadata.get('year') if isinstance(episode_metadata, dict) else None),
                            'genres': [g.get('name') for g in episode_metadata.get('genres', [])] if isinstance(episode_metadata, dict) else [],
                            'series_slug': series_slug,
                            'series_title': episode.get('series_title'),
                            'season_number': episode.get('season_number'),
                            'episode_number': episode.get('episode_number'),
                            'metadata': metadata
                        }
                        
                        # Preserve existing geo-restriction status if it was marked as restricted
                        if existing_status and existing_status['is_geo_restricted'] is True:
                            content_data['is_geo_restricted'] = True
                            content_data['restriction_type'] = existing_status['restriction_type']
                            print(f"      ✓ Preserved existing geo-restricted status")
                        else:
                            # Don't set status - leave it as None or existing value
                            if existing_status:
                                content_data['is_geo_restricted'] = existing_status['is_geo_restricted']
                                content_data['restriction_type'] = existing_status['restriction_type']
                            else:
                                content_data['is_geo_restricted'] = None
                                content_data['restriction_type'] = None
                        
                        # Save to database
                        self.db.upsert_content(content_data)
                        
                        # Update stats (don't count as geo-check)
                        self.stats['total_checked'] += 1
                        
                        episode_data_list.append(content_data)
                    else:
                        # Normal flow - check geo-restriction for this episode
                        # If API already returned 403/500, mark as geo-restricted immediately
                        if api_restricted:
                            # Create content data with limited info (API restricted)
                            error_msg = 'Geo-restricted'
                            
                            metadata = episode_metadata.copy() if isinstance(episode_metadata, dict) else {}
                            metadata['error'] = error_msg
                            metadata['api_restricted'] = True
                            metadata = self._add_platform_url_to_metadata(metadata, episode_slug, 'episode', series_slug)
                            
                            content_data = {
                                'slug': episode_slug,
                                'platform': self.platform,
                                'title': episode_metadata.get('title') if isinstance(episode_metadata, dict) else episode.get('episode_title'),
                                'type': 'episode',
                                'series_slug': series_slug,
                                'series_title': episode.get('series_title'),
                                'season_number': episode.get('season_number'),
                                'episode_number': episode.get('episode_number'),
                                'is_geo_restricted': True,
                                'restriction_type': f'api_{api_status_code}',
                                'metadata': metadata
                            }
                            
                            # Save to database
                            self.db.upsert_content(content_data)
                            self.db.add_check_history(episode_slug, {
                                'is_geo_restricted': True,
                                'status_code': api_status_code,
                                'error': error_msg
                            })
                            
                            # Update stats
                            self.stats['total_checked'] += 1
                            self.stats['geo_restricted'] += 1
                            
                            episode_data_list.append(content_data)
                        else:
                            # API is accessible, check manifest/audio file
                            # Pass episode_metadata so API can detect audio content
                            episode_meta_dict = episode_metadata if isinstance(episode_metadata, dict) else None
                            geo_check = self.api.check_geo_restriction(episode_slug, media_metadata=episode_meta_dict)
                        self._sleep()
                        
                            # Extract media_type from episode metadata
                            episode_media_type = None
                            if isinstance(episode_metadata, dict):
                                episode_media_type = episode_metadata.get('media_type', '').lower() if episode_metadata.get('media_type') else None
                            
                            # Determine restriction type based on media type
                            if geo_check.get('media_type') == 'audio':
                                restriction_type = f"audio_{geo_check.get('status_code')}"
                            else:
                                restriction_type = f"manifest_{geo_check.get('status_code')}"
                            
                            # Handle case where geo_check returns None for is_geo_restricted
                            is_geo_restricted = geo_check.get('is_geo_restricted')
                            if is_geo_restricted is None:
                                # If status_code is 403 or 500, treat as geo-restricted
                                status_code = geo_check.get('status_code')
                                if status_code in [403, 500]:
                                    is_geo_restricted = True
                                    print(f"      ⚠️  Manifest check returned None but status_code={status_code}, treating as geo-restricted")
                                else:
                                    # For other cases (404, network errors, etc.), log warning but keep as None
                                    print(f"      ⚠️  Geo-restriction status unclear for {episode_slug}: {geo_check.get('error', 'Unknown error')}")
                            
                        # Prepare content data
                            # Add platform URL to metadata
                            metadata = episode_metadata.copy() if isinstance(episode_metadata, dict) else {}
                            metadata = self._add_platform_url_to_metadata(metadata, episode_slug, 'episode', series_slug)
                            
                            # Ensure media_type is in metadata
                            if episode_media_type:
                                metadata['media_type'] = episode_media_type
                            
                        content_data = {
                            'slug': episode_slug,
                                'platform': self.platform,
                                'title': episode_metadata.get('title') if isinstance(episode_metadata, dict) else episode.get('episode_title'),
                            'type': 'episode',
                                'duration': episode_metadata.get('duration') if isinstance(episode_metadata, dict) else episode.get('duration'),
                                'year': episode_metadata.get('production_year') or (episode_metadata.get('year') if isinstance(episode_metadata, dict) else None),
                                'genres': [g.get('name') for g in episode_metadata.get('genres', [])] if isinstance(episode_metadata, dict) else [],
                            'series_slug': series_slug,
                            'series_title': episode.get('series_title'),
                            'season_number': episode.get('season_number'),
                            'episode_number': episode.get('episode_number'),
                                'is_geo_restricted': is_geo_restricted,
                                'restriction_type': restriction_type if is_geo_restricted is not None else None,
                                'metadata': metadata
                        }
                        
                        # Save to database
                        self.db.upsert_content(content_data)
                        self.db.add_check_history(episode_slug, geo_check)
                        
                        # Update stats
                        self.stats['total_checked'] += 1
                        if geo_check.get('is_geo_restricted') is True:
                            self.stats['geo_restricted'] += 1
                        elif geo_check.get('is_geo_restricted') is False:
                            self.stats['accessible'] += 1
                        
                        episode_data_list.append(content_data)
                    
                except Exception as e:
                    print(f"      Error checking episode {episode_slug}: {e}")
                    self.stats['errors'] += 1
            
            return episode_data_list
            
        except Exception as e:
            print(f"  Error checking series {series_slug}: {e}")
            self.stats['errors'] += 1
            return []
    
    def _create_series_record(self, series_slug: str, series_metadata: Dict[str, Any], episodes: List[Dict[str, Any]]) -> None:
        """
        Create a series record in the database
        
        Args:
            series_slug: Series slug
            series_metadata: Series metadata from API
            episodes: List of episode dictionaries (for counting)
        """
        try:
            # Extract series information
            series_title = series_metadata.get('title') or series_slug
            series_type = series_metadata.get('type', 'series')
            
            # Get metadata
            metadata = series_metadata.copy()
            metadata = self._add_platform_url_to_metadata(metadata, series_slug, 'series')
            
            # Calculate geo-restriction summary from episodes if available
            restricted_count = 0
            accessible_count = 0
            unknown_count = 0
            
            if episodes:
                for episode in episodes:
                    # Try to get geo-restriction from existing database records
                    episode_slug = episode.get('episode_slug')
                    if episode_slug:
                        existing_status = self.db.get_content_status(episode_slug, self.platform)
                        if existing_status:
                            if existing_status['is_geo_restricted'] is True:
                                restricted_count += 1
                            elif existing_status['is_geo_restricted'] is False:
                                accessible_count += 1
                            else:
                                unknown_count += 1
                        else:
                            unknown_count += 1
            
            # Determine overall geo-restriction status
            # If all episodes are restricted, series is restricted
            # If all episodes are accessible, series is accessible
            # Otherwise, it's unknown
            total_episodes = len(episodes)
            is_geo_restricted = None
            if total_episodes > 0:
                if restricted_count == total_episodes:
                    is_geo_restricted = True
                elif accessible_count == total_episodes:
                    is_geo_restricted = False
                # Otherwise, keep as None (mixed or unknown)
            
            # Create series content data
            content_data = {
                'slug': series_slug,
                'platform': self.platform,
                'title': series_title,
                'type': 'series',
                'duration': series_metadata.get('duration'),
                'year': series_metadata.get('production_year') or series_metadata.get('year'),
                'genres': [g.get('name') for g in series_metadata.get('genres', [])] if isinstance(series_metadata.get('genres'), list) else [],
                'is_geo_restricted': is_geo_restricted,
                'restriction_type': None,  # Series don't have a single restriction type
                'metadata': metadata
            }
            
            # Save to database
            self.db.upsert_content(content_data)
            print(f"  ✓ Created series record: {series_title}")
            
        except Exception as e:
            print(f"  ⚠️  Error creating series record: {e}")
    
    def scrape_all(self, 
                   media_slugs: List[str] = None,
                   series_slugs: List[str] = None,
                   limit: Optional[int] = None):
        """
        Scrape all content
        
        Args:
            media_slugs: Optional list of media slugs to check
            series_slugs: Optional list of series slugs to check
        """
        print("=" * 80)
        print(f"Starting {self.platform} Content Scraper")
        print("=" * 80)
        
        # Discover content if not provided
        if not media_slugs:
            print("\n[Step 1] Discovering media...")
            media_slugs = self.discover_media_from_sections()
            print(f"  Found {len(media_slugs)} media items")
        
        if not series_slugs:
            print("\n[Step 2] Discovering series...")
            series_slugs = self.discover_series_from_sections()
            print(f"  Found {len(series_slugs)} series")
        
        self.stats['total_discovered'] = len(media_slugs) + len(series_slugs)
        
        # Apply limit if specified
        if limit:
            if media_slugs:
                media_slugs = media_slugs[:limit]
            if series_slugs:
                series_slugs = series_slugs[:limit]
            print(f"\n[LIMIT] Processing first {limit} items of each type")
        
        # Check media
        if media_slugs:
            print(f"\n[Step 3] Checking {len(media_slugs)} media items...")
            for slug in media_slugs:
                if slug not in self.discovered_slugs:
                    self.check_media(slug)
                    self.discovered_slugs.add(slug)
        
        # Check series
        if series_slugs:
            print(f"\n[Step 4] Checking {len(series_slugs)} series...")
            for slug in series_slugs:
                if slug not in self.discovered_slugs:
                    self.check_series(slug)
                    self.discovered_slugs.add(slug)
        
        # Print summary
        print("\n" + "=" * 80)
        print("Scraping Complete!")
        print("=" * 80)
        print(f"Total discovered: {self.stats['total_discovered']}")
        print(f"Total checked: {self.stats['total_checked']}")
        print(f"Geo-restricted: {self.stats['geo_restricted']}")
        print(f"Accessible: {self.stats['accessible']}")
        print(f"Errors: {self.stats['errors']}")
        
        # Database statistics
        db_stats = self.db.get_statistics()
        print(f"\nDatabase Statistics:")
        print(f"  Total in DB: {db_stats['total_content']}")
        print(f"  Geo-restricted: {db_stats['geo_restricted_count']} ({db_stats['geo_restricted_percentage']:.1f}%)")
        print(f"  Accessible: {db_stats['accessible_count']}")
        print(f"  Unknown: {db_stats['unknown_count']}")
