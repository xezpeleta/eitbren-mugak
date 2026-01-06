# Makusi.eus API Documentation

## ⚠️ Important Note on API Keys

The API key `4_OrNV-xF_hgF-IKSFkQrJxg` referenced throughout this documentation is a **public API key** used in the Makusi.eus frontend JavaScript. It is not a secret and is visible in browser network requests. However, you still need valid user credentials (username/password) to authenticate and access content.

**Note**: Makusi.eus shares the same Gigya SSO authentication system as Primeran.eus. If you are already logged into Primeran.eus, you will automatically be authenticated on Makusi.eus as well.

---

## Base URLs

- **Main API**: `https://makusi.eus/api/v1/`
- **Raw API**: `https://makusi.eus/api/raw/v1/`
- **Video Manifests**: `https://makusi.eus/manifests/`
- **DRM License**: `https://makusi.eus/drm/widevine/`
- **Video CDN**: `https://cdn.makusi.eus/media/`
- **Image CDN**: `https://img.primeran.eus/imgproxy/` (shared with Primeran)
- **Storage CDN**: `https://cdnstorage.primeran.eus/` (shared with Primeran)
- **Web Assets CDN**: `https://cdnweb.makusi.eus/`

---

## Authentication

The platform uses **Gigya SSO** (SAP Customer Data Cloud) for authentication, **shared with Primeran.eus**.

### Authentication System Overview

- **SSO Provider**: Gigya (SAP Customer Data Cloud)
- **Primary Login Domain**: `https://login.primeran.eus/` (shared with Primeran)
- **Secondary SSO Domain**: `https://login.nireitb.eitb.eus/` (shared with Primeran)
- **API Key (Primary)**: `4_OrNV-xF_hgF-IKSFkQrJxg` (Makusi-specific)
- **API Key (SSO Segment)**: `4_uJplPIpbnazIi6T4FQ1YgA` (shared with Primeran)

---

### How to Authenticate Programmatically

#### Method 1: Using Gigya SDK (Recommended)

**Step 1: Load Gigya SDK**

```javascript
// Include Gigya SDK
<script src="https://cdns.eu1.gigya.com/js/gigya.js?apikey=4_OrNV-xF_hgF-IKSFkQrJxg"></script>
```

**Step 2: Login with Credentials**

```javascript
// Login using Gigya SDK
gigya.accounts.login({
    loginID: 'your-username-or-email',
    password: 'your-password',
    callback: function(response) {
        if (response.errorCode === 0) {
            console.log('Login successful!');
            console.log('UID:', response.UID);
            console.log('Session Token:', response.sessionInfo.sessionToken);
            console.log('Session Secret:', response.sessionInfo.sessionSecret);
        } else {
            console.error('Login failed:', response.errorMessage);
        }
    }
});
```

**Step 3: Get Account Information**

```javascript
// After login, get account details
gigya.accounts.getAccountInfo({
    callback: function(response) {
        if (response.errorCode === 0) {
            console.log('User Profile:', response.profile);
            console.log('Email:', response.profile.email);
        }
    }
});
```

---

#### Method 2: Using Direct API Calls

**Step 1: Login**

```bash
curl -X POST 'https://login.primeran.eus/accounts.login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'apiKey=4_OrNV-xF_hgF-IKSFkQrJxg' \
  -d 'loginID=your-username-or-email' \
  -d 'password=your-password' \
  -d 'format=json'
```

**Response**:
```json
{
  "errorCode": 0,
  "statusCode": 200,
  "sessionInfo": {
    "sessionToken": "st2.s.AcbDef...",
    "sessionSecret": "abcd1234..."
  },
  "UID": "1a2b3c4d5e6f...",
  "UIDSignature": "signature...",
  "signatureTimestamp": "1704390000"
}
```

**Step 2: Get Account Info**

```bash
curl -X POST 'https://login.primeran.eus/accounts.getAccountInfo' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'apiKey=4_OrNV-xF_hgF-IKSFkQrJxg' \
  -d 'sessionToken=st2.s.AcbDef...' \
  -d 'sessionSecret=abcd1234...' \
  -d 'format=json'
```

**Step 3: Use Session with Makusi API**

After successful login, the session cookies are automatically set by Gigya. Use these cookies for subsequent API requests:

