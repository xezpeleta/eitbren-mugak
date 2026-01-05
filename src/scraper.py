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
            response = self.api.session.get(f"{self.api.base_url}/media/{slug}")
            self._sleep()
            
            # Handle different response codes
            if response.status_code == 404:
                # Item doesn't exist (might be a collection/page, not actual media)
                print(f"    ⚠️  Skipping {slug}: Not found (likely not a media item)")
                return None
            
            if response.status_code == 403:
                # Geo-restricted at API level
                print(f"    🚫 {slug}: Geo-restricted at API level (403)")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Geo-restricted')
                except:
                    error_msg = 'Geo-restricted'
                
                # Create content data with limited info
                content_data = {
                    'slug': slug,
                    'platform': self.platform,
                    'title': slug.replace('-', ' ').title(),  # Best guess from slug
                    'type': 'unknown',
                    'is_geo_restricted': True,
                    'restriction_type': 'api_403',
                    'metadata': {'error': error_msg, 'api_restricted': True}
                }
                
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
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Server error - likely geo-restricted')
                except:
                    error_msg = response.text[:200] if response.text else 'Server error - likely geo-restricted'
                
                # Create content data with limited info
                content_data = {
                    'slug': slug,
                    'platform': self.platform,
                    'title': slug.replace('-', ' ').title(),  # Best guess from slug
                    'type': 'unknown',
                    'is_geo_restricted': True,
                    'restriction_type': 'api_500',
                    'metadata': {'error': error_msg, 'api_restricted': True, 'status_code': 500}
                }
                
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
            
            # Check if geo-check is disabled
            if self.disable_geo_check:
                print(f"    ℹ️  Geo-check disabled - fetching metadata only")
                # Get existing status from DB if available
                existing_status = self.db.get_content_status(slug, self.platform)
                
                # Prepare content data
                content_data = {
                    'slug': slug,
                    'platform': self.platform,
                    'title': media_data.get('title'),
                    'type': media_data.get('type', 'unknown'),
                    'duration': media_data.get('duration'),
                    'year': media_data.get('production_year') or media_data.get('year'),
                    'genres': [g.get('name') for g in media_data.get('genres', [])],
                    'metadata': media_data
                }
                
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
                # Normal flow - check geo-restriction via manifest
                geo_check = self.api.check_geo_restriction(slug)
                self._sleep()
                
                # Prepare content data
                content_data = {
                    'slug': slug,
                    'platform': self.platform,
                    'title': media_data.get('title'),
                    'type': media_data.get('type', 'unknown'),
                    'duration': media_data.get('duration'),
                    'year': media_data.get('production_year') or media_data.get('year'),
                    'genres': [g.get('name') for g in media_data.get('genres', [])],
                    'is_geo_restricted': geo_check.get('is_geo_restricted'),
                    'restriction_type': f"manifest_{geo_check.get('status_code')}",
                    'metadata': media_data
                }
                
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
            # Get all episodes
            episodes = self.api.get_all_episodes_from_series(series_slug)
            self._sleep()
            
            if not episodes:
                print(f"  No episodes found in series {series_slug}")
                return []
            
            print(f"  Found {len(episodes)} episodes")
            
            episode_data_list = []
            
            for episode in episodes:
                episode_slug = episode['episode_slug']
                print(f"    Checking episode: {episode_slug}")
                
                try:
                    # Try to get full episode metadata (includes images, description, etc.)
                    episode_metadata = episode  # Default to transformed episode data
                    try:
                        full_episode_data = self.api.get_media(episode_slug)
                        self._sleep()
                        # Use full metadata if available
                        episode_metadata = full_episode_data
                    except Exception as e:
                        # If get_media fails (404, 403, etc.), use the transformed episode data
                        print(f"      Could not fetch full metadata for {episode_slug}: {e}")
                    
                    # Check if geo-check is disabled
                    if self.disable_geo_check:
                        print(f"      ℹ️  Geo-check disabled - fetching metadata only")
                        # Get existing status from DB if available
                        existing_status = self.db.get_content_status(episode_slug)
                        
                        # Prepare content data
                        content_data = {
                            'slug': episode_slug,
                            'platform': self.platform,
                            'title': episode_metadata.get('title') or episode.get('episode_title'),
                            'type': 'episode',
                            'duration': episode_metadata.get('duration') or episode.get('duration'),
                            'year': episode_metadata.get('production_year') or episode_metadata.get('year'),
                            'genres': [g.get('name') for g in episode_metadata.get('genres', [])],
                            'series_slug': series_slug,
                            'series_title': episode.get('series_title'),
                            'season_number': episode.get('season_number'),
                            'episode_number': episode.get('episode_number'),
                            'metadata': episode_metadata
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
                        geo_check = self.api.check_geo_restriction(episode_slug)
                        self._sleep()
                        
                        # Prepare content data
                        content_data = {
                            'slug': episode_slug,
                            'platform': self.platform,
                            'title': episode_metadata.get('title') or episode.get('episode_title'),
                            'type': 'episode',
                            'duration': episode_metadata.get('duration') or episode.get('duration'),
                            'year': episode_metadata.get('production_year') or episode_metadata.get('year'),
                            'genres': [g.get('name') for g in episode_metadata.get('genres', [])],
                            'series_slug': series_slug,
                            'series_title': episode.get('series_title'),
                            'season_number': episode.get('season_number'),
                            'episode_number': episode.get('episode_number'),
                            'is_geo_restricted': geo_check.get('is_geo_restricted'),
                            'restriction_type': f"manifest_{geo_check.get('status_code')}",
                            'metadata': episode_metadata
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
