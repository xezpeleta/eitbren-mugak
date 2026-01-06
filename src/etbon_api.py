#!/usr/bin/env python3
"""
ETB On (etbon.eus) API Client

Handles authentication and API interactions with the ETB On platform.
Uses shared Gigya SSO with the rest of the EITB ecosystem.
"""

import os
from typing import Optional, Dict, Any, List

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EtbonAPI:
    """API client for ETB On (etbon.eus)"""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize API client

        Args:
            username: Username/email (defaults to PRIMERAN_USERNAME env var, shared SSO)
            password: Password (defaults to PRIMERAN_PASSWORD env var, shared SSO)
        """
        # ETB On uses the same SSO credentials as Primeran/Makusi
        self.username = username or os.getenv("PRIMERAN_USERNAME")
        self.password = password or os.getenv("PRIMERAN_PASSWORD")

        if not self.username or not self.password:
            raise ValueError(
                "Username and password required. "
                "Set PRIMERAN_USERNAME and PRIMERAN_PASSWORD in .env file "
                "(shared SSO credentials work for Primeran, Makusi, and ETB On)."
            )

        self.session = requests.Session()

        # Public Gigya web API key for ETB On
        self.gigya_api_key = "4_eUfqY3nplenbM2JKHjSxLw"

        # Base API URL for ETB On
        self.base_url = "https://etbon.eus/api/v1"

        self.authenticated = False

    @property
    def platform(self) -> str:
        """Return platform identifier"""
        return "etbon.eus"

    def login(self) -> bool:
        """
        Authenticate with ETB On using Gigya SSO

        Returns:
            True if authentication successful, False otherwise
        """
        # ETB On shares the same Gigya SSO endpoints as Primeran/Makusi
        login_url = "https://login.primeran.eus/accounts.login"

        response = self.session.post(
            login_url,
            data={
                "apiKey": self.gigya_api_key,
                "loginID": self.username,
                "password": self.password,
                "format": "json",
            },
        )

        result = response.json()

        if result.get("errorCode") == 0:
            self.authenticated = True
            return True
        else:
            error_msg = result.get("errorMessage", "Unknown error")
            raise Exception(f"Authentication failed: {error_msg}")

    def ensure_authenticated(self):
        """Ensure we're authenticated, login if needed"""
        if not self.authenticated:
            self.login()

    # -------------------------------------------------------------------------
    # Core content API methods (mirror PrimeranAPI / MakusiAPI contracts)
    # -------------------------------------------------------------------------

    def get_media(self, slug: str) -> Dict[str, Any]:
        """
        Get media details

        Args:
            slug: Media slug (e.g., 'la-familia-bloom-1-17403293')

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
            slug: Series slug (e.g., 'vaya-semanita')

        Returns:
            Series metadata dictionary with seasons and episodes
        """
        self.ensure_authenticated()
        response = self.session.get(f"{self.base_url}/series/{slug}")
        response.raise_for_status()
        return response.json()

    def get_home_content(self) -> Dict[str, Any]:
        """
        Get home page content structure, if available.

        NOTE: ETB On may or may not expose a /home endpoint; this is provided
        to keep the interface compatible with ContentScraper. If the endpoint
        does not exist, callers should be prepared to handle HTTP errors.

        Returns:
            Home page content with sections, carousels, etc.
        """
        self.ensure_authenticated()
        response = self.session.get(f"{self.base_url}/home")
        response.raise_for_status()
        return response.json()

    # -------------------------------------------------------------------------
    # Geo-restriction checking
    # -------------------------------------------------------------------------

    def check_geo_restriction(
        self,
        slug: str,
        language: str = "eu",
        media_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Check if content is geo-restricted.

        For now, ETB On streaming endpoints have not been fully reversed, so
        this returns a stub result with is_geo_restricted = None. This keeps
        the scraper logic working without making incorrect assumptions.

        Args:
            slug: Content slug (episode slug for series, media slug for individual content)
            language: Language code (default: 'eu' for Euskara)
            media_metadata: Optional media metadata (unused for now, reserved for future)

        Returns:
            Dictionary with:
            - is_geo_restricted: None (unknown)
            - status_code: None
            - accessible: False
            - error: explanatory message
            - media_type: 'audio' or 'video' if detectable from metadata
        """
        media_type = None
        if media_metadata and isinstance(media_metadata, dict):
            media_type = (
                media_metadata.get("media_type", "").lower()
                if media_metadata.get("media_type")
                else None
            )

        return {
            "status_code": None,
            "accessible": False,
            "is_geo_restricted": None,
            "error": (
                "Geo-restriction check for ETB On is not implemented yet; "
                "streaming endpoints need further reverse engineering."
            ),
            "media_type": media_type,
        }

    # -------------------------------------------------------------------------
    # Series helpers
    # -------------------------------------------------------------------------

    def get_all_episodes_from_series(self, series_slug: str) -> List[Dict[str, Any]]:
        """
        Extract all episodes from a series

        Args:
            series_slug: Series slug

        Returns:
            List of episode dictionaries with series context
        """
        series_data = self.get_series(series_slug)
        episodes: List[Dict[str, Any]] = []

        for season in series_data.get("seasons", []):
            season_number = season.get("season_number", season.get("id", 1))

            for episode in season.get("episodes", []):
                episode_info: Dict[str, Any] = {
                    "episode_id": episode.get("id"),
                    "episode_slug": episode.get("slug"),
                    "episode_title": episode.get("title"),
                    "episode_number": episode.get("episode_number"),
                    "duration": episode.get("duration"),
                    "series_slug": series_slug,
                    "series_title": series_data.get("title"),
                    "season_number": season_number,
                    "type": "episode",
                }

                # Include images if available in the episode data
                if (
                    "images" in episode
                    and isinstance(episode["images"], list)
                    and episode["images"]
                ):
                    episode_info["images"] = episode["images"]

                # Include description if available
                if "description" in episode:
                    episode_info["description"] = episode.get("description")

                # Include other metadata that might be in the episode object
                if "age_rating" in episode:
                    episode_info["age_rating"] = episode.get("age_rating")

                if "access_restriction" in episode:
                    episode_info["access_restriction"] = episode.get(
                        "access_restriction"
                    )

                episodes.append(episode_info)

        return episodes