```bash
# Get user profile
curl 'https://makusi.eus/api/v1/profiles/me' \
  --cookie 'glt_4_OrNV-xF_hgF-IKSFkQrJxg=...; gmid=...; ucid=...'
```

---

#### Method 3: Python Example

```python
import requests

# Configuration
GIGYA_API_KEY = "4_OrNV-xF_hgF-IKSFkQrJxg"
LOGIN_ENDPOINT = "https://login.primeran.eus/accounts.login"
ACCOUNT_INFO_ENDPOINT = "https://login.primeran.eus/accounts.getAccountInfo"

# Login credentials (same as Primeran)
username = "your-username-or-email"
password = "your-password"

# Step 1: Login
login_data = {
    'apiKey': GIGYA_API_KEY,
    'loginID': username,
    'password': password,
    'format': 'json'
}

session = requests.Session()
response = session.post(LOGIN_ENDPOINT, data=login_data)
login_result = response.json()

if login_result.get('errorCode') == 0:
    print("Login successful!")
    session_token = login_result['sessionInfo']['sessionToken']
    session_secret = login_result['sessionInfo']['sessionSecret']
    uid = login_result['UID']
    
    # Step 2: Get account info
    account_info_data = {
        'apiKey': GIGYA_API_KEY,
        'sessionToken': session_token,
        'sessionSecret': session_secret,
        'format': 'json'
    }
    
    account_response = session.post(ACCOUNT_INFO_ENDPOINT, data=account_info_data)
    account_info = account_response.json()
    
    if account_info.get('errorCode') == 0:
        print(f"User email: {account_info['profile']['email']}")
        print(f"User ID: {uid}")
    
    # Step 3: Use authenticated session with Makusi API
    # The session object now has the necessary cookies
    profile_response = session.get('https://makusi.eus/api/v1/profiles/me')
    print("Profile data:", profile_response.json())
    
    # Get user's watch progress
    progress_response = session.get('https://makusi.eus/api/v1/watching-progress')
    print("Watch progress:", progress_response.json())
    
    # Get user's list
    my_list_response = session.get('https://makusi.eus/api/v1/my-list')
    print("My list:", my_list_response.json())
    
else:
    print(f"Login failed: {login_result.get('errorMessage')}")
    print(f"Error code: {login_result.get('errorCode')}")
```

---

### Important Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/accounts.login` | POST | Login with username/email and password |
| `/accounts.getAccountInfo` | POST | Get account details |
| `/accounts.logout` | POST | Logout and invalidate session |
| `/api/v1/profiles/me` | GET | Get current user's Makusi profile |
| `/api/v1/profiles` | GET | List all profiles for the account |
| `/api/v1/watching-progress` | GET | Get user's watching progress |
| `/api/v1/my-list` | GET | Get user's saved content list |

---

### Session Management

**Cookies Set After Authentication**:
- `glt_4_OrNV-xF_hgF-IKSFkQrJxg`: Login token (Gigya)
- `gmid`: Gigya member ID
- `ucid`: User context ID
- `hasGmid`: Boolean flag indicating Gigya session
- Additional session cookies for Makusi domain

**Session Duration**:
- Sessions typically expire after 30-90 days of inactivity
- Tokens can be refreshed using the session token/secret pair

**Profile Management**:
- Each account can have multiple profiles (similar to Netflix)
- Profile ID is used for personalized recommendations and watch progress
- Profile ID format: UUID (e.g., `f4665272-a808-4a94-a092-b4a6232e8827`)

---

### Authentication Flow Diagram

```
1. User enters credentials
   ↓
2. POST to /accounts.login with apiKey + credentials
   ↓
3. Gigya validates credentials
   ↓
4. Session tokens returned (sessionToken, sessionSecret, UID)
   ↓
5. Browser/client stores session cookies
   ↓
6. All API requests include session cookies
   ↓
7. Makusi validates session via Gigya SSO
   ↓
8. Access granted to content and user data
```

---

### Error Codes

Common Gigya error codes:

| Code | Description |
|------|-------------|
| 0 | Success |
| 403005 | Invalid login credentials |
| 403042 | Invalid API key |
| 403120 | Missing required parameter |
| 403047 | Session expired or invalid |
| 500000 | General server error |

