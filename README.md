# EITBren mugak

EITBren streaming plataforma ezberdinetan dagoen eduki asko ez dago eskuragarri Ipar Euskal Herrian. Proiektu honen xedea, hain zuzen ere, eduki hau identifikatzea da eta APIa dokumentatzea.

Many content items on EITB streaming platforms are not available in Northern Basque Country. This project aims to identify this content and document the APIs.

---

## 📚 Platforms / Plataformak

- [x] **[Primeran](platforms/primeran/)** ✅ (Complete - API documented + Geo-restriction checker)
- [ ] **[Makusi](platforms/makusi/)** (Planned)
- [ ] **[Guau](platforms/guau/)** (Planned)
- [ ] **[Etbon](platforms/etbon/)** (Planned)

---

## 🎯 Project Overview

This project consists of two main components:

1. **API Documentation** - Complete reverse-engineered API documentation for each platform
2. **Geo-Restriction Checker** - Automated tool to identify geo-restricted content with a web dashboard

### Current Statistics (Primeran - 2026-01-04)

- **Total content discovered**: 6,294 items
- **Geo-restricted items**: 1,503 items (23.9% restriction rate)
- **Accessible items**: 4,791 items
- **Detection accuracy**: 100% (verified against browser behavior)

---

## 🚀 Quick Start

### Using the Geo-Restriction Checker

1. **Set up environment**:
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env and add your credentials for the platform(s) you want to use
   PRIMERAN_USERNAME=your_username_or_email
   PRIMERAN_PASSWORD=your_password
   ```

2. **Install dependencies** (using `uv` - recommended):
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Run the scraper**:
   ```bash
   # Full scrape for Primeran (discovers all content)
   uv run python run_scraper.py --platform primeran
   
   # Test with limited items
   uv run python run_scraper.py --platform primeran --limit 10
   
   # Check specific content
   uv run python run_scraper.py --platform primeran --media-slug la-infiltrada
   uv run python run_scraper.py --platform primeran --series-slug lau-hankan
   ```

4. **View the dashboard**:
   ```bash
   cd dashboard
   python3 -m http.server 8000
   # Open http://localhost:8000 in your browser
   ```

---

## 📖 Documentation

### Core Documentation

- **[METHODOLOGY.md](METHODOLOGY.md)** - Geo-restriction detection methodology (applies to all platforms)
- **[AGENTS.md](AGENTS.md)** - Development preferences and guidelines

### Platform-Specific Documentation

Each platform has its own documentation in the `platforms/` directory:

- **[Primeran](platforms/primeran/)** - Complete API documentation and platform guide
  - [API Reference](platforms/primeran/API.md) - Complete API documentation
  - [Platform Guide](platforms/primeran/README.md) - Quick start and platform details

- **Makusi** - Coming soon
- **Guau** - Coming soon
- **Etbon** - Coming soon

---

## 🔑 Key Features

### API Documentation
✅ **Complete Authentication Flows** - Documented for each platform  
✅ **Content Discovery** - Browse, search, and discover content  
✅ **Video Streaming** - Streaming protocols and DRM documentation  
✅ **User Management** - Profiles, watch progress, saved lists  
✅ **Analytics Integration** - Tracking systems documentation  

### Geo-Restriction Checker
✅ **Automated Content Discovery** - Discovers all media and series  
✅ **Geo-Restriction Detection** - Identifies restricted content via manifest checks  
✅ **SQLite Database** - Stores all content metadata and restriction status  
✅ **Web Dashboard** - Interactive dashboard with statistics and visualizations  
✅ **Filterable Content List** - Search, filter, and sort all discovered content  
✅ **Multi-Platform Support** - Architecture ready for multiple platforms  

---

## 🛠 Technology Stack

- **Scraper**: Python with `requests` and SQLite
- **Dashboard**: HTML/CSS/JavaScript with Chart.js
- **Package Management**: `uv` (from Astral)
- **Platform-Specific**: See each platform's documentation for details

---

## 📦 Project Structure

```
eitbhub/
├── src/                    # Scraper source code
│   ├── primeran_api.py    # Primeran API client
│   ├── database.py        # SQLite database operations
│   ├── scraper.py         # Content discovery & checking
│   └── exporter.py        # JSON export for dashboard
├── platforms/              # Platform-specific documentation
│   ├── primeran/
│   │   ├── API.md        # Complete API documentation
│   │   └── README.md     # Platform guide
│   ├── makusi/           # Coming soon
│   ├── guau/             # Coming soon
│   └── etbon/            # Coming soon
├── dashboard/             # Web dashboard
│   ├── index.html         # Dashboard
│   ├── content.html       # Content list
│   ├── css/               # Styles
│   ├── js/                # JavaScript
│   └── data/              # JSON exports
├── run_scraper.py         # Main scraper entry point
├── METHODOLOGY.md         # Detection methodology
├── AGENTS.md             # Development preferences
├── .env.example          # Environment template
└── requirements.txt      # Python dependencies
```

---

## 🔒 Security & Legal

**Important Notes:**
- ⚠️ This documentation is for **educational purposes** only
- 🔐 Keep your credentials secure - never commit them to code
- 📝 Respect each platform's terms of service
- 🚫 Do not share or redistribute copyrighted content
- ✅ All video content is DRM-protected
- 🔑 API keys referenced in documentation are public (used in frontend JavaScript)

---

## 🤝 Contributing

Found an error or want to add more documentation? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📞 Support

For issues with the platforms themselves:
- **Primeran**: https://primeran.eus/
- **Makusi**: Coming soon
- **Guau**: Coming soon
- **Etbon**: Coming soon

---

## 📝 License

This documentation is provided "as-is" for educational purposes.

---

## 🌟 Acknowledgments

- **EITB** - Euskal Irrati Telebista
- **Primeran.eus** - For Basque streaming content
- Documentation generated through network analysis

---

*Euskaraz sortutako edukia, euskal kulturarako streaming plataforma*

*Basque content, streaming platform for Basque culture*
