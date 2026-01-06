#!/usr/bin/env python3
"""
Main entry point for EITB platform content scraper

Usage:
    python run_scraper.py [--platform PLATFORM] [--test] [--media-slug SLUG] [--series-slug SLUG]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import ContentDatabase
from src.scraper import ContentScraper
from src.exporter import JSONExporter


def main():
    parser = argparse.ArgumentParser(description='Scrape EITB platform content and check geo-restrictions')
    parser.add_argument('--platform', choices=['primeran', 'makusi'], default='primeran',
                        help='Platform to scrape (default: primeran)')
    parser.add_argument('--test', action='store_true', help='Run with test data (few items)')
    parser.add_argument('--media-slug', help='Check specific media slug')
    parser.add_argument('--series-slug', help='Check specific series slug')
    parser.add_argument('--db', default='platforms/primeran/primeran_content.db', help='Database file path')
    parser.add_argument('--output-dir', default='docs/data', help='Output directory for JSON')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--limit', type=int, help='Limit number of items to check (for testing)')
    parser.add_argument('--disable-geo-check', action='store_true', 
                        help='Skip geo-restriction checks (useful when using VPN to update metadata)')
    
    args = parser.parse_args()
    
    try:
        # Initialize API client based on platform
        print(f"Initializing {args.platform} API client...")
        if args.platform == 'makusi':
            from src.makusi_api import MakusiAPI
            api = MakusiAPI()
        else:
            from src.primeran_api import PrimeranAPI
        api = PrimeranAPI()
        
        api.login()
        print("✓ Authenticated")
        
        print(f"Initializing database: {args.db}")
        db = ContentDatabase(args.db)
        print("✓ Database ready")
        
        scraper = ContentScraper(api, db, delay=args.delay, disable_geo_check=args.disable_geo_check)
        exporter = JSONExporter(db, args.output_dir)
        
        if args.disable_geo_check:
            print("⚠️  Geo-restriction checking is DISABLED")
            print("   This mode will update metadata but preserve existing geo-restriction status")
            print("   Use this when running via VPN to update metadata for geo-restricted content\n")
        
        # Run scraper
        if args.test:
            # Test with known content
            print("\n[TEST MODE] Running with test data...")
            if args.platform == 'makusi':
                test_media = ['zuk-zeuk-egin-1-domino-harriekin', 'ikusi-makusiren-aurkezpena', 'twin-melody-gabon-kantak']
                test_series = ['goazen-d12', 'kody-kapow']
            else:
                # Primeran test data
            test_media = ['la-infiltrada', 'itoiz-udako-sesioak', 'gatibu-azken-kontzertua-zuzenean']
            test_series = ['lau-hankan', 'krimenak-gure-kronika-beltza']
            scraper.scrape_all(media_slugs=test_media, series_slugs=test_series)
        elif args.media_slug:
            print(f"\nChecking media: {args.media_slug}")
            scraper.check_media(args.media_slug)
        elif args.series_slug:
            print(f"\nChecking series: {args.series_slug}")
            scraper.check_series(args.series_slug)
        else:
            # Full scrape
            print("\n[FULL MODE] Starting full content scrape...")
            print("This will discover and check all content (may take a while)...")
            scraper.scrape_all(limit=args.limit)
        
        # Export to JSON
        print("\n" + "=" * 80)
        print("Exporting to JSON...")
        print("=" * 80)
        exporter.export_all()
        exporter.export_statistics_only()
        exporter.export_geo_restricted_only()
        
        print("\n✓ Scraping complete!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
