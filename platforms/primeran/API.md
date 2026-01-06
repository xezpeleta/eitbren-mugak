# Primeran.eus API Documentation

## ⚠️ Important Note on API Keys

The API key `4_iXtBSPAhyZYN6kg3DlaQuQ` referenced throughout this documentation is a **public API key** used in the Primeran.eus frontend JavaScript. It is not a secret and is visible in browser network requests. However, you still need valid user credentials (username/password) to authenticate and access content.

---

## Base URLs

- **Main API**: `https://primeran.eus/api/v1/`
- **Raw API**: `https://primeran.eus/api/raw/v1/`
- **Video Manifests**: `https://primeran.eus/manifests/`
- **DRM License**: `https://primeran.eus/drm/widevine/`
- **CDN**: `https://cdn.primeran.eus/media/`
- **Image CDN**: `https://img.primeran.eus/imgproxy/`
- **Storage CDN**: `https://cdnstorage.primeran.eus/`

---

## Authentication

The platform uses **Gigya SSO** (SAP Customer Data Cloud) for authentication.

### Authentication System Overview

- **SSO Provider**: Gigya (SAP Customer Data Cloud)
- **Primary Login Domain**: `https://login.primeran.eus/`
- **Secondary SSO Domain**: `https://login.nireitb.eitb.eus/`
- **API Key (Primary)**: `4_iXtBSPAhyZYN6kg3DlaQuQ`
- **API Key (SSO Segment)**: `4_uJplPIpbnazIi6T4FQ1YgA`

---

### How to Authenticate Programmatically

#### Method 1: Using Gigya SDK (Recommended)

**Step 1: Load Gigya SDK**

```javascript
// Include Gigya SDK
<script src="https://cdns.eu1.gigya.com/js/gigya.js?apikey=4_iXtBSPAhyZYN6kg3DlaQuQ"></script>
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
  -d 'apiKey=4_iXtBSPAhyZYN6kg3DlaQuQ' \
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
  -d 'apiKey=4_iXtBSPAhyZYN6kg3DlaQuQ' \
  -d 'sessionToken=st2.s.AcbDef...' \
  -d 'sessionSecret=abcd1234...' \
  -d 'format=json'
```

**Step 3: Use Session with Primeran API**

After successful login, the session cookies are automatically set by Gigya. Use these cookies for subsequent API requests:

```bash
# Get user profile
curl 'https://primeran.eus/api/v1/profiles/me' \
  --cookie 'glt_4_iXtBSPAhyZYN6kg3DlaQuQ=...; gmid=...; ucid=...'
```

---

#### Method 3: Python Example

```python
import requests

# Configuration
GIGYA_API_KEY = "4_iXtBSPAhyZYN6kg3DlaQuQ"
LOGIN_ENDPOINT = "https://login.primeran.eus/accounts.login"
ACCOUNT_INFO_ENDPOINT = "https://login.primeran.eus/accounts.getAccountInfo"

# Login credentials
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
    
    # Step 3: Use authenticated session with Primeran API
    # The session object now has the necessary cookies
    profile_response = session.get('https://primeran.eus/api/v1/profiles/me')
    print("Profile data:", profile_response.json())
    
    # Get user's watch progress
    progress_response = session.get('https://primeran.eus/api/v1/watching-progress')
    print("Watch progress:", progress_response.json())
    
    # Get user's list
    my_list_response = session.get('https://primeran.eus/api/v1/my-list')
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
| `/api/v1/profiles/me` | GET | Get current user's Primeran profile |
| `/api/v1/profiles` | GET | List all profiles for the account |
| `/api/v1/watching-progress` | GET | Get user's watching progress |
| `/api/v1/my-list` | GET | Get user's saved content list |

---

### Session Management

**Cookies Set After Authentication**:
- `glt_4_iXtBSPAhyZYN6kg3DlaQuQ`: Login token (Gigya)
- `gmid`: Gigya member ID
- `ucid`: User context ID
- `hasGmid`: Boolean flag indicating Gigya session
- Additional session cookies for Primeran domain

**Session Duration**:
- Sessions typically expire after 30-90 days of inactivity
- Tokens can be refreshed using the session token/secret pair

**Profile Management**:
- Each account can have multiple profiles (similar to Netflix)
- Profile ID is used for personalized recommendations and watch progress
- Profile ID format: UUID (e.g., `17d8a933-d8b2-4331-a83e-3735f3094732`)

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
7. Primeran validates session via Gigya SSO
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

---

## Content API Endpoints

### 1. Get Media Details

**Endpoint**: `GET /api/v1/media/{slug}`

**Description**: Retrieves detailed information about a specific movie, series, or episode.

**Example**:
```
GET https://primeran.eus/api/v1/media/la-infiltrada
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

