# Makusi.eus Platform

## Overview

Makusi.eus is a Basque children's streaming platform operated by EITB. This platform provides access to children's content including animated series, movies, music, and educational content.

## Status

✅ **API Documented** - API documentation complete, implementation pending

## Quick Start

### Authentication

Makusi uses **Gigya SSO** (SAP Customer Data Cloud) for authentication, **shared with Primeran.eus**. If you're already logged into Primeran.eus, you'll automatically be authenticated on Makusi.eus.

```python
import requests

session = requests.Session()
response = session.post('https://login.primeran.eus/accounts.login', data={
    'apiKey': '4_OrNV-xF_hgF-IKSFkQrJxg',  # Makusi-specific API key
    'loginID': 'your_username',
    'password': 'your_password',
    'format': 'json'
})

if response.json().get('errorCode') == 0:
    # Authenticated - can now access API
    profile = session.get('https://makusi.eus/api/v1/profiles/me').json()
```

### Environment Variables

Makusi uses the **same credentials as Primeran** (shared SSO). Add to your `.env` file:

```bash
PRIMERAN_USERNAME=your_username_or_email
PRIMERAN_PASSWORD=your_password
```

**Note**: Since Makusi shares authentication with Primeran, you can use the same `PRIMERAN_USERNAME` and `PRIMERAN_PASSWORD` environment variables.

## API Documentation

See [API.md](API.md) for complete API reference including:
- Authentication flow (shared SSO with Primeran)
- Content discovery endpoints
- Video streaming (MPEG-DASH, Widevine DRM)
- User management
- Analytics integration

## Key Differences from Primeran

- **Target Audience**: Children's content (vs. general audience for Primeran)
- **API Key**: `4_OrNV-xF_hgF-IKSFkQrJxg` (vs. `4_iXtBSPAhyZYN6kg3DlaQuQ` for Primeran)
- **Base URL**: `https://makusi.eus/` (vs. `https://primeran.eus/`)
- **Shared Infrastructure**: Uses same CDN, authentication, and some API endpoints as Primeran

## Shared Infrastructure

Makusi.eus shares the following infrastructure with Primeran.eus:
- **Authentication System**: Same Gigya SSO (login.primeran.eus)
- **CDN**: Same storage and video CDN (cdnstorage.primeran.eus, cdn.primeran.eus)
- **Image Processing**: Same imgproxy service (img.primeran.eus)
- **Analytics**: Same Youbora and ComScore configuration

---

*For project-wide information, see the main [README.md](../../README.md)*
