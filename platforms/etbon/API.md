# ETB On (etbon.eus) API Documentation

> Reverse‑engineered from live `etbon.eus` traffic (Jan 2026).  
> This describes only what has been directly observed or is clearly analogous to Primeran/Makusi.

---

## ⚠️ Important Note on API Keys

The Gigya API key used by ETB On is a **public key** embedded in the web frontend:

- **Gigya Web API key (ETB On)**: `4_eUfqY3nplenbM2JKHjSxLw`
- **Gigya SSO segment key (shared)**: `4_uJplPIpbnazIi6T4FQ1YgA`

These keys alone do **not** grant access to any personal data; valid user credentials and session cookies are still required.

---

## Base URLs

- **Web app**: `https://etbon.eus/`
- **Main API**: `https://etbon.eus/api/v1/`
- **Web app assets**:
  - Vite bundles: `https://etbon.eus/vite/…`
  - Static web assets: `https://etbon.eus/public/…`
  - Legacy splash/HbbTV scripts: `https://etbon.eus/public/{build}/js/*.js`
- **Gigya SSO**:
  - Primary: `https://login.primeran.eus/`
  - NireEITB SSO: `https://login.nireitb.eitb.eus/`
- **Image / storage CDNs** (shared with Primeran/Makusi):
  - Directus storage: `https://cdnstorage.primeran.eus/directus/eitb/{uuid}.{ext}`
  - Image proxy: `https://img.primeran.eus/imgproxy/{size}/plain/{cdn_url}@{format}`

Analytics & consent infrastructure:

- **ComScore**: `https://sb.scorecardresearch.com/…`
- **Adobe Launch**: `https://assets.adobedtm.com/.../launch-*.min.js`
- **Consent (GDPR)**: `https://cdn.privacy-mgmt.com/…`

---

## Authentication

### Overview

ETB On uses **Gigya (SAP Customer Data Cloud)** SSO, shared with other EITB platforms:

- `gigya.js` loaded from `https://cdns.eu1.gigya.com/js/gigya.js?apikey=4_eUfqY3nplenbM2JKHjSxLw`
- Additional SSO API from `https://login.nireitb.eitb.eus/js/Api.htm`
- SSO segment from `https://login.nireitb.eitb.eus/js/sso.htm?APIKey=4_uJplPIpbnazIi6T4FQ1YgA&sourceKey=4_eUfqY3nplenbM2JKHjSxLw`

### Authentication Flow (High‑Level)

The flow is effectively the same as Primeran/Makusi:

1. **User logs in** via Gigya using `accounts.login` on `login.primeran.eus`, with ETB On API key `4_eUfqY3nplenbM2JKHjSxLw`.
2. Gigya returns `sessionToken`, `sessionSecret`, `UID`, and sets SSO cookies on the `*.eitb.eus` domains.
3. The ETB On frontend then calls ETB On API endpoints (e.g. `/api/v1/profiles/me`, `/api/v1/my-list`) with those cookies.
4. ETB On validates the session through Gigya and returns user‑specific data.

You can treat the login process as a straightforward variant of the Primeran one, just swapping the `apiKey`.

#### Direct Login (Pattern)

```bash
curl -X POST 'https://login.primeran.eus/accounts.login' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'apiKey=4_eUfqY3nplenbM2JKHjSxLw' \
  -d 'loginID=your-username-or-email' \
  -d 'password=your-password' \
  -d 'format=json'
```

Response structure matches Gigya’s standard schema (see `platforms/primeran/API.md` for detailed examples).

#### Python Example

```python
import requests

GIGYA_API_KEY = "4_eUfqY3nplenbM2JKHjSxLw"
LOGIN_ENDPOINT = "https://login.primeran.eus/accounts.login"
ACCOUNT_INFO_ENDPOINT = "https://login.primeran.eus/accounts.getAccountInfo"

session = requests.Session()

login_resp = session.post(
    LOGIN_ENDPOINT,
    data={
        "apiKey": GIGYA_API_KEY,
        "loginID": "your-username-or-email",
        "password": "your-password",
        "format": "json",
    },
)
data = login_resp.json()

if data.get("errorCode") == 0:
    info_resp = session.post(
        ACCOUNT_INFO_ENDPOINT,
        data={
            "apiKey": GIGYA_API_KEY,
            "sessionToken": data["sessionInfo"]["sessionToken"],
            "sessionSecret": data["sessionInfo"]["sessionSecret"],
            "format": "json",
        },
    )
    # This same session can then be used with https://etbon.eus/api/v1/...
    me = session.get("https://etbon.eus/api/v1/profiles/me").json()
```

