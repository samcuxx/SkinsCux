#!/usr/bin/env python3
"""
Command-line interface for the Rainmeter Skins Scraper
Usage: python run_scraper.py [options]
"""

import argparse
import sys
import os
from scraper.rainmeter_scraper import RainmeterScraper

def main():
    parser = argparse.ArgumentParser(
        description="Professional Rainmeter Skins Scraper - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py                     # Scrape all skins with default settings
  python run_scraper.py --max-pages 50     # Limit to 50 pages
  python run_scraper.py --delay 2          # 2 second delay between requests
  python run_scraper.py --output my_skins  # Custom output filename
        """
    )
    
    parser.add_argument(
        '--max-pages', 
        type=int, 
        default=None,
        help='Maximum number of pages to scrape (default: all pages)'
    )
    
    parser.add_argument(
        '--delay', 
        type=float, 
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default='rainmeter_skins',
        help='Output filename prefix (default: rainmeter_skins)'
    )
    
    parser.add_argument(
        '--format', 
        choices=['csv', 'json', 'both'], 
        default='both',
        help='Output format (default: both)'
    )
    
    parser.add_argument(
        '--base-url', 
        type=str, 
        default='https://visualskins.com',
        help='Base URL to scrape (default: https://visualskins.com)'
    )
    
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--no-cleanup', 
        action='store_true',
        help='Skip data cleaning and duplicate removal'
    )

    args = parser.parse_args()
    
    print("=" * 60)
    print("🕷️  Rainmeter Skins Scraper - Professional Edition")
    print("=" * 60)
    print(f"Target: {args.base_url}")
    print(f"Max pages: {'All' if args.max_pages is None else args.max_pages}")
    print(f"Request delay: {args.delay}s")
    print(f"Output format: {args.format}")
    print(f"Output prefix: {args.output}")
    print("=" * 60)
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    try:
        # Initialize scraper
        scraper = RainmeterScraper(base_url=args.base_url, delay=args.delay)
        
        # Start scraping
        print("🚀 Starting scraping process...")
        data = scraper.scrape_all_skins(max_pages=args.max_pages)
        
        if not data:
            print("❌ No data was scraped. Please check the website URL and try again.")
            sys.exit(1)
        
        print(f"✅ Successfully scraped {len(data)} skins")
        
        # Clean data unless disabled
        if not args.no_cleanup:
            print("🧹 Cleaning and processing data...")
            scraper.clean_data()
            scraper.remove_duplicates()
            print(f"✅ Data cleaned. {len(scraper.scraped_data)} unique skins remaining")
        
        # Save data
        print("💾 Saving data...")
        
        if args.format in ['csv', 'both']:
            csv_filename = f"data/{args.output}.csv"
            scraper.save_to_csv(csv_filename)
            print(f"✅ CSV saved: {csv_filename}")
        
        if args.format in ['json', 'both']:
            json_filename = f"data/{args.output}.json"
            scraper.save_to_json(json_filename)
            print(f"✅ JSON saved: {json_filename}")
        
        # Display statistics
        stats = scraper.get_stats()
        print("\n📊 Scraping Statistics:")
        print(f"   Total skins scraped: {stats['total_scraped']}")
        print(f"   Failed URLs: {stats['failed_urls']}")
        print(f"   Unique developers: {stats['unique_developers']}")
        print(f"   Skins with downloads: {stats['with_downloads']}")
        print(f"   Skins with thumbnails: {stats['with_thumbnails']}")
        
        if stats['failed_urls'] > 0:
            print(f"\n⚠️  {stats['failed_urls']} URLs failed to load")
            if args.verbose:
                print("Failed URLs:")
                for url in scraper.failed_urls[:10]:  # Show first 10
                    print(f"   - {url}")
                if len(scraper.failed_urls) > 10:
                    print(f"   ... and {len(scraper.failed_urls) - 10} more")
        
        print("\n🎉 Scraping completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping stopped by user")
        print("Partial data may have been saved.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 