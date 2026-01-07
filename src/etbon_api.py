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
        Check if content is geo-restricted by testing manifest URL and CDN segments.

        This method performs a multi-level check:
        1. Tests the API response for explicit geo-restriction errors
        2. For CDN-based content, tests actual media segments for HTTP 451 blocks
        3. Falls back to standard manifest URL testing

        Args:
            slug: Content slug (episode slug for series, media slug for individual content)
            language: Language code (default: 'eu' for Euskara)
            media_metadata: Optional media metadata to determine content type

        Returns:
            Dictionary with:
            - is_geo_restricted: bool or None
            - status_code: HTTP status code
            - accessible: bool (True if 200, False otherwise)
            - error: str or None
            - media_type: 'audio' or 'video' if detectable from metadata
        """
        self.ensure_authenticated()

        # Determine media type if available
        media_type = None
        if media_metadata and isinstance(media_metadata, dict):
            media_type = (
                media_metadata.get("media_type", "").lower()
                if media_metadata.get("media_type")
                else None
            )

        # Step 1: Get media metadata from API to check for CDN manifests
        # This also catches API-level geo-restrictions
        try:
            api_response = self.session.get(
                f"{self.base_url}/media/{slug}", timeout=10
            )

            # Check for API-level geo-restriction (HTTP 403)
            if api_response.status_code == 403:
                error_data = api_response.json()
                if error_data.get("message") == "MEDIA_GEO_RESTRICTED_ACCESS":
                    return {
                        "status_code": 403,
                        "accessible": False,
                        "is_geo_restricted": True,
                        "error": "Forbidden - Geo-restricted (API level)",
                        "media_type": media_type or "video",
                    }

            # If API returns success, check for manifests
            if api_response.status_code == 200:
                api_data = api_response.json()
                manifests = api_data.get("manifests", [])
                
                last_restricted_result = None

                # Step 2: Check manifests from API response
                # This handles both CDN-level blocks (HTTP 451) and standard checking
                for manifest in manifests:
                    # We are primarily interested in DASH manifests
                    if manifest.get("type") != "dash":
                        continue
                        
                    manifest_url = manifest.get("manifestURL", "")
                    if not manifest_url:
                        continue

                    # Handle relative URLs (common for etbon.eus)
                    if manifest_url.startswith("/"):
                        manifest_url = f"https://etbon.eus{manifest_url}"
                    
                    check_result = None

                    # Use specialized check for CDN URLs (which might block at segment level)
                    if manifest_url.startswith("https://cdn"):
                        check_result = self._check_cdn_geo_restriction(manifest_url)
                    else:
                        # Standard check for direct URLs
                        check_result = self._check_standard_manifest(manifest_url)

                    if check_result is not None:
                        # If we find an ACCESSIBLE manifest, the content is accessible
                        if check_result["accessible"]:
                            return {
                                "status_code": check_result.get("status_code", 200),
                                "accessible": True,
                                "is_geo_restricted": False,
                                "error": None,
                                "media_type": media_type or "video",
                            }
                        
                        # If we find a RESTRICTED manifest, keep it but continue checking others
                        # (in case another manifest works)
                        if check_result.get("is_geo_restricted"):
                            last_restricted_result = check_result

                # If we iterated all manifests and found no accessible ones, but did find a restricted one,
                # then return the restricted result.
                if last_restricted_result:
                    return {
                        "status_code": last_restricted_result.get("status_code"),
                        "accessible": False,
                        "is_geo_restricted": True,
                        "error": last_restricted_result.get("error"),
                        "media_type": media_type or "video",
                    }

        except requests.exceptions.RequestException:
            # If API check fails, fall through to standard manifest check
            pass

        # Step 3: Fallback to constructed manifest URL if no API manifests worked
        # (same as primeran/makusi logic)
        manifest_url = (
            f"https://etbon.eus/manifests/{slug}/{language}/widevine/dash.mpd"
        )
        
        check_result = self._check_standard_manifest(manifest_url)
        if check_result:
            # Augment result with media_type
            check_result["media_type"] = media_type or "video"
            return check_result
            
        return {
            "status_code": None,
            "accessible": False,
            "is_geo_restricted": None,
            "error": "Could not determine geo-restriction status",
            "media_type": media_type or "video",
        }

    def _check_standard_manifest(self, manifest_url: str) -> Optional[Dict[str, Any]]:
        """
        Check a standard manifest URL (non-CDN deep inspection)
        
        Args:
            manifest_url: Full manifest URL
            
        Returns:
            Dictionary with check result or None if check completely fails
        """
        try:
            response = self.session.get(manifest_url, timeout=10)
            status_code = response.status_code

            result = {
                "status_code": status_code,
                "accessible": status_code == 200,
                "error": None,
            }

            if status_code == 200:
                result["is_geo_restricted"] = False
            elif status_code == 403:
                result["is_geo_restricted"] = True
                result["error"] = "Forbidden - Geo-restricted"
            elif status_code == 500:
                # Server error - often indicates geo-restriction
                result["is_geo_restricted"] = True
                result["error"] = "Server error (500) - likely geo-restricted"
            elif status_code == 404:
                result["is_geo_restricted"] = None
                result["error"] = "Not found - Content may not exist"
            else:
                result["is_geo_restricted"] = None
                result["error"] = f"Unexpected status code: {status_code}"

            return result

        except Exception as e:
            return None

    def _check_cdn_geo_restriction(
        self, cdn_manifest_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check CDN-level geo-restriction by testing media segments.

        Some content (e.g., live TV recordings) may return 200 at the API level
        but block actual media delivery with HTTP 451 at the CDN level.

        Args:
            cdn_manifest_url: Full CDN manifest URL (e.g., https://cdn1.etbon.eus/...)

        Returns:
            Dictionary with geo-restriction status, or None if check fails
        """
        try:
            import xml.etree.ElementTree as ET

            # Fetch the CDN manifest
            manifest_response = self.session.get(cdn_manifest_url, timeout=5)

            if manifest_response.status_code != 200:
                # If manifest itself is blocked, it's geo-restricted
                return {
                    "status_code": manifest_response.status_code,
                    "accessible": False,
                    "is_geo_restricted": True,
                    "error": f"CDN manifest blocked ({manifest_response.status_code})",
                }

            # Parse the DASH manifest to extract a media segment URL
            root = ET.fromstring(manifest_response.content)
            base_url = cdn_manifest_url.rsplit("/", 1)[0] + "/"

            # Find first initialization segment
            ns = {"mpd": "urn:mpeg:dash:schema:mpd:2011"}
            for rep in root.findall(".//mpd:Representation", ns):
                seg_template = rep.find(".//mpd:SegmentTemplate", ns)
                if seg_template is not None:
                    init_url = seg_template.get("initialization")
                    if init_url:
                        # Build full segment URL
                        segment_url = base_url + init_url

                        # Test the segment with HEAD request (no download)
                        seg_response = self.session.head(segment_url, timeout=5)

                        if seg_response.status_code == 451:
                            # HTTP 451: Unavailable For Legal Reasons (geo-block)
                            return {
                                "status_code": 451,
                                "accessible": False,
                                "is_geo_restricted": True,
                                "error": "Unavailable For Legal Reasons - Geo-restricted (CDN level)",
                            }
                        elif seg_response.status_code == 403:
                            return {
                                "status_code": 403,
                                "accessible": False,
                                "is_geo_restricted": True,
                                "error": "Forbidden - Geo-restricted (CDN level)",
                            }
                        elif seg_response.status_code == 200:
                            return {
                                "status_code": 200,
                                "accessible": True,
                                "is_geo_restricted": False,
                                "error": None,
                            }
                        # If we get other status codes, break and return None
                        break

        except Exception:
            # If CDN check fails, return None to fall back to standard check
            pass

        return None

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

    # -------------------------------------------------------------------------
    # Live channels support
    # -------------------------------------------------------------------------

    def get_live_channels(self) -> List[Dict[str, Any]]:
        """
        Get list of all live channels from /api/v1/pages/zuzenekoak

        Returns:
            List of channel dictionaries with slug, title, type, etc.
        """
        self.ensure_authenticated()

        try:
            response = self.session.get(f"{self.base_url}/pages/zuzenekoak")
            response.raise_for_status()
            page_data = response.json()

            channels: List[Dict[str, Any]] = []

            # Recursively extract channels from children structure
            def extract_channels(obj: Any):
                if isinstance(obj, dict):
                    # Check if this is a live channel
                    if obj.get("type") == "live" and "slug" in obj:
                        channel_info = {
                            "slug": obj.get("slug"),
                            "title": obj.get("title"),
                            "type": "live",
                            "is_fast_channel": obj.get("is_fast_channel", False),
                        }
                        # Include direct manifest URLs if available (for FAST channels)
                        if "m3u8" in obj:
                            channel_info["m3u8"] = obj.get("m3u8")
                        if "mpd" in obj:
                            channel_info["mpd"] = obj.get("mpd")
                        channels.append(channel_info)

                    # Recursively check nested structures
                    for value in obj.values():
                        extract_channels(value)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_channels(item)

            extract_channels(page_data)
            return channels

        except requests.exceptions.RequestException as e:
            # Return empty list if channels page is not accessible
            return []

    def check_channel_geo_restriction(self, slug: str) -> Dict[str, Any]:
        """
        Check if a live channel is geo-restricted using /api/v1/stream/{slug}

        Args:
            slug: Channel slug

        Returns:
            Dictionary with:
            - is_geo_restricted: bool or None
            - status_code: HTTP status code
            - accessible: bool (True if 200, False otherwise)
            - error: str or None
        """
        self.ensure_authenticated()

        try:
            response = self.session.get(f"{self.base_url}/stream/{slug}", timeout=10)
            status_code = response.status_code

            result = {
                "status_code": status_code,
                "accessible": status_code == 200,
                "error": None,
            }

            if status_code == 200:
                result["is_geo_restricted"] = False
                # Optionally parse manifests from response
                try:
                    stream_data = response.json()
                    result["manifests"] = stream_data.get("manifests", [])
                except:
                    pass
            elif status_code == 403:
                result["is_geo_restricted"] = True
                # Try to get error message
                try:
                    error_data = response.json()
                    if error_data.get("message") == "MEDIA_GEO_RESTRICTED_ACCESS":
                        result["error"] = "Forbidden - Geo-restricted (channel)"
                    else:
                        result["error"] = f"Forbidden - {error_data.get('message', 'Unknown')}"
                except:
                    result["error"] = "Forbidden - Geo-restricted (channel)"
            elif status_code == 404:
                result["is_geo_restricted"] = None
                result["error"] = "Not found - Channel may not exist"
            else:
                result["is_geo_restricted"] = None
                result["error"] = f"Unexpected status code: {status_code}"

            return result

        except requests.exceptions.RequestException as e:
            return {
                "status_code": None,
                "accessible": False,
                "is_geo_restricted": None,
                "error": str(e),
            }