**Example Response:**
```json
{
  "id": 112598,
  "slug": "la-infiltrada",
  "title": "La infiltrada",
  "type": "vod",
  "description": "Hainbat urtez ezker abertzaleko giroetan...",
  "duration": 6817,
  "production_year": 2024,
  "access_restriction": "registration_required",
  "age_rating": {
    "id": 3,
    "age": 12,
    "label": "+12",
    "background_color": "#FFC23B",
    "text_color": "#000000"
  },
  "available_until": "2095-11-10T22:59:00+00:00",
  "images": [
    {
      "id": 76121,
      "file": "https://cdnstorage.primeran.eus/directus/eitb/56bf82d4-9a4a-43cb-a95a-15575085d4f7.jpg",
      "width": 3840,
      "format": 6,
      "height": 1380,
      "has_text": true
    }
  ],
  "manifests": [
    {
      "manifestURL": "/manifests/la-infiltrada/eu/widevine/dash.mpd",
      "type": "dash",
      "drmConfig": {
        "type": "widevine",
        "licenseAcquisitionURL": "/drm/widevine/112598/662f4a9a-1871-4d37-8d0c-d58adcc62b16"
      },
      "thumbnailMetadata": {
        "tileDuration": 200,
        "thumbnailDuration": 10,
        "url": "https://cdn.primeran.eus/media/.../trickplay/tiles/{{index}}.jpg"
      }
    }
  ],
  "audios": [
    {
      "id": 1,
      "code": "eu",
      "label": "Euskara",
      "transcoding_code": "baq"
    }
  ],
  "subtitle": [
    {
      "id": 92505,
      "file": "https://cdnstorage.primeran.eus/directus/eitb/2b3dd3df-023e-47e1-aa71-40557cc0e0e0.vtt",
      "language": {
        "id": 1,
        "code": "eu",
        "label": "Euskara",
        "transcoding_code": "baq"
      }
    }
  ],
  "custom_tags": [
    {
      "id": 114,
      "icon": "https://cdnstorage.primeran.eus/directus/eitb/52a3db70-1e33-4a18-ba64-b3197bd2f2ce.png",
      "display": "Euskal Zinema Icon",
      "position": "bottom-right"
    }
  ],
  "is_playable_offline": true,
  "media_type": "video",
  "theme": { /* large theme configuration object */ }
}
```

**Note**: This endpoint is for **individual media** (movies, documentaries, concerts, or individual episodes). For TV series, use the `/api/v1/series/{slug}` endpoint instead.

**Storage**: The complete response is stored in the database `metadata` field as a JSON blob. See `METHODOLOGY.md` for details on what's stored.

---

### 2. Get Series Details

**Endpoint**: `GET /api/v1/series/{slug}`

**Description**: Retrieves detailed information about a TV series, including all seasons and episodes.