---

### Security Notes

1. **Never hardcode credentials** in your source code
2. **Use environment variables** for sensitive data
3. **Session tokens should be kept secure** - they provide full account access
4. **HTTPS only** - Never send credentials over unencrypted connections
5. **Respect rate limits** - Gigya implements rate limiting on authentication endpoints
6. **Cookie security** - Session cookies are marked as HttpOnly and Secure
7. **Shared SSO** - Logging into Primeran.eus automatically authenticates you for Makusi.eus

---

## Content API Endpoints

### 1. Get Media Details

**Endpoint**: `GET /api/v1/media/{slug}`

**Description**: Retrieves detailed information about a specific movie, series, or episode.

**Example**:
```
GET https://makusi.eus/api/v1/media/heidi-katamotzaren-erreskatea
```

**Response**: JSON with complete media metadata. The response includes:

**Media Types**:
- **Video content** (`media_type: "video"`): Uses DASH manifests for streaming
- **Audio content** (`media_type: "audio"`): Uses direct MP3 file URLs (no DASH manifests)

For audio content, the `manifests` field contains MP3 file URLs instead of DASH manifest URLs:
```json
{
  "manifests": [
    {
      "manifestURL": "https://cdn.primeran.eus/media/audios/23lufs_GUAU_10002379_5882603_01- Uxue Alberdi Am.mp3",
      "type": "mp3"
    }
  ]
}
```

**Response**: JSON with complete media metadata. The response includes:

**Core Fields:**
- `id` - Numeric media ID
- `slug` - URL-friendly identifier
- `title` - Content title
- `type` - Content type (`vod`, `movie`, `documentary`, `concert`, etc.)
- `description` - Full description/synopsis
- `duration` - Duration in seconds
- `production_year` - Production/release year
- `collection` - Content collection type (`media`, `series`, etc.)

**Access & Restrictions:**
- `access_restriction` - Access level (`registration_required`, `public`, `subscription_required`, etc.)
- `age_rating` - Age rating object with `id`, `age`, `label`, `background_color`, `text_color`
- `available_until` - Expiration date (ISO 8601 format)
- `offline_expiration_date` - Offline availability expiration

**Media Assets:**
- `images` - Array of image objects with CDN URLs, dimensions, formats (landscape, portrait, slider, etc.)
- `manifests` - Array of streaming manifest objects with:
  - `manifestURL` - Path to DASH/HLS manifest
  - `type` - Stream type (`dash`, `hls`)
  - `drmConfig` - DRM configuration (Widevine, PlayReady, FairPlay)
  - `thumbnailMetadata` - Thumbnail/preview configuration

**Audio/Subtitle Tracks:**
- `audios` - Array of available audio languages with `id`, `code`, `label`, `transcoding_code`
- `subtitle` / `subtitles` - Arrays of subtitle track objects with VTT file URLs and language info

**Additional Metadata:**
- `custom_tags` - Array of custom tag objects
- `eitb_visual_radio` - Boolean flag
- `is_external_manifest` - Boolean flag
- `is_playable_offline` - Boolean flag
- `media_format` - Format type (e.g., `episode`)
- `media_type` - Media type (e.g., `video`)
- `theme` - Complete theme configuration object (includes all UI icons, logos, colors)

**Note**: This endpoint is for **individual media** (movies, documentaries, concerts, or individual episodes). For TV series, use the `/api/v1/series/{slug}` endpoint instead.

**Storage**: The complete response is stored in the database `metadata` field as a JSON blob. See `METHODOLOGY.md` for details on what's stored.

---

### 2. Get Series Details

**Endpoint**: `GET /api/v1/series/{slug}`

**Description**: Retrieves detailed information about a TV series, including all seasons and episodes.

**Example**:
```
GET https://makusi.eus/api/v1/series/goazen-d12
```

**Response**: JSON with series metadata including:
- Series title, description
- Number of seasons
- Episodes for each season
- Series metadata (director, cast, genres, etc.)
- First episode information