### Important Auth‑Related Endpoints (Observed)

On ETB On itself:

- `GET /api/v1/profiles/me` – Get the current logged‑in ETB On profile.
- `GET /api/v1/watching-progress` – Get per‑profile watching progress.
- `GET /api/v1/my-list` – User’s favorites / watchlist.
- `GET /api/v1/notifications` – In‑app notification list.

On Gigya / SSO:

- `https://cdns.eu1.gigya.com/js/gigya.js?apikey=4_eUfqY3nplenbM2JKHjSxLw`
- `https://login.nireitb.eitb.eus/js/Api.htm?apiKey=4_eUfqY3nplenbM2JKHjSxLw`
- `https://login.nireitb.eitb.eus/js/sso.htm?APIKey=4_uJplPIpbnazIi6T4FQ1YgA&sourceKey=4_eUfqY3nplenbM2JKHjSxLw`

---

## Application & UI Configuration API

These are called on every page load, similar to Primeran/Makusi.

### 1. Get Application Settings

**Endpoint**: `GET /api/v1/application`

**Purpose**: Global application metadata and configuration for ETB On.

Includes (inferred from usage and analogy with Primeran/Makusi):

- Application ID and name (likely `name: "etbon"`)
- Web URL
- Theme (colors, logos, icons)
- Channel and EPG configuration
- SSO configuration (Gigya keys, SSO segment)
- Analytics configuration (ComScore, Adobe Launch, etc.)

**Example**:

```bash
GET https://etbon.eus/api/v1/application
```

### 2. Get UI Settings

**Endpoint**: `GET /api/v1/settings`

**Purpose**: Static configuration needed by the frontend UI.

Expected structure (based on Primeran/Makusi):

- Available UI languages (Basque/Spanish)
- Age ratings and labels (`D`, `GAZT`, etc. in the UI)
- Media language codes
- Image format definitions
- Miscellaneous feature flags

### 3. Get Localized UI Texts

**Endpoint**: `GET /api/v1/settings/texts`

**Purpose**: Full dictionary of localized strings in the current UI language.

Returns a large JSON object mapping keys (e.g. `app_title`, `login_button`) to localized strings. The current language is controlled by `language-selector` / cookies.

### 4. Get Available Avatars

**Endpoint**: `GET /api/v1/avatars`

**Purpose**: Avatars for user profiles.

Each entry includes at least:

- `id` – numeric ID
- `image` – full URL in `cdnstorage.primeran.eus/directus/eitb/...`

### 5. Get Language Selector Configuration

**Endpoint**: `GET /api/v1/language-selector`

**Purpose**: Available languages for the UI and content (Basque/Spanish) and rules for switching between them.

---

## User & Profile API

ETB On exposes a familiar set of profile endpoints:

### 6. Get Current Profile

**Endpoint**: `GET /api/v1/profiles/me`

**Purpose**: Returns the currently active profile for the logged‑in account (name, avatar, default language, etc.).

### 7. Get Watching Progress

**Endpoint**: `GET /api/v1/watching-progress`

**Purpose**: Retrieve progress entries so the UI can show “continue watching” rows.

Typical fields (by analogy with Makusi):

- `media_id`
- `slug`
- `progress` (in seconds)
- `duration`
- `last_watched` timestamp

### 8. Get My List (Favorites)

**Endpoint**: `GET /api/v1/my-list`

**Purpose**: Returns the user’s favorites/watchlist, used to drive “My List” rows and the “Add to favorites” button on series/media pages.

### 9. Notifications

**Endpoint**: `GET /api/v1/notifications`

**Purpose**: User‑facing notifications, likely for new episodes, expiring content, or platform messages.

---

## Channels & EPG (ETB‑specific)

Unlike Primeran/Makusi, ETB On is focused on linear channels and an EPG (7‑day grid).

### 10. Get Stations (Channels)

**Endpoint**: `GET /api/v1/stations`

**Purpose**: Returns the list of TV (and possibly radio) stations managed by ETB On.

Each station represents something like `ETB1`, `ETB2`, `ETB3`, `ETB4`, `eitb.eus`, etc. The frontend uses this together with `epg` data to render channel rows in `/epg` and the “Kanalak eta zuzenekoak” page.

### 11. Get EPG (Electronic Program Guide)

**Endpoint**: `POST /api/v1/epg`

**Purpose**: Fetch the multi‑channel schedule over a period of time (used by `/epg` and live/7‑day catch‑up).