**Example**:
```
GET https://primeran.eus/api/v1/series/lau-hankan
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
  "slug": "lau-hankan",
  "title": "Lau hankan",
  "description": "Maskotak ez ezik, gure familiaren parte diren animalien programa.",
  "type": "podcast",
  "production_year": 2025,
  "seasons": [
    {
      "id": 1,
      "season_number": 1,
      "episodes": [
        {
          "id": 67890,
          "slug": "lau-hankan-d1-1-atala",
          "title": "1. atala",
          "episode_number": 1,
          "duration": 3240,
          "description": "...",
          "published_on": "2025-01-02T23:01:00+00:00"
        },
        {
          "id": 67891,
          "slug": "lau-hankan-d1-2-atala",
          "title": "2. atala",
          "episode_number": 2,
          "duration": 3060
        }
      ]
    }
  ],
  "first_episode": {
    "slug": "lau-hankan-d1-1-atala",
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
5. Season ordering: the **smallest `season_number` is the first season** (D1), increasing with later seasons (D2, D3, …); the API may return seasons newest-first.

**Testing Geo-Restrictions for Series**:
```python
# ✗ WRONG - This will return 404
manifest_url = f"https://primeran.eus/manifests/{series_slug}/eu/widevine/dash.mpd"

# ✓ CORRECT - Get series first, then test episodes
series_response = session.get(f"https://primeran.eus/api/v1/series/{series_slug}")
series_data = series_response.json()

for season in series_data['seasons']:
    for episode in season['episodes']:
        episode_slug = episode['slug']
        # Test each episode's manifest
        manifest_url = f"https://primeran.eus/manifests/{episode_slug}/eu/widevine/dash.mpd"
        response = session.get(manifest_url)
        # Check status: 200 = accessible, 403 = geo-restricted
```

---

### 3. Get Menu/Navigation

**Endpoint**: `GET /api/v1/menus/{menu_id}`

**Description**: Retrieves navigation menu structure.

**Example**:
```
GET https://primeran.eus/api/v1/menus/4
```

**Response**: Menu items with links and categories.

---

## Application Configuration API

### 4. Get Application Settings

**Endpoint**: `GET /api/v1/application`

**Description**: Retrieves complete application configuration including theme, menus, settings, and branding.

**Example**:
```
GET https://primeran.eus/api/v1/application
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
  "id": "fac904d9-11c8-4037-93f1-f56ca2eacf5b",
  "name": "primeran",
  "web_url": "https://primeran.eus",
  "sso_api_key": "4_iXtBSPAhyZYN6kg3DlaQuQ",
  "sso_api_key_tv": "4_iXtBSPAhyZYN6kg3DlaQuQ",
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
GET https://primeran.eus/api/v1/settings
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
GET https://primeran.eus/api/v1/settings/texts
```

**Response**: JSON object with all UI strings:
```json
{
  "app": "Primeran",
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
GET https://primeran.eus/api/v1/avatars
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
  /* 21 avatars total */
]
```

---

### 8. Get Home Content

**Endpoint**: `GET /api/v1/home`

**Description**: Retrieves home page content sections and carousels.

**Example**:
```
GET https://primeran.eus/api/v1/home
```

**Response**: JSON with home page structure:
- Featured content carousels
- Continue watching section
- Recommended content
- Category rows
- Personalized content based on user profile

---

## Smart TV Integration

### TV Device Registration Flow

Primeran supports Smart TV and streaming device integration through a QR code or device code pairing system.

---

### 9. TV Registration Page

**Endpoint**: `GET /tv`

**URL**: `https://primeran.eus/tv`

**Description**: Landing page for TV device registration. Displays QR code and instructions.

**User Flow**:
1. User opens Primeran app on Smart TV
2. TV displays a 6-digit code
3. User navigates to `https://primeran.eus/tv` on mobile/computer
4. User scans QR code or enters 6-digit code
5. User logs in (if not already authenticated)
6. Device is linked to user account

---

### 10. Register Specific Device

**Endpoint**: `GET /tv/{device_code}`

**URL Pattern**: `https://primeran.eus/tv/268861`

**Description**: Device-specific registration page where user confirms linking.

**Parameters**:
- `device_code`: 6-digit code displayed on TV (e.g., `268861`)

**Process**:
1. User enters device code or scans QR
2. System validates code
3. User authenticates via Gigya SSO
4. Device is linked to user account
5. Redirect to success page

---

### 11. Registration Success