**Key Fields**:
```json
{
  "id": 12345,
  "slug": "goazen-d12",
  "title": "GO!azen D12",
  "description": "Basakabi eraberrituak adingabeen zentrotik etorritako gazteak hartuko ditu...",
  "type": "series",
  "production_year": 2025,
  "seasons": [
    {
      "id": 1,
      "season_number": 1,
      "episodes": [
        {
          "id": 67890,
          "slug": "goazen-d12-1-ardi-beltzak",
          "title": "D12: 1. Ardi beltzak",
          "episode_number": 1,
          "duration": 3900,
          "description": "...",
          "published_on": "2025-01-02T23:01:00+00:00"
        }
      ]
    }
  ],
  "first_episode": {
    "slug": "goazen-d12-1-ardi-beltzak",
    "production_year": 2025,
    "access_restriction": "registration_required"
  }
}
```

**Important Notes**:
1. **Series do NOT have manifest URLs** - Only individual episodes have manifests
2. To check geo-restrictions for a series, test each episode individually
3. Each episode has its own `slug` that can be used with the manifest endpoint
4. Series structure: Series → Seasons → Episodes
5. Season ordering: the **smallest `season_number` is the first season** (D1), increasing with later seasons (D2, D3, …); API may return seasons in reverse order.

---

### 2.1. Get Series Clips

**Endpoint**: `GET /api/v1/series/{series_id}/clip`

**Description**: Retrieves clips/previews for a series.

**Example**:
```
GET https://makusi.eus/api/v1/series/2158/clip
```

**Response**: JSON with clip information for the series.

---

**Testing Geo-Restrictions for Series**:
```python
# ✗ WRONG - This will return 404
manifest_url = f"https://makusi.eus/manifests/{series_slug}/eu/widevine/dash.mpd"

# ✓ CORRECT - Get series first, then test episodes
series_response = session.get(f"https://makusi.eus/api/v1/series/{series_slug}")
series_data = series_response.json()

for season in series_data['seasons']:
    for episode in season['episodes']:
        episode_slug = episode['slug']
        # Test each episode's manifest
        manifest_url = f"https://makusi.eus/manifests/{episode_slug}/eu/widevine/dash.mpd"
        response = session.get(manifest_url)
        # Check status: 200 = accessible, 403 = geo-restricted
```

---

### 3. Get Menu/Navigation

**Endpoint**: `GET /api/v1/menus/{menu_id}`

**Description**: Retrieves navigation menu structure.

**Example**:
```
GET https://makusi.eus/api/v1/menus/6
```

**Response**: Menu items with links and categories.

---

## Application Configuration API

### 4. Get Application Settings

**Endpoint**: `GET /api/v1/application`

**Description**: Retrieves complete application configuration including theme, menus, settings, and branding.

**Example**:
```
GET https://makusi.eus/api/v1/application
```

**Response**: JSON with comprehensive application configuration:
- Application ID and name
- Theme configuration (colors, logos, icons)
- Menu structure
- Base URLs and API endpoints
- Gigya SSO configuration
- Analytics configuration (Youbora, ComScore, Adobe, Google)
- SMTP settings
- Legal documents and footer
- Feature flags and settings

**Key Fields**:
```json
{
  "id": "makusi-application-id",
  "name": "makusi",
  "web_url": "https://makusi.eus",
  "sso_api_key": "4_OrNV-xF_hgF-IKSFkQrJxg",
  "sso_api_key_tv": "4_OrNV-xF_hgF-IKSFkQrJxg",
  "youbora_account_code": "etb",
  "comscore_publisher_id": "14621447",
  "theme": { /* theme configuration */ },
  "menu": { /* navigation menu */ }
}
```

---

### 5. Get UI Settings

**Endpoint**: `GET /api/v1/settings`

**Description**: Retrieves user interface settings and configuration options.

**Example**:
```
GET https://makusi.eus/api/v1/settings
```

**Response**: JSON with UI configuration:
- Available UI languages (`eu` - Euskara, `es` - Gaztelania)
- Age ratings and content classifications
- Media languages with transcoding codes
- Image format specifications
- Default language code
- Maximum profiles per account
- Watching progress tracking interval (15000ms = 15 seconds)
- Tudum (intro/outro) configuration with DRM manifests
- Feature flags