**Observed**: `POST` requests from the EPG page (`/epg`) with a JSON body (not fully captured here). By analogy with other EPG APIs, likely parameters include:

- Date range (from/to)
- Station IDs (subset of channels)
- Timezone and/or locale

**Response** (inferred):

- Per‑station schedule with:
  - Start/end datetime
  - Program title
  - Episode/season info, if applicable
  - Slugs or IDs to navigate into catch‑up media (`/m/{slug}` or `/s/{slug}`)

This endpoint is critical for any scraper that wants to tie scheduled broadcasts to VOD media.

---

## Content API (Series & Media)

ETB On surfaces series and individual media through these routes:

- Series pages: `/s/{slug}` (e.g. `/s/vaya-semanita`)
- Media pages: `/m/{slug}` (e.g. `/m/la-familia-bloom-1-17403293`)

The frontend uses the following API endpoints:

### 12. Get Series Details

**Endpoint**: `GET /api/v1/series/{slug}`

**Example (observed)**:

```bash
GET https://etbon.eus/api/v1/series/vaya-semanita
```

This is called when opening the series page `/s/vaya-semanita`.

**Response** (pattern, based on actual usage + Makusi/Primeran):

- `id` – numeric series ID (used in `/series/{id}/clip`)
- `slug` – URL slug (`"vaya-semanita"`)
- `title` – `"Vaya Semanita"`
- `description` – Basque/Spanish description
- `type` – something like `"series"`
- `seasons` – array of season objects:
  - `id`
  - `season_number`
  - `episodes` – array with:
    - `id`
    - `slug` (e.g. `vaya-semanita-1-17662594`)
    - `title`
    - `duration`
    - `published_on`
- Possibly `first_episode`, `images`, `tags`, etc.

The UI shows seasons (e.g. `"15. DENBORALDIA"`) and lists episodes linking to `/m/{episode_slug}`. The API supports this by returning at least one season with episode information.

### 13. Get Series Clips

**Endpoint**: `GET /api/v1/series/{series_id}/clip`

**Example (observed)**:

```bash
GET https://etbon.eus/api/v1/series/2171/clip
```

This matches the Makusi pattern (`/api/v1/series/{series_id}/clip`), returning promotional clips or previews for the series.

### 14. Get Media Details

**Endpoint**: `GET /api/v1/media/{slug}`

**Example (observed)**:

```bash
GET https://etbon.eus/api/v1/media/la-familia-bloom-1-17403293  # HTTP 403 from our IP
```

This is called when opening a media page like `/m/la-familia-bloom-1-17403293` (a La Noche De... film).

We received a **403** from outside the intended region, but the existence and shape of the endpoint can be inferred from Primeran/Makusi:

- `id`
- `slug`
- `title`
- `description`
- `duration`
- `production_year`
- `collection` (`"media"` or `"series"`)
- `access_restriction` (public/registration required)
- `age_rating`
- `images` (Directus URLs, often accessed via `img.primeran.eus/imgproxy`)
- `audios` / `subtitles`
- Possibly `manifests` if ETB On exposes DRM‑protected VOD (not directly observed in the captured traffic)

**Important**: we have not yet captured the **streaming manifest** endpoints (`/manifests/...`) or DRM license server for ETB On; live channels may use HLS played via different URLs exposed through `/stations` or internal configuration.

---

## Home / Navigation Content

While not exhaustively captured, ETB On shows multiple rows on its home page (Top in Basque/Spanish, recommendations, etc.). These are likely backed by additional endpoints similar to Primeran's `/home` and `/menus/{id}`.

### 15. Get Home Content

**Endpoint**: `GET /api/v1/home`

**Purpose**: Returns the home page structure with sections, carousels, and content rows.

**Response** (based on observed structure):

The home page includes a `children` array with multiple sections such as:
- Slider (featured content)
- Channels (`Canales`)
- Weekly highlights (`Zuzenekoak: Asteko nabarmenenak`)
- Information section (`Informazioa`)
- Programs section (`Programak`)
- Current affairs (`Aktualitatea`)
- Sports (`ETB Kirolak`)
- Top 5 lists (Basque/Spanish)

**Note on "Newest" Content**:

Unlike Primeran and Makusi, ETB On does **not** have a clearly labeled "newest" or "latest" section in the `/home` endpoint. For incremental scraping of recent content, consider these alternatives:

1. **Use "Aktualitatea" (Current Affairs)** section - likely contains recent news and current content
2. **Use "Zuzenekoak: Asteko nabarmenenak"** - weekly highlights from live broadcasts
3. **Use "Programak" (Programs)** section - may include recently added programs
4. **Monitor EPG data** via `/api/v1/epg` to track new broadcasts that become available as catch-up content

