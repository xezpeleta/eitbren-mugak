# ETB On (etbon.eus) Platform

## Overview

ETB On (`etbon.eus`) is EITB's live and catch‑up TV platform for linear channels and on‑demand programs (news, entertainment, sports, documentaries, etc.). It exposes a JSON API for application configuration, EPG (electronic program guide), channels, user profiles, and VOD media (series, episodes, and standalone programs).

## Status

✅ **API documented** – reverse‑engineered main endpoints  
🛠️ **Scraper implementation** – not yet implemented in `src/` (only documentation for now)

## Quick Start

### Authentication

ETB On uses **Gigya SSO** (SAP Customer Data Cloud), shared with the rest of the EITB ecosystem.

The public Gigya API key used by ETB On is:

- `4_eUfqY3nplenbM2JKHjSxLw`

The SSO segment key is the same as Primeran/Makusi:

- `4_uJplPIpbnazIi6T4FQ1YgA`

Programmatic login looks almost identical to Primeran/Makusi, just changing the API key:

```python
import requests

session = requests.Session()
response = session.post(
    "https://login.primeran.eus/accounts.login",
    data={
        "apiKey": "4_eUfqY3nplenbM2JKHjSxLw",  # ETB On public API key
        "loginID": "your_username",
        "password": "your_password",
        "format": "json",
    },
)

if response.json().get("errorCode") == 0:
    profile = session.get("https://etbon.eus/api/v1/profiles/me").json()
```

### Environment Variables

ETB On shares the same SSO as Primeran/Makusi, so we can reuse the existing credentials:

```bash
PRIMERAN_USERNAME=your_username_or_email
PRIMERAN_PASSWORD=your_password
```

Internally, any future ETB On scraper should reuse the same env vars that are already used for Primeran/Makusi.

## API Documentation

See `API.md` in this folder for the full reverse‑engineered reference:

- Authentication flow (Gigya SSO)
- Application/config endpoints
- Channels and EPG
- Series and media metadata
- User/profile endpoints
- Analytics and tracking

## Relationship to Other Platforms

- **Shared SSO**: Same Gigya SSO backend as Primeran/Makusi (`login.primeran.eus` + `login.nireitb.eitb.eus`)
- **Shared storage/CDN**: Uses the same Directus storage and `imgproxy` image pipeline as Primeran/ Makusi (`cdnstorage.primeran.eus`, `img.primeran.eus`)
- **Different focus**: ETB On is oriented around **linear TV + catch‑up** (EPG, channels, live events), while Primeran/Makusi are pure on‑demand streaming services.

---

*For project‑wide information, see the main `README.md` in the repo root.*

# Etbon Platform

## Overview

Etbon is an EITB streaming platform. This platform is planned for future implementation.

## Status

⏳ **Planned** - Not yet implemented

## Documentation

API documentation and implementation guide coming soon.

---

*For project-wide information, see the main [README.md](../../README.md)*