**Endpoint**: `GET /tv/success`

**URL**: `https://primeran.eus/tv/success`

**Description**: Success confirmation page after device registration.

**Response**: 
- Confirmation message
- Instructions to return to TV
- Automatic device activation

**Gigya API Integration**:
```
https://login.nireitb.eitb.eus/js/Api.htm?apiKey=4_iXtBSPAhyZYN6kg3DlaQuQ&version=latest&build=18305&flavor=base&serviceName=apiService
```

**Parameters**:
- `apiKey`: `4_iXtBSPAhyZYN6kg3DlaQuQ`
- `build`: `18305`
- `flavor`: `base`
- `serviceName`: `apiService`

---

### TV Authentication Flow Diagram

```
┌──────────────┐
│   Smart TV   │
│  Opens App   │
└──────┬───────┘
       │
       │ Generates Device Code
       │
       ▼
┌──────────────────┐
│ Display 6-digit  │
│   Code: 268861   │
│   + QR Code      │
└──────────────────┘
       │
       │ User scans QR or
       │ visits primeran.eus/tv
       │
       ▼
┌──────────────────┐
│   Mobile/Web     │
│ Enters code or   │
│  Scans QR code   │
└──────┬───────────┘
       │
       │ Redirects to
       │ /tv/268861
       │
       ▼
┌──────────────────┐
│  User Logs In    │
│  (Gigya SSO)     │
└──────┬───────────┘
       │
       │ Device linked
       │
       ▼
┌──────────────────┐
│  /tv/success     │
│ "Device linked!" │
└──────┬───────────┘
       │
       │ TV polls for
       │ activation
       │
       ▼
┌──────────────────┐
│   Smart TV       │
│ Authenticated!   │
│  Ready to play   │
└──────────────────┘
```

---

### TV-Specific Configuration

**From Application Settings**:
```json
{
  "sso_api_key_tv": "4_iXtBSPAhyZYN6kg3DlaQuQ",
  "tv_login_background_image": "https://cdnstorage.primeran.eus/directus/eitb/37ffe739-63d9-4f61-8264-f12548be4f87.jpg",
  "login_qr_image": "https://cdnstorage.primeran.eus/directus/eitb/15d4e4b5-d20d-4e12-8e04-7c18cff095c1.png",
  "chromecast_app_id": "7B5BBE9A",
  "chromecast_logo": "https://cdnstorage.primeran.eus/directus/eitb/587703e5-53ab-4b7a-8d5a-f3c74a17eb59.svg",
  "chromecast_splash_image": "https://cdnstorage.primeran.eus/directus/eitb/3d4d2879-5bc0-4660-932c-a427317fbfba.jpg"
}
```

---

## Video Streaming API

### 12. Get DASH Manifest

**Endpoint**: `GET /manifests/{slug}/{language}/{drm_type}/dash.mpd`

**Description**: Retrieves the MPEG-DASH manifest for video streaming.

**Parameters**:
- `slug`: Media identifier (e.g., `la-infiltrada`)
- `language`: Language code (e.g., `eu` for Basque)
- `drm_type`: DRM type (e.g., `widevine`)

**Query Parameters**:
- `include_tudum`: `true` (includes intro/outro markers)

**Example**:
```
GET https://primeran.eus/manifests/la-infiltrada/eu/widevine/dash.mpd?include_tudum=true
```

**Response**: MPEG-DASH MPD XML manifest with:
- Video quality variants (360p, 720p, 1080p, etc.)
- Audio tracks
- Subtitle tracks
- Segment URLs

---

### 13. Get Widevine DRM License

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
POST https://primeran.eus/drm/widevine/112598/662f4a9a-1871-4d37-8d0c-d58adcc62b16?th=3b23c3&d=3971804340000&sig=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body**: Widevine challenge (binary protobuf)

**Response**: Widevine license (binary protobuf)

---

### 14. Get Video Segments

**Endpoint**: `GET /media/{content_hash}/cenc/{quality}/{segment}`

**Description**: Retrieves encrypted video/audio segments.

