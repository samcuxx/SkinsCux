#!/usr/bin/env python3
"""
Save current scraped data to files
"""

import requests
import json
import os

def save_current_data():
    """Try to save current data from the Flask app"""
    
    print("🔄 Attempting to save current scraped data...")
    
    try:
        # Get current status
        status_response = requests.get("http://localhost:5000/api/scraping_status")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"📊 Current status: {status['scraped_count']} skins scraped")
        
        # Try to trigger data export
        print("📥 Exporting CSV...")
        csv_response = requests.get("http://localhost:5000/api/export/csv")
        if csv_response.status_code == 200:
            os.makedirs('data', exist_ok=True)
            with open('data/rainmeter_skins.csv', 'wb') as f:
                f.write(csv_response.content)
            print("✅ CSV saved to data/rainmeter_skins.csv")
        else:
            print(f"❌ CSV export failed: {csv_response.status_code}")
        
        print("📥 Exporting JSON...")
        json_response = requests.get("http://localhost:5000/api/export/json")
        if json_response.status_code == 200:
            with open('data/rainmeter_skins.json', 'wb') as f:
                f.write(json_response.content)
            print("✅ JSON saved to data/rainmeter_skins.json")
        else:
            print(f"❌ JSON export failed: {json_response.status_code}")
            
        # Get data quality info
        data_response = requests.get("http://localhost:5000/api/get_data")
        if data_response.status_code == 200:
            data = data_response.json()
            stats = data.get('stats', {})
            print(f"\n📊 Data Quality Summary:")
            print(f"   📦 Total Skins: {data.get('total_count', 0)}")
            print(f"   📥 With Downloads: {stats.get('with_downloads', 0)}")
            print(f"   👨‍💻 Unique Developers: {stats.get('unique_developers', 0)}")
            print(f"   🖼️ With Thumbnails: {stats.get('with_thumbnails', 0)}")
            
            # Show sample
            skins = data.get('data', [])
            if skins:
                sample = skins[0]
                print(f"\n🎯 Sample Skin:")
                print(f"   Name: {sample.get('name', 'N/A')}")
                print(f"   Developer: {sample.get('developer', 'N/A')}")
                print(f"   Has Download: {'Yes' if sample.get('download_url') else 'No'}")
                print(f"   Has Thumbnail: {'Yes' if sample.get('thumbnail_url') else 'No'}")
        
    except requests.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the Flask app is running on localhost:5000")

if __name__ == "__main__":
    save_current_data() 