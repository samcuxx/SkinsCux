#!/usr/bin/env python3
"""
Installation and functionality test script for Rainmeter Scraper Pro
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import requests
        print("  ✅ requests")
    except ImportError:
        print("  ❌ requests - Please install: pip install requests")
        return False
    
    try:
        import pandas
        print("  ✅ pandas")
    except ImportError:
        print("  ❌ pandas - Please install: pip install pandas")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("  ✅ beautifulsoup4")
    except ImportError:
        print("  ❌ beautifulsoup4 - Please install: pip install beautifulsoup4")
        return False
    
    try:
        import flask
        print("  ✅ flask")
    except ImportError:
        print("  ❌ flask - Please install: pip install flask")
        return False
    
    try:
        from scraper import RainmeterScraper
        print("  ✅ scraper package")
    except ImportError as e:
        print(f"  ❌ scraper package - {e}")
        return False
    
    return True

def test_file_structure():
    """Test if all required files are present"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'scraper/__init__.py',
        'scraper/rainmeter_scraper.py',
        'templates/base.html',
        'templates/index.html',
        'templates/scraper.html',
        'templates/viewer.html',
        'app.py',
        'run_scraper.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file}")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_scraper_functionality():
    """Test basic scraper functionality"""
    print("\n🕷️ Testing scraper functionality...")
    
    try:
        from scraper import RainmeterScraper
        scraper = RainmeterScraper(delay=1)
        print("  ✅ Scraper initialization")
        
        # Test URL formation
        test_url = scraper.base_url
        print(f"  ✅ Base URL: {test_url}")
        
        # Test basic methods exist
        assert hasattr(scraper, 'scrape_all_skins'), "Missing scrape_all_skins method"
        assert hasattr(scraper, 'clean_data'), "Missing clean_data method"
        assert hasattr(scraper, 'save_to_csv'), "Missing save_to_csv method"
        print("  ✅ Required methods present")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Scraper test failed: {e}")
        return False

def test_web_app():
    """Test if Flask app can be initialized"""
    print("\n🌐 Testing web application...")
    
    try:
        from app import app
        print("  ✅ Flask app import")
        
        # Test if app has required routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required_routes = ['/', '/scraper', '/viewer']
        
        for route in required_routes:
            if route in routes:
                print(f"  ✅ Route: {route}")
            else:
                print(f"  ❌ Missing route: {route}")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Web app test failed: {e}")
        return False

def create_data_directory():
    """Create data directory if it doesn't exist"""
    print("\n📂 Creating data directory...")
    os.makedirs('data', exist_ok=True)
    print("  ✅ data/ directory ready")

def main():
    """Run all tests"""
    print("🚀 Rainmeter Scraper Pro - Installation Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("File Structure Test", test_file_structure),
        ("Scraper Functionality Test", test_scraper_functionality),
        ("Web Application Test", test_web_app),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Create data directory
    create_data_directory()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your installation is ready.")
        print("\nQuick start:")
        print("  🌐 Web Interface: python app.py")
        print("  💻 CLI: python run_scraper.py --help")
    else:
        print("\n⚠️  Some tests failed. Please check the requirements and file structure.")
        print("💡 Try: pip install -r requirements.txt")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 