# Primeran Geo-Restriction Checker - Static Website

This directory contains the static website that displays geo-restriction data from Primeran.eus.

## Structure

```
dashboard/
├── index.html          # Main dashboard with statistics
├── content.html        # Filterable content list
├── css/
│   └── style.css      # Styling
├── js/
│   ├── dashboard.js   # Dashboard logic and charts
│   └── content.js     # Content list filtering/sorting
└── data/
    ├── content.json           # Full content list (generated)
    ├── statistics.json        # Summary statistics (generated)
    └── geo-restricted.json    # Geo-restricted items only (generated)
```

## Testing Locally

Due to browser CORS restrictions, you cannot open the HTML files directly with `file://`. You need to serve them via HTTP.

### Option 1: Python HTTP Server

```bash
cd dashboard
python3 -m http.server 8000
# Then open http://localhost:8000 in your browser
```

### Option 2: Using uv (as per project preferences)

```bash
cd dashboard
uv run python -m http.server 8000
# Then open http://localhost:8000 in your browser
```

### Option 3: Node.js HTTP Server

```bash
cd dashboard
npx http-server -p 8000
# Then open http://localhost:8000 in your browser
```

## Updating Data

To update the data files, run the scraper:

```bash
# From project root
python run_scraper.py --test  # Test mode (20 items)
python run_scraper.py        # Full scrape (all content)
```

The scraper will automatically update the JSON files in `dashboard/data/`.

## Deployment

This website is designed to be deployed on **GitHub Pages**:

1. Push the `dashboard/` folder to your repository
2. Enable GitHub Pages in repository settings
3. Set source to `/dashboard` folder
4. The website will be available at `https://username.github.io/repo-name/`

## Features

### Dashboard (index.html)
- Statistics overview cards
- Pie chart showing geo-restriction status
- Bar chart showing content by type
- Last updated timestamp

### Content List (content.html)
- Searchable table
- Filter by type and geo-restriction status
- Sortable columns
- Responsive design

## Dependencies

- **Chart.js** (loaded via CDN) - For visualizations
- No build step required - pure HTML/CSS/JS