**Key Fields**:
```json
{
  "ui_languages": [
    {"id": 2, "code": "eu", "label": "Euskara"},
    {"id": 1, "code": "es", "label": "Gaztelania"}
  ],
  "age_ratings": [
    {"id": 9, "age": 11, "label": "Haurra"},
    {"id": 10, "age": 12, "label": "Gaztea"},
    {"id": 11, "age": 18, "label": "Orokorra"}
  ],
  "media_languages": [
    {"id": 1, "label": "Euskara", "code": "eu", "transcoding_code": "baq"},
    {"id": 2, "label": "Gaztelania", "code": "es", "transcoding_code": "spa"}
  ],
  "max_profiles": 6,
  "watching_progress_interval": 15000,
  "current_lang": "eu"
}
```

---

### 6. Get UI Text Strings

**Endpoint**: `GET /api/v1/settings/texts`

**Description**: Retrieves all localized UI text strings for the current language.

**Example**:
```
GET https://makusi.eus/api/v1/settings/texts
```

**Response**: JSON object with all UI strings:
```json
{
  "app": "Makusi",
  "login_title": "Saioa hasi",
  "login_remember": "Pasahitza ahaztu duzu?",
  "form_field_email": "Helbide elektronikoa",
  "form_field_password": "Pasahitza",
  "player_play": "Ikusi",
  "error_generic": "Errorea",
  /* hundreds more text strings */
}
```

**Use Case**: Load all localized strings for the UI in the user's selected language.

---

### 7. Get Available Avatars

**Endpoint**: `GET /api/v1/avatars`

**Description**: Retrieves list of available avatar images for user profiles.

**Example**:
```
GET https://makusi.eus/api/v1/avatars
```

**Response**: Array of avatar objects:
```json
[
  {
    "id": 1,
    "image": "https://cdnstorage.primeran.eus/directus/eitb/54d44b94-0e7d-4b43-ab3c-41c7e980b305.jpg"
  },
  {
    "id": 2,
    "image": "https://cdnstorage.primeran.eus/directus/eitb/a27868e7-b856-4f72-81c1-f0e501ed80bd.jpg"
  }
  /* more avatars */
]
```

---

### 8. Get Home Content

**Endpoint**: `GET /api/v1/home`

**Description**: Retrieves home page content sections and carousels.

**Example**:
```
GET https://makusi.eus/api/v1/home
```

**Response**: JSON with home page structure:
- Featured content carousels
- Continue watching section
- Recommended content
- Category rows
- Personalized content based on user profile

---

### 9. Get User Profile

**Endpoint**: `GET /api/v1/profiles/me`

**Description**: Retrieves the current authenticated user's profile information.

**Example**:
```
GET https://makusi.eus/api/v1/profiles/me
```

**Response**: JSON with user profile data including:
- Profile ID
- Profile name
- Avatar
- Language preferences
- Watch history settings

---

### 10. Get All Profiles

**Endpoint**: `GET /api/v1/profiles`

**Description**: Retrieves all profiles associated with the authenticated account.

**Example**:
```
GET https://makusi.eus/api/v1/profiles
```

**Response**: Array of profile objects for the account.

---

### 11. Get Watching Progress

**Endpoint**: `GET /api/v1/watching-progress`

**Description**: Retrieves the user's watching progress for all content.

**Example**:
```
GET https://makusi.eus/api/v1/watching-progress
```

**Response**: JSON array with watching progress entries:
```json
[
  {
    "media_id": 12345,
    "slug": "heidi-katamotzaren-erreskatea",
    "progress": 1200,
    "duration": 4710,
    "last_watched": "2025-01-05T10:30:00Z"
  }
]
```

---

### 12. Get My List

**Endpoint**: `GET /api/v1/my-list`

**Description**: Retrieves the user's saved content list (favorites/watchlist).

**Example**:
```
GET https://makusi.eus/api/v1/my-list
```

**Response**: JSON array with saved content items.

---

### 13. Get Language Selector

**Endpoint**: `GET /api/v1/language-selector`

**Description**: Retrieves available languages and language selection configuration.

**Example**:
```
GET https://makusi.eus/api/v1/language-selector
```

**Response**: JSON with language options and configuration.

---

## Video Streaming API

### 14. Get DASH Manifest

**Endpoint**: `GET /manifests/{slug}/{language}/{drm_type}/dash.mpd`

**Description**: Retrieves the MPEG-DASH manifest for video streaming.

