# EITBHub

EITBren streaming plataforma ezberdinak bateratzend dituen webgunea da EITBHub.

## Ezaugarriak

- Zerrenda bateratua
- Bilatzaile aurreratua eta filtroak
- Geo-murrizketa informazioa (Espainiar estatutik kanpo edukia eskuragarri dagoen zehazten da).
- Estekak jatorrizko plataformetara, edukia ikusi ahal izateko

---

## Plataformak

- [x] **[Primeran](platforms/primeran/)**
- [x] **[Makusi](platforms/makusi/)**
- [x] **[Etbon](platforms/etbon/)**
- [ ] **[Guau](platforms/guau/)** (egiteke)


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
   
   # Update metadata for geo-restricted content (use with VPN)
   uv run python run_scraper.py --platform primeran --geo-restricted-only --disable-geo-check
   
   # Update metadata for content without metadata (use with VPN)
   uv run python run_scraper.py --platform primeran --update-missing-metadata --disable-geo-check
   ```

4. **Regenerate EITBHub JSON data** (from existing database):
   ```bash
   uv run python export_json.py
   ```

5. **Open the EITBHub web UI**:
   ```bash
   cd docs
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

- **[Makusi](platforms/makusi/)** - Complete API documentation and platform guide
  - [API Reference](platforms/makusi/API.md) - Complete API documentation
  - [Platform Guide](platforms/makusi/README.md) - Quick start and platform details
- **[EtbON](platforms/etbon/)** - Complete API documentation and platform guide
  - [API Reference](platforms/etbon/API.md) - Complete API documentation
  - [Platform Guide](platforms/etbon/README.md) - Quick start and platform details
- **Guau** - Coming soon
