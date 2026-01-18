#!/usr/bin/env python3
"""
Main entry point for EITB platform content scraper

Usage:
    # Full scrape (all platforms by default)
    python run_scraper.py [--platform {all,primeran,makusi,etbon}] [--test] [--media-slug SLUG] [--series-slug SLUG]
    
    # Update geo-restricted content (use with VPN)
    python run_scraper.py --geo-restricted-only --disable-geo-check
    
    # Update content without metadata (use with VPN)
    python run_scraper.py --update-missing-metadata --disable-geo-check
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
    parser.add_argument('--platform', choices=['all', 'primeran', 'makusi', 'etbon'], default='all',
                        help='Platform to scrape (default: all)')
    parser.add_argument('--test', action='store_true', help='Run with test data (few items)')
    parser.add_argument('--media-slug', help='Check specific media slug')
    parser.add_argument('--series-slug', help='Check specific series slug')
    parser.add_argument('--db', help='Database file path (auto-detected if not specified)')
    parser.add_argument('--output-dir', default='docs/data', help='Output directory for JSON')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--limit', type=int, help='Limit number of items to check (for testing)')
    parser.add_argument('--disable-geo-check', action='store_true', 
                        help='Skip geo-restriction checks (useful when using VPN to update metadata)')
    parser.add_argument('--channels', action='store_true',
                        help='Also scrape live channels (ETB On only)')
    parser.add_argument('--geo-restricted-only', action='store_true',
                        help='Only update geo-restricted content (use with --disable-geo-check)')
    parser.add_argument('--new-only', '-n', action='store_true',
                        help='Only scrape content not present in the database')
    parser.add_argument('--no-export', action='store_true',
                        help='Skip JSON export after scraping')
    parser.add_argument('--update-missing-metadata', action='store_true',
                        help='Only update content without metadata (use with --disable-geo-check and VPN)')
    
    args = parser.parse_args()
    
    # Validate mutually exclusive options
    if args.geo_restricted_only and args.update_missing_metadata:
        parser.error("--geo-restricted-only and --update-missing-metadata cannot be used together. Choose one.")
    
    # Determine which platforms to scrape
    if args.platform == 'all':
        platforms = ['primeran', 'makusi', 'etbon']
    else:
        platforms = [args.platform]
    
    try:
        # Process each platform
        for platform in platforms:
            if len(platforms) > 1:
                print("\n" + "=" * 80)
                print(f"PROCESSING PLATFORM: {platform.upper()}")
                print("=" * 80)
            
            # Initialize API client based on platform
            print(f"Initializing {platform} API client...")
            if platform == 'makusi':
                from src.makusi_api import MakusiAPI
                api = MakusiAPI()
                db_path = args.db or 'platforms/makusi/makusi_content.db'
            elif platform == 'etbon':
                from src.etbon_api import EtbonAPI
                api = EtbonAPI()
                db_path = args.db or 'platforms/etbon/etbon_content.db'
            else:
                from src.primeran_api import PrimeranAPI
                api = PrimeranAPI()
                db_path = args.db or 'platforms/primeran/primeran_content.db'
            
            api.login()
            print("✓ Authenticated")
            
            print(f"Initializing database: {db_path}")
            db = ContentDatabase(db_path)
            print("✓ Database ready")
            
            scraper = ContentScraper(api, db, delay=args.delay, disable_geo_check=args.disable_geo_check, new_only=args.new_only)
            exporter = JSONExporter(db, args.output_dir)
            
            if args.disable_geo_check:
                print("⚠️  Geo-restriction checking is DISABLED")
                if args.geo_restricted_only:
                    print("   Mode: Update ONLY geo-restricted content")
                elif args.update_missing_metadata:
                    print("   Mode: Update ONLY content without metadata")
                else:
                    print("   Mode: Update ALL content")
                print("   This mode will update metadata but preserve existing geo-restriction status")
                print("   Use this when running via VPN to update metadata for geo-restricted content\n")
            
            # Run scraper
            if args.test:
                # Test with known content
                print("\n[TEST MODE] Running with test data...")
                if platform == 'makusi':
                    test_media = ['zuk-zeuk-egin-1-domino-harriekin', 'ikusi-makusiren-aurkezpena', 'twin-melody-gabon-kantak']
                    test_series = ['goazen-d12', 'kody-kapow']
                elif platform == 'etbon':
                    # ETB On test data
                    test_media = ['7073_5182885942461937664', '7073_5182885942461937666']
                    test_series = ['7073_5182885942461937660']
                else:
                    # Primeran test data
                    test_media = ['la-infiltrada', 'itoiz-udako-sesioak', 'gatibu-azken-kontzertua-zuzenean']
                    test_series = ['lau-hankan', 'krimenak-gure-kronika-beltza']
                scraper.scrape_all(media_slugs=test_media, series_slugs=test_series, check_channels=args.channels)
            elif args.media_slug:
                print(f"\nChecking media: {args.media_slug}")
                scraper.check_media(args.media_slug)
            elif args.series_slug:
                print(f"\nChecking series: {args.series_slug}")
                scraper.check_series(args.series_slug)
            else:
                # Full scrape or geo-restricted only or missing metadata only
                if args.geo_restricted_only:
                    print("\n[GEO-RESTRICTED ONLY MODE] Updating geo-restricted content...")
                    # Get geo-restricted content from database
                    geo_restricted = db.get_all_content(geo_restricted_only=True, platform=api.platform)
                    media_slugs = [item['slug'] for item in geo_restricted if item['type'] not in ['series', 'live']]
                    series_slugs = [item['slug'] for item in geo_restricted if item['type'] == 'series']
                    print(f"Found {len(media_slugs)} geo-restricted media and {len(series_slugs)} geo-restricted series")
                    scraper.scrape_all(media_slugs=media_slugs, series_slugs=series_slugs, check_channels=args.channels)
                elif args.update_missing_metadata:
                    print("\n[MISSING METADATA MODE] Updating content without metadata...")
                    # Get content without metadata from database
                    missing_metadata = db.get_content_without_metadata(platform=api.platform)
                    media_slugs = [item['slug'] for item in missing_metadata if item['type'] not in ['series', 'live']]
                    series_slugs = [item['slug'] for item in missing_metadata if item['type'] == 'series']
                    print(f"Found {len(media_slugs)} media and {len(series_slugs)} series without metadata")
                    scraper.scrape_all(media_slugs=media_slugs, series_slugs=series_slugs, check_channels=args.channels)
                else:
                    print("\n[FULL MODE] Starting full content scrape...")
                    print("This will discover and check all content (may take a while)...")
                    scraper.scrape_all(limit=args.limit, check_channels=args.channels)
            
            # Export to JSON
            if not args.no_export:
                print("\n" + "=" * 80)
                print("Exporting to JSON...")
                print("=" * 80)
                exporter.export_all()
                exporter.export_statistics_only()
                exporter.export_geo_restricted_only()
            else:
                print("\n" + "=" * 80)
                print("Skipping JSON export (--no-export used)")
                print("=" * 80)
        
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