**Parameters**:
- `content_hash`: MD5 hash of content
- `quality`: Quality level (e.g., `360`, `720`, `1080`, or `audio_baq`, `audio_und`)
- `segment`: Segment file (`init.mp4` for initialization, `{n}.m4s` for media segments)

**Examples**:
```
# Video initialization segment (1080p)
GET https://cdn.primeran.eus/media/a242dfb25540853d4403554f0ee858c8/cenc/1080/init.mp4

# Video segment #1 (1080p)
GET https://cdn.primeran.eus/media/a242dfb25540853d4403554f0ee858c8/cenc/1080/1.m4s

# Audio initialization segment (Basque)
GET https://cdn.primeran.eus/media/a242dfb25540853d4403554f0ee858c8/cenc/audio_baq/init.mp4

# Audio segment #1 (Basque)
GET https://cdn.primeran.eus/media/a242dfb25540853d4403554f0ee858c8/cenc/audio_baq/1.m4s
```

**Response**: Binary MP4 segment (encrypted with CENC)

**Notes**:
- Videos use CENC (Common Encryption) with Widevine
- Each quality has its own content hash
- Segments are typically 4-6 seconds long

---

### 15. Track Watching Progress

**Endpoint**: `POST /api/raw/v1/watching-progress`

**Description**: Updates the user's watching progress for resume functionality.

**Example**:
```
POST https://primeran.eus/api/raw/v1/watching-progress
```

**Request Body**: JSON with:
- Media ID
- Current playback position (in seconds)
- Total duration

**Response**: 204 No Content (on success)

---

## Image API

### 16. Get Optimized Images

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

### 17. Youbora Analytics

The platform uses Youbora for video analytics:

**Endpoints**:
- `GET https://a-fds.youborafds01.com/data` - Fast data service
- `GET https://infinity-c41.youboranqs01.com/init` - Session initialization
- `GET https://infinity-c41.youboranqs01.com/start` - Playback start
- `GET https://infinity-c41.youboranqs01.com/joinTime` - Join time tracking
- `GET https://infinity-c41.youboranqs01.com/ping` - Periodic heartbeat

**Parameters Tracked**:
- Account code: `etb`
- Player: `Shaka v4.16.9`
- Content metadata (title, duration, type)
- Playback metrics (bitrate, throughput, dropped frames)
- User session info

---

### 18. ComScore Analytics

The platform uses ComScore for audience measurement:

**Endpoints**:
- `GET https://sb.scorecardresearch.com/b` - Beacon
- `GET https://sb.scorecardresearch.com/p` - Pixel tracking

**Parameters Tracked**:
- Publisher ID: `c2=14621447`
- Publisher: `EITB / PRIMERAN`
- Page views and video events

---

## Content Delivery

### CDN Structure

**Storage CDN** (`cdnstorage.primeran.eus`):
- Static assets (images, icons, player libraries)
- Uses Directus CMS structure: `/directus/eitb/{uuid}.{ext}`

**Video CDN** (`cdn.primeran.eus`):
- Video and audio segments
- Organized by content hash and quality level

---

## Video Player

### Technology Stack

- **Player**: Shaka Player v4.16.9
- **Streaming Protocol**: MPEG-DASH
- **DRM**: Widevine
- **Encryption**: CENC (Common Encryption)
- **Analytics**: Youbora v6.8.9, ComScore

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

---

## Example Playback Flow

1. User authenticates via `login.primeran.eus`
2. User selects content → Navigate to `/m/{slug}`
3. Fetch media metadata via `/api/v1/media/{slug}`
4. User clicks "Watch" → Navigate to `/w/{slug}`
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

---

## Additional Resources

- **Player Library**: Shaka Player (https://github.com/shaka-project/shaka-player)
- **DASH Specification**: MPEG-DASH ISO/IEC 23009-1
- **Widevine DRM**: Google Widevine CDM
- **Analytics**: Youbora (NPAW), ComScore

---

*Documentation generated through reverse engineering of network traffic on 2025-01-04*
