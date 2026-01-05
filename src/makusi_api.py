#!/usr/bin/env python3
"""
Makusi.eus API Client

Handles authentication and API interactions with Makusi.eus platform.
Uses shared Gigya SSO with Primeran.eus.
"""

import requests
import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MakusiAPI:
    """API client for Makusi.eus"""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize API client
        
        Args:
            username: Makusi username/email (defaults to PRIMERAN_USERNAME env var, shared SSO)
            password: Makusi password (defaults to PRIMERAN_PASSWORD env var, shared SSO)
        """
        # Makusi uses the same credentials as Primeran (shared SSO)
        self.username = username or os.getenv('PRIMERAN_USERNAME')
        self.password = password or os.getenv('PRIMERAN_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError(
                "Username and password required. "
                "Set PRIMERAN_USERNAME and PRIMERAN_PASSWORD in .env file "
                "(shared SSO credentials work for both Primeran and Makusi)"
            )
        
        self.session = requests.Session()
        self.gigya_api_key = "4_OrNV-xF_hgF-IKSFkQrJxg"  # Makusi-specific API key
        self.base_url = "https://makusi.eus/api/v1"
        self.authenticated = False
    
    @property
    def platform(self) -> str:
        """Return platform identifier"""
        return 'makusi.eus'
    
    def login(self) -> bool:
        """
        Authenticate with Makusi.eus using Gigya SSO (shared with Primeran)
        
        Returns:
            True if authentication successful, False otherwise
        """
        # Makusi uses the same login endpoint as Primeran (shared SSO)
        login_url = "https://login.primeran.eus/accounts.login"
        
        response = self.session.post(login_url, data={
            'apiKey': self.gigya_api_key,
            'loginID': self.username,
            'password': self.password,
            'format': 'json'
        })
        
        result = response.json()
        
        if result.get('errorCode') == 0:
            self.authenticated = True
            return True
        else:
            error_msg = result.get('errorMessage', 'Unknown error')
            raise Exception(f"Authentication failed: {error_msg}")
    
    def ensure_authenticated(self):
        """Ensure we're authenticated, login if needed"""
        if not self.authenticated:
            self.login()
    
    def get_media(self, slug: str) -> Dict[str, Any]:
        """
        Get media details
        
        Args:
            slug: Media slug (e.g., 'heidi-katamotzaren-erreskatea')
            
        Returns:
            Media metadata dictionary
        """
        self.ensure_authenticated()
        response = self.session.get(f"{self.base_url}/media/{slug}")
        response.raise_for_status()
        return response.json()
    
    def get_series(self, slug: str) -> Dict[str, Any]:
        """
        Get series details including all seasons and episodes
        
        Args:
            slug: Series slug (e.g., 'goazen-d12')
            
        Returns:
            Series metadata dictionary with seasons and episodes
        """
        self.ensure_authenticated()
        response = self.session.get(f"{self.base_url}/series/{slug}")
        response.raise_for_status()
        return response.json()
    
    def get_home_content(self) -> Dict[str, Any]:
        """
        Get home page content structure
        
        Returns:
            Home page content with sections, carousels, etc.
        """
        self.ensure_authenticated()
        response = self.session.get(f"{self.base_url}/home")
        response.raise_for_status()
        return response.json()
    
    def check_geo_restriction(self, slug: str, language: str = 'eu') -> Dict[str, Any]:
        """
        Check if content is geo-restricted by testing manifest URL
        
        Args:
            slug: Content slug (episode slug for series, media slug for individual content)
            language: Language code (default: 'eu' for Euskara)
            
        Returns:
            Dictionary with:
            - is_geo_restricted: bool or None
            - status_code: HTTP status code
            - accessible: bool (True if 200, False otherwise)
            - error: str or None
        """
        self.ensure_authenticated()
        
        manifest_url = f"https://makusi.eus/manifests/{slug}/{language}/widevine/dash.mpd"
        
        try:
            response = self.session.get(manifest_url, timeout=10)
            status_code = response.status_code
            
            result = {
                'status_code': status_code,
                'accessible': status_code == 200,
                'error': None
            }
            
            if status_code == 200:
                result['is_geo_restricted'] = False
            elif status_code == 403:
                result['is_geo_restricted'] = True
                result['error'] = 'Forbidden - Geo-restricted'
            elif status_code == 500:
                # Server error - often indicates geo-restriction when accessing from restricted regions
                result['is_geo_restricted'] = True
                result['error'] = 'Server error (500) - likely geo-restricted'
            elif status_code == 404:
                result['is_geo_restricted'] = None
                result['error'] = 'Not found - Content may not exist'
            else:
                result['is_geo_restricted'] = None
                result['error'] = f'Unexpected status code: {status_code}'
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                'status_code': None,
                'accessible': False,
                'is_geo_restricted': None,
                'error': str(e)
            }
    
    def get_all_episodes_from_series(self, series_slug: str) -> List[Dict[str, Any]]:
        """
        Extract all episodes from a series
        
        Args:
            series_slug: Series slug
            
        Returns:
            List of episode dictionaries with series context
        """
        series_data = self.get_series(series_slug)
        episodes = []
        
        for season in series_data.get('seasons', []):
            season_number = season.get('season_number', season.get('id', 1))
            
            for episode in season.get('episodes', []):
                episode_info = {
                    'episode_id': episode.get('id'),
                    'episode_slug': episode.get('slug'),
                    'episode_title': episode.get('title'),
                    'episode_number': episode.get('episode_number'),
                    'duration': episode.get('duration'),
                    'series_slug': series_slug,
                    'series_title': series_data.get('title'),
                    'season_number': season_number,
                    'type': 'episode'
                }
                
                # Include images if available in the episode data
                if 'images' in episode and isinstance(episode['images'], list) and len(episode['images']) > 0:
                    episode_info['images'] = episode['images']
                
                # Include description if available
                if 'description' in episode:
                    episode_info['description'] = episode.get('description')
                
                # Include other metadata that might be in the episode object
                if 'age_rating' in episode:
                    episode_info['age_rating'] = episode.get('age_rating')
                
                if 'access_restriction' in episode:
                    episode_info['access_restriction'] = episode.get('access_restriction')
                
                episodes.append(episode_info)
        
        return episodes