**Parameters**:
- `slug`: Media identifier (e.g., `heidi-katamotzaren-erreskatea`)
- `language`: Language code (e.g., `eu` for Basque)
- `drm_type`: DRM type (e.g., `widevine`)

**Query Parameters**:
- `include_tudum`: `true` (includes intro/outro markers)

**Example**:
```
GET https://makusi.eus/manifests/heidi-katamotzaren-erreskatea/eu/widevine/dash.mpd?include_tudum=true
```

**Response**: MPEG-DASH MPD XML manifest with:
- Video quality variants (360p, 720p, 1080p, etc.)
- Audio tracks
- Subtitle tracks
- Segment URLs

---

### 15. Get Widevine DRM License

**Endpoint**: `POST /drm/widevine/{media_id}/{session_id}`

**Description**: Requests a Widevine DRM license to decrypt video content.

**Parameters**:
- `media_id`: Numeric media ID (e.g., `112598`)
- `session_id`: UUID session identifier

**Query Parameters**:
- `th`: Token hash
- `d`: Timestamp (in milliseconds)
- `sig`: JWT signature

**Example**:
```
POST https://makusi.eus/drm/widevine/112598/662f4a9a-1871-4d37-8d0c-d58adcc62b16?th=3b23c3&d=3971804340000&sig=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body**: Widevine challenge (binary protobuf)

**Response**: Widevine license (binary protobuf)

---

### 16. Get Video Segments

**Endpoint**: `GET /media/{content_hash}/cenc/{quality}/{segment}`

**Description**: Retrieves encrypted video/audio segments.

**Parameters**:
- `content_hash`: MD5 hash of content
- `quality`: Quality level (e.g., `360`, `720`, `1080`, or `audio_baq`, `audio_und`)
- `segment`: Segment file (`init.mp4` for initialization, `{n}.m4s` for media segments)

**Examples**:
```
# Video initialization segment (1080p)
GET https://cdn.makusi.eus/media/3332299a9e2f4331448afec033830a76/cenc/1080/init.mp4

# Video segment #1 (1080p)
GET https://cdn.makusi.eus/media/3332299a9e2f4331448afec033830a76/cenc/1080/1.m4s

# Audio initialization segment (Basque)
GET https://cdn.makusi.eus/media/3332299a9e2f4331448afec033830a76/cenc/audio_baq/init.mp4

# Audio segment #1 (Basque)
GET https://cdn.makusi.eus/media/3332299a9e2f4331448afec033830a76/cenc/audio_baq/1.m4s
```

**Response**: Binary MP4 segment (encrypted with CENC)

**Notes**:
- Videos use CENC (Common Encryption) with Widevine
- Each quality has its own content hash
- Segments are typically 4-6 seconds long

---

### 17. Track Watching Progress

**Endpoint**: `POST /api/raw/v1/watching-progress`

**Description**: Updates the user's watching progress for resume functionality.

**Example**:
```
POST https://makusi.eus/api/raw/v1/watching-progress
```

**Request Body**: JSON with:
- Media ID
- Current playback position (in seconds)
- Total duration

**Response**: 204 No Content (on success)

---

## Image API

### 18. Get Optimized Images

**Endpoint**: `GET /imgproxy/{size}/plain/{cdn_url}@{format}`

**Description**: Returns optimized/resized images via imgproxy.

**Parameters**:
- `size`: Image size preset (e.g., `sm`, `xl`)
- `cdn_url`: Full CDN URL to original image
- `format`: Output format (e.g., `webp`)

**Example**:
```
GET https://img.primeran.eus/imgproxy/xl/plain/https://cdnstorage.primeran.eus/directus/eitb/846582cd-fa7b-430f-bfe2-96cd1238e55f.jpg@webp
```

**Response**: Optimized image (WebP format)

---

## Analytics & Tracking

### 19. Youbora Analytics

The platform uses Youbora for video analytics:

**Endpoints**:
- `GET https://a-fds.youborafds01.com/data` - Fast data service
- `GET https://infinity-c35.youboranqs01.com/init` - Session initialization
- `GET https://infinity-c35.youboranqs01.com/start` - Playback start
- `GET https://infinity-c35.youboranqs01.com/joinTime` - Join time tracking
- `GET https://infinity-c35.youboranqs01.com/ping` - Periodic heartbeat
- `GET https://infinity-c35.youboranqs01.com/seek` - Seek tracking

