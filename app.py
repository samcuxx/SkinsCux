from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
import json
import os
from datetime import datetime
from scraper.rainmeter_scraper import RainmeterScraper
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Global variables for scraping status
scraping_status = {
    'is_running': False,
    'progress': 0,
    'current_task': 'Ready to start',
    'total_found': 0,
    'scraped_count': 0,
    'discovered_count': 0,
    'discovery_complete': False,
    'errors': [],
    'start_time': None,
    'estimated_time': None,
    'scraping_rate': 0,  # skins per minute
    'discovery_rate': 0  # URLs per minute
}

scraper_instance = None
scraper_thread = None

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/scraper')
def scraper_page():
    """Scraper control interface"""
    return render_template('scraper.html')

@app.route('/viewer')
def viewer_page():
    """Data viewer page"""
    return render_template('viewer.html')

@app.route('/api/start_scraping', methods=['POST'])
def start_scraping():
    """Start the scraping process"""
    global scraping_status, scraper_instance, scraper_thread
    
    if scraping_status['is_running']:
        return jsonify({'error': 'Scraping is already in progress'}), 400
    
    # Get parameters from request
    try:
        data = request.get_json() or {}
        max_pages = data.get('max_pages', None)
        delay = float(data.get('delay', 1))
        max_workers = int(data.get('max_workers', 8))  # New parameter for thread count
        
        if max_pages:
            max_pages = int(max_pages)
            
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid parameters: {str(e)}'}), 400
    
    # Reset status
    scraping_status = {
        'is_running': True,
        'progress': 0,
        'current_task': 'Initializing parallel scraper...',
        'total_found': 0,
        'scraped_count': 0,
        'discovered_count': 0,
        'discovery_complete': False,
        'errors': [],
        'start_time': datetime.now().isoformat(),
        'estimated_time': None,
        'scraping_rate': 0,
        'discovery_rate': 0
    }
    
    # Start scraping in background thread
    def run_parallel_scraper():
        global scraper_instance, scraping_status
        try:
            scraper_instance = RainmeterScraper(delay=delay, max_workers=max_workers)
            
            scraping_status['current_task'] = 'Starting parallel discovery and scraping...'
            scraping_status['progress'] = 5
            
            start_time = time.time()
            last_update_time = start_time
            last_discovered = 0
            last_scraped = 0
            
            # Start parallel scraping
            scraper_instance.scrape_all_skins_parallel(max_pages=max_pages)
            
            if not scraping_status['is_running']:
                scraping_status['current_task'] = 'Stopped by user'
                return
            
            scraping_status['current_task'] = 'Cleaning and saving data...'
            scraping_status['progress'] = 95
            
            scraper_instance.clean_data()
            scraper_instance.remove_duplicates()
            
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            
            scraper_instance.save_to_csv('data/rainmeter_skins.csv')
            scraper_instance.save_to_json('data/rainmeter_skins.json')
            
            scraping_status['current_task'] = 'Completed!'
            scraping_status['progress'] = 100
            
            # Final statistics
            final_stats = scraper_instance.get_progress_stats()
            scraping_status['scraped_count'] = final_stats['scraped_count']
            scraping_status['discovered_count'] = final_stats['discovered_count']
            
        except Exception as e:
            scraping_status['errors'].append(str(e))
            scraping_status['current_task'] = f'Error: {str(e)}'
        finally:
            scraping_status['is_running'] = False
    
    scraper_thread = threading.Thread(target=run_parallel_scraper)
    scraper_thread.daemon = True
    scraper_thread.start()
    
    return jsonify({'message': 'Parallel scraping started successfully'})

@app.route('/api/scraping_status')
def get_scraping_status():
    """Get current scraping status with enhanced parallel information"""
    global scraper_instance, scraping_status
    
    # If scraper is running, get live stats
    if scraper_instance and scraping_status['is_running']:
        try:
            live_stats = scraper_instance.get_progress_stats()
            scraping_status.update({
                'discovered_count': live_stats['discovered_count'],
                'scraped_count': live_stats['scraped_count'],
                'discovery_complete': live_stats['discovery_complete'],
                'failed_count': live_stats.get('failed_count', 0)
            })
        except:
            pass  # Continue with cached status if live update fails
    
    return jsonify(scraping_status)

@app.route('/api/stop_scraping', methods=['POST'])
def stop_scraping():
    """Stop the scraping process and save current data"""
    global scraping_status, scraper_instance
    
    if scraping_status['is_running']:
        scraping_status['is_running'] = False
        scraping_status['current_task'] = 'Stopping and saving data...'
        
        # Force save current data if scraper instance exists
        if scraper_instance and hasattr(scraper_instance, 'scraped_data') and scraper_instance.scraped_data:
            try:
                # Save current data immediately
                cleaned_data = scraper_instance.clean_data()
                if cleaned_data:
                    filename = scraper_instance.save_to_files(cleaned_data)
                    scraping_status['current_task'] = f'Data saved to {filename}'
                    scraping_status['scraped_count'] = len(cleaned_data)
                    print(f"✅ Force saved {len(cleaned_data)} skins to {filename}")
                else:
                    scraping_status['current_task'] = 'No valid data to save'
            except Exception as e:
                print(f"❌ Error saving data: {e}")
                scraping_status['current_task'] = f'Error saving data: {e}'
        
        scraping_status['is_running'] = False
        return jsonify({'message': 'Scraping stopped and data saved'})
    else:
        return jsonify({'message': 'No scraping process running'})