For daily scraping of ETB On, a full scrape or monitoring the EPG for new broadcasts may be more effective than relying on a "newest" section.

If future work identifies a dedicated newest content section or endpoint, document it here.

---

## Image API

As with Primeran/Makusi, ETB On uses the shared `imgproxy` service:

**Endpoint pattern**:

```text
GET https://img.primeran.eus/imgproxy/{size}/plain/{cdn_url}@{format}
```

Where:

- `size` – size preset (`xs`, `sm`, `xl`, …)
- `cdn_url` – a full Directus image URL, e.g.  
  `https://cdnstorage.primeran.eus/directus/eitb/3845e686-4e1e-43e8-a917-39dac38837b5.jpg`
- `format` – output format (`webp`, `png`, …)

**Example (observed)**:

```text
https://img.primeran.eus/imgproxy/xl/plain/https://cdnstorage.primeran.eus/directus/eitb/3845e686-4e1e-43e8-a917-39dac38837b5.jpg@webp
```

---

## Analytics & Tracking

### ComScore

ETB On uses ComScore, with the same publisher ID as Primeran/Makusi:

- Beacons: `https://sb.scorecardresearch.com/b` / `b2`
- Pixel: `https://sb.scorecardresearch.com/p`
- Publisher ID: `c2=14621447`
- App name: `c4=ETBON`, `c6=ETBON` in some requests

### Adobe Launch

- `https://assets.adobedtm.com/c2eed86bea5f/540d51c142d8/launch-693a375ffe5c.min.js`

Used for general web analytics / tag management.

### Consent Management (GDPR)

ETB On integrates a CMP from `cdn.privacy-mgmt.com`:

- `wrapperMessagingWithoutDetection.js`
- `/mms/v2/get_site_data`
- `/wrapper/v2/messages`
- `/wrapper/v2/choice/...`

This is responsible for the cookie banner and consent storage and is shared across EITB domains.

---

## Technology Stack (Frontend)

From the observed assets:

- **Bundler/runtime**: Vite (`/vite/*.js`, `/vite/*.css`)
- **UI framework**: Not explicitly named in traffic, but Vite + component bundles indicate a modern JS framework (likely React or Vue).
- **Fonts**:
  - `Raleway`, `Poppins`, `Roboto` via Google Fonts
  - `Neue Haas Grotesk Display Pro` via `fonts.cdnfonts.com`
- **Accessibility**: A custom `AccessibilityManager` is initialized on load (`[AM] initializing AccessibilityManager…` in console logs).

---

## Summary of Observed Endpoints

**Configuration & UI**

- `GET /api/v1/application`
- `GET /api/v1/settings`
- `GET /api/v1/settings/texts`
- `GET /api/v1/language-selector`
- `GET /api/v1/avatars`

**User / Profile**

- `GET /api/v1/profiles/me`
- `GET /api/v1/watching-progress`
- `GET /api/v1/my-list`
- `GET /api/v1/notifications`

**Channels & EPG**

- `GET /api/v1/stations`
- `POST /api/v1/epg`

**Content (Series & Media)**

- `GET /api/v1/series/{slug}` – e.g. `/api/v1/series/vaya-semanita`
- `GET /api/v1/series/{id}/clip` – e.g. `/api/v1/series/2171/clip`
- `GET /api/v1/media/{slug}` – e.g. `/api/v1/media/la-familia-bloom-1-17403293` (403 from our IP)

**Other**

- Shared image/CDN infrastructure with Primeran/Makusi.
- Shared SSO and analytics infrastructure across EITB platforms.

---

## Notes & Open Questions

1. **Streaming manifests**: The exact endpoints for live/VOD manifests and DRM licenses were not visible in the sampled traffic; they may be resolved inside player code or set up via `/api/v1/stations` and internal configuration.
2. **Raw API**: We did not directly observe any `/api/raw/v1/...` calls, but ETB On may still use a raw API for POST updates (e.g. watching progress) similar to Primeran.
3. **Scraper integration**: When implementing an ETB On scraper, we should:
   - Reuse the Gigya login logic from Primeran/Makusi with the ETB On API key.
   - Use `/api/v1/series` + `/api/v1/media` as primary discovery endpoints.
   - Use `/api/v1/stations` + `/api/v1/epg` to correlate linear broadcasts with VOD slugs.

---

*Documentation generated through reverse engineering of network traffic on 2026‑01‑06.*