**Parameters Tracked**:
- Account code: `etb`
- Player: `Shaka v4.16.9`
- Content metadata (title, duration, type)
- Playback metrics (bitrate, throughput, dropped frames)
- User session info

---

### 20. ComScore Analytics

The platform uses ComScore for audience measurement:

**Endpoints**:
- `GET https://sb.scorecardresearch.com/b` - Beacon
- `GET https://sb.scorecardresearch.com/p` - Pixel tracking

**Parameters Tracked**:
- Publisher ID: `c2=14621447`
- Publisher: `EITB / MAKUSI`
- Page views and video events

---

## Content Delivery

### CDN Structure

**Storage CDN** (`cdnstorage.primeran.eus`):
- Static assets (images, icons, player libraries)
- Uses Directus CMS structure: `/directus/eitb/{uuid}.{ext}`
- **Shared with Primeran.eus**

**Video CDN** (`cdn.makusi.eus`):
- Video and audio segments
- Organized by content hash and quality level
- **Makusi-specific**

**Web Assets CDN** (`cdnweb.makusi.eus`):
- JavaScript bundles
- CSS files
- Public assets
- **Makusi-specific**

---

## Video Player

### Technology Stack

- **Player**: Shaka Player v4.16.9
- **Streaming Protocol**: MPEG-DASH
- **DRM**: Widevine
- **Encryption**: CENC (Common Encryption)
- **Analytics**: Youbora v6.8.9-shaka-js (adapter), ComScore

### Available Qualities

Based on observed traffic:
- **Video**: 360p, 720p, 1080p (adaptive bitrate)
- **Audio**: Multiple language tracks (Basque `baq`, undefined `und`)
- **Bitrate**: Adaptive (up to ~5 Mbps for 1080p)

### Audio Languages

- `eu` / `baq`: Basque (Euskara)
- `und`: Undefined/Original

### Subtitle Languages

- `eu`: Basque (Euskara)
- `es`: Spanish (Gaztelania)

---

## Notes

1. **DRM Protection**: All video content is protected with Widevine DRM. The license server validates user authentication and generates time-limited licenses.

2. **Adaptive Streaming**: The player automatically selects the best quality based on available bandwidth.

3. **Session Management**: Video playback requires valid session cookies from the authentication system.

4. **GDPR Compliance**: The platform implements GDPR consent management for analytics tracking.

5. **Cross-Origin**: The CDN endpoints support CORS for browser playback.

6. **Shared Infrastructure**: Makusi.eus shares CDN infrastructure, authentication system, and some API endpoints with Primeran.eus.

---

## Example Playback Flow

1. User authenticates via `login.primeran.eus` (shared SSO)
2. User selects content → Navigate to `/ikusi/m/{slug}` or `/ikusi/s/{slug}`
3. Fetch media metadata via `/api/v1/media/{slug}` or `/api/v1/series/{slug}`
4. User clicks "Watch" → Navigate to `/ikusi/w/{slug}`
5. Player requests DASH manifest: `/manifests/{slug}/{lang}/widevine/dash.mpd`
6. Player initializes Widevine DRM
7. Player requests DRM license: `POST /drm/widevine/{id}/{session}`
8. Player fetches video/audio segments from CDN
9. Player periodically reports progress: `POST /api/raw/v1/watching-progress`
10. Player sends analytics to Youbora and ComScore

---

## Security Considerations

- **Token-Based DRM**: The DRM license endpoint requires valid JWT signatures
- **Time-Limited Access**: DRM licenses include expiration timestamps
- **Session Validation**: API endpoints validate user session cookies
- **HTTPS Only**: All endpoints use encrypted HTTPS connections
- **Shared SSO**: Authentication is shared with Primeran.eus - logging into one platform authenticates you for both

---

## Additional Resources

- **Player Library**: Shaka Player (https://github.com/shaka-project/shaka-player)
- **DASH Specification**: MPEG-DASH ISO/IEC 23009-1
- **Widevine DRM**: Google Widevine CDM
- **Analytics**: Youbora (NPAW), ComScore

---

*Documentation generated through reverse engineering of network traffic on 2026-01-05*