@app.route('/api/force_save', methods=['POST'])
def force_save():
    """Force save current scraped data without stopping the scraper"""
    global scraper_instance
    
    if scraper_instance and hasattr(scraper_instance, 'scraped_data') and scraper_instance.scraped_data:
        try:
            cleaned_data = scraper_instance.clean_data()
            if cleaned_data:
                filename = scraper_instance.save_to_files(cleaned_data)
                return jsonify({
                    'message': f'Successfully saved {len(cleaned_data)} skins',
                    'filename': filename,
                    'count': len(cleaned_data)
                })
            else:
                return jsonify({'error': 'No valid data to save'})
        except Exception as e:
            return jsonify({'error': f'Error saving data: {e}'})
    else:
        return jsonify({'error': 'No scraped data available'})

@app.route('/api/get_data')
def get_data():
    """Get scraped data for display"""
    try:
        data = []
        
        # Try to load from the most recent file
        csv_path = 'data/rainmeter_skins.csv'
        json_path = 'data/rainmeter_skins.json'
        
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                data = df.fillna('').to_dict('records')
            except Exception as e:
                print(f"Error reading CSV: {e}")
        
        if not data and os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading JSON: {e}")
        
        # Get summary statistics
        stats = {
            'total_skins': len(data),
            'unique_developers': len(set(item.get('developer', '') for item in data if item.get('developer', '').strip())),
            'with_downloads': len([item for item in data if item.get('download_url', '').strip()]),
            'with_thumbnails': len([item for item in data if item.get('thumbnail_url', '').strip()]),
            'categories': list(set(item.get('category', '') for item in data if item.get('category', '').strip()))
        }
        
        return jsonify({
            'data': data[:50],  # Limit to first 50 for performance
            'total_count': len(data),
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error in get_data: {e}")
        return jsonify({
            'data': [],
            'total_count': 0,
            'stats': {
                'total_skins': 0,
                'unique_developers': 0,
                'with_downloads': 0,
                'with_thumbnails': 0,
                'categories': []
            }
        })

@app.route('/api/search')
def search_data():
    """Search scraped data"""
    try:
        query = request.args.get('q', '').lower().strip()
        category = request.args.get('category', '').strip()
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(50, max(10, int(request.args.get('per_page', 20))))
        
        # Load data
        data = []
        csv_path = 'data/rainmeter_skins.csv'
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            data = df.fillna('').to_dict('records')
        
        # Filter data
        filtered_data = []
        for item in data:
            # Text search
            if query:
                searchable_fields = [
                    item.get('name', ''),
                    item.get('description', ''),
                    item.get('tags', ''),
                    item.get('developer', '')
                ]
                searchable_text = ' '.join(str(field) for field in searchable_fields).lower()
                if query not in searchable_text:
                    continue
            
            # Category filter
            if category and item.get('category', '') != category:
                continue
            
            filtered_data.append(item)
        
        # Pagination
        total_pages = (len(filtered_data) + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_data = filtered_data[start_idx:end_idx]
        
        return jsonify({
            'data': paginated_data,
            'total_count': len(filtered_data),
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        })
        
    except Exception as e:
        print(f"Error in search: {e}")
        return jsonify({
            'data': [],
            'total_count': 0,
            'page': 1,
            'per_page': 20,
            'total_pages': 0
        })

@app.route('/api/export/<format>')
def export_data(format):
    """Export data in different formats"""
    try:
        csv_path = 'data/rainmeter_skins.csv'
        json_path = 'data/rainmeter_skins.json'
        
        if format == 'csv' and os.path.exists(csv_path):
            return send_file(csv_path, as_attachment=True, download_name='rainmeter_skins.csv')
        elif format == 'json' and os.path.exists(json_path):
            return send_file(json_path, as_attachment=True, download_name='rainmeter_skins.json')
        else:
            return jsonify({'error': 'No data available to export'}), 404
            
    except Exception as e:
        print(f"Error in export: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get detailed statistics"""
    try:
        if os.path.exists('data/rainmeter_skins.csv'):
            df = pd.read_csv('data/rainmeter_skins.csv')
            
            stats = {
                'total_skins': len(df),
                'unique_developers': df['developer'].nunique(),
                'avg_rating': df['rating'].astype(str).str.extract(r'(\d+\.?\d*)').astype(float).mean().iloc[0] if 'rating' in df.columns else 0,
                'top_developers': df['developer'].value_counts().head(10).to_dict(),
                'top_categories': df['category'].value_counts().head(10).to_dict() if 'category' in df.columns else {},
                'scraping_date': datetime.now().isoformat()
            }
            
            return jsonify(stats)
        else:
            return jsonify({'error': 'No data available'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/performance_stats')
def get_performance_stats():
    """Get performance statistics for parallel scraping"""
    global scraper_instance, scraping_status
    
    if scraper_instance and scraping_status['is_running']:
        try:
            stats = scraper_instance.get_progress_stats()
            return jsonify({
                'discovery_rate': scraping_status.get('discovery_rate', 0),
                'scraping_rate': scraping_status.get('scraping_rate', 0),
                'discovered_count': stats['discovered_count'],
                'scraped_count': stats['scraped_count'],
                'failed_count': stats.get('failed_count', 0),
                'discovery_complete': stats['discovery_complete'],
                'estimated_time': scraping_status.get('estimated_time', 'Calculating...')
            })
        except:
            pass
    
    return jsonify({
        'discovery_rate': 0,
        'scraping_rate': 0,
        'discovered_count': 0,
        'scraped_count': 0,
        'failed_count': 0,
        'discovery_complete': False,
        'estimated_time': 'N/A'
    })

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000) 