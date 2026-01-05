#!/usr/bin/env python3
"""
Quick script to regenerate dashboard JSON files from existing database
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database import ContentDatabase
from src.exporter import JSONExporter

def main():
    db_path = 'platforms/primeran/primeran_content.db'
    output_dir = 'docs/data'
    
    print("Loading database...")
    db = ContentDatabase(db_path)
    
    print("Initializing exporter...")
    exporter = JSONExporter(db, output_dir)
    
    print("\nExporting all content...")
    exporter.export_all()
    
    print("Exporting statistics...")
    exporter.export_statistics_only()
    
    print("Exporting geo-restricted content...")
    exporter.export_geo_restricted_only()
    
    print("\n✓ Dashboard data regenerated!")

if __name__ == "__main__":
    main()
