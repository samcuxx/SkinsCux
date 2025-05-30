import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import csv
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
from tqdm import tqdm
import json
import logging
from datetime import datetime
import hashlib
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
import random

class RainmeterScraper:
    def __init__(self, base_url="https://visualskins.com", delay=1, max_workers=8):
        self.base_url = base_url
        self.delay = delay
        self.max_workers = max_workers
        self.session = requests.Session()
        self.ua = UserAgent()
        self.scraped_data = []
        self.seen_urls = set()
        self.failed_urls = []
        self.discovered_urls = Queue()
        self.processing_stats = {
            'discovered_count': 0,
            'scraped_count': 0,
            'failed_count': 0,
            'discovery_complete': False
        }
        self._lock = threading.Lock()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Setup session headers with better user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def get_page(self, url, retries=3):
        """Safely fetch a page with error handling and retries"""
        for attempt in range(retries):
            try:
                # Rotate user agent occasionally
                if random.random() < 0.1:  # 10% chance to rotate
                    self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                # Random delay to avoid rate limiting
                time.sleep(self.delay + random.uniform(0, 0.5))
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    with self._lock:
                        self.failed_urls.append(url)
                        self.processing_stats['failed_count'] += 1
                    return None
                time.sleep(self.delay * (attempt + 1))
        return None

    def clean_text(self, text):
        """Clean and normalize text data"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII characters
        return text

    def discover_comprehensive_urls(self):
        """Professional comprehensive URL discovery using multiple strategies"""
        all_urls = set()
        
        # Strategy 1: Category-based discovery
        categories = [
            # Main categories from site structure
            '/tag/themes/',
            '/tag/weather/',
            '/tag/clock/',
            '/tag/visualizer/',
            '/tag/launcher/',
            
            # Featured categories
            '/tag/system-monitor/',
            '/tag/cpu/',
            '/tag/battery/',
            '/tag/network/',
            '/tag/hdd/',
            '/tag/ram/',
            '/tag/wifi/',
            
            # Skins by category
            '/tag/time-and-date/',
            '/tag/music/',
            '/tag/calendar/',
            '/tag/notes/',
            '/tag/effects/',
            '/tag/wallpaper/',
            '/tag/volume/',
            '/tag/recycle-bin/',
            '/tag/search/',
            '/tag/countdown/',
            '/tag/currency/',
            '/tag/e-mail/',
            
            # Skins by style
            '/tag/minimalism/',
            '/tag/anime/',
            '/tag/steampunk/',
            '/tag/fallout/',
            
            # Collection pages
            '/best-rainmeter-skins/',
            '/rainmeter-equalizer/',
            '/rainmeter-docks/',
            
            # Additional categories found from research
            '/tag/time/',
            '/tag/date/',
            '/tag/system/',
            '/tag/monitoring/',
            '/tag/desktop/',
            '/tag/widgets/',
            '/tag/skins/',
            '/tag/windows/',
        ]
        
        # Strategy 2: Add pagination for each category (up to 50 pages each)
        paginated_urls = []
        for category in categories:
            for page in range(1, 51):  # Try up to 50 pages per category
                paginated_urls.append(f"{category}page/{page}/")
                if 'tag' not in category:  # For non-tag URLs
                    paginated_urls.append(f"{category}/page/{page}/")
        
        # Strategy 3: Alphabetical skin discovery
        alphabet_urls = []
        for letter in 'abcdefghijklmnopqrstuvwxyz0123456789':
            alphabet_urls.extend([
                f"/search/?q={letter}",
                f"/tag/{letter}/",
                f"/?s={letter}",
            ])
        
        # Strategy 4: Main site pagination (up to 100 pages)
        main_pagination = [f"/page/{i}/" for i in range(1, 101)]
        
        # Combine all strategies
        discovery_urls = categories + paginated_urls + alphabet_urls + main_pagination
        
        # Convert relative URLs to absolute
        full_urls = [urljoin(self.base_url, url) for url in discovery_urls]
        
        self.logger.info(f"Generated {len(full_urls)} discovery URLs using professional multi-strategy approach")
        return full_urls

    def extract_skin_links_worker(self, category_url):
        """Enhanced worker function for extracting skin links with better selectors"""
        try:
            response = self.get_page(category_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            skin_links = []
            
            # Enhanced selectors based on site structure analysis
            selectors = [
                # Direct skin links
                'a[href*="/skin/"]',
                
                # Title and heading links
                'h1 a[href*="/skin/"]',
                'h2 a[href*="/skin/"]', 
                'h3 a[href*="/skin/"]',
                'h4 a[href*="/skin/"]',
                
                # Post and entry links
                '.entry-title a',
                '.post-title a',
                '.skin-title a',
                
                # Article and content links
                'article a[href*="/skin/"]',
                '.content a[href*="/skin/"]',
                '.post-content a[href*="/skin/"]',
                
                # Grid and list items
                '.grid-item a',
                '.list-item a',
                '.skin-item a',
                '.item a',
                
                # Thumbnail and image links
                '.thumbnail a',
                '.image a',
                '.featured-image a',
                
                # Card and widget links
                '.card a',
                '.widget a',
                '.skin-card a',
                
                # More/read more links
                '.more-link',
                '.read-more',
                '.continue-reading',
                
                # Links with skin-related attributes
                'a[title*="Skin"]',
                'a[title*="skin"]',
                'a[title*="Rainmeter"]',
                'a[title*="rainmeter"]',
                
                # Generic content links that might contain skins
                '.entry a',
                '.post a',
                'main a',
                '#content a',
                
                # Search result links
                '.search-result a',
                '.result a',
                
                # Navigation and pagination
                '.navigation a',
                '.pagination a',
                '.page-numbers a',
            ]
            
            # Process each selector
            for selector in selectors:
                try:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            
                            # Enhanced filtering for skin URLs
                            if (('/skin/' in full_url or 
                                 '/theme/' in full_url or
                                 '/widget/' in full_url or
                                 '/rainmeter/' in full_url) and 
                                full_url not in self.seen_urls and
                                'visualskins.com' in full_url and
                                not any(exclude in full_url.lower() for exclude in [
                                    'javascript:', 'mailto:', 'tel:', 
                                    'contact', 'about', 'privacy', 'terms',
                                    'how-to', 'tutorial', 'guide'
                                ])):
                                
                                skin_links.append(full_url)
                                with self._lock:
                                    self.seen_urls.add(full_url)
                except Exception as e:
                    continue  # Skip problematic selectors
            
            # Additional discovery for collection/category pages
            if any(keyword in category_url.lower() for keyword in [
                'best-rainmeter', 'collection', 'rainmeter-', 'tag/'
            ]):
                # Look for any links that might lead to skins
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        # Be more permissive for collection pages
                        if ('visualskins.com' in full_url and 
                            full_url not in self.seen_urls and
                            not any(exclude in full_url.lower() for exclude in [
                                'javascript:', 'mailto:', 'tel:', 'contact', 
                                'about', 'privacy', 'wp-', 'admin'
                            ])):
                            
                            # Check if link text suggests it's a skin
                            link_text = link.get_text().lower()
                            if any(keyword in link_text for keyword in [
                                'skin', 'theme', 'widget', 'rainmeter', 'clock',
                                'visualizer', 'weather', 'system', 'monitor'
                            ]):
                                skin_links.append(full_url)
                                with self._lock:
                                    self.seen_urls.add(full_url)
            
            # Remove duplicates while preserving order
            unique_skin_links = []
            seen_in_this_batch = set()
            for link in skin_links:
                if link not in seen_in_this_batch:
                    unique_skin_links.append(link)
                    seen_in_this_batch.add(link)
            
            if unique_skin_links:
                self.logger.info(f"Found {len(unique_skin_links)} skin links from {category_url}")
            
            return unique_skin_links
            
        except Exception as e:
            self.logger.error(f"Error extracting links from {category_url}: {e}")
            return []

    def discovery_worker(self, category_urls, max_urls=None):
        """Enhanced discovery worker with intelligent completion detection"""
        
        # Use comprehensive discovery instead of limited categories
        if not hasattr(self, '_comprehensive_urls_generated'):
            comprehensive_urls = self.discover_comprehensive_urls()
            category_urls.extend(comprehensive_urls)
            self._comprehensive_urls_generated = True
            self.logger.info(f"Enhanced discovery with {len(category_urls)} total URLs to check")
        
        with ThreadPoolExecutor(max_workers=min(8, self.max_workers)) as executor:
            # Process URLs in batches to avoid overwhelming the server
            batch_size = 25  # Smaller batches for better control
            total_discovered = 0
            last_discovery_count = 0
            stagnant_batches = 0
            max_stagnant_batches = 8  # Allow 8 batches without new discoveries
            
            for i in range(0, len(category_urls), batch_size):
                batch = category_urls[i:i+batch_size]
                
                future_to_url = {executor.submit(self.extract_skin_links_worker, url): url 
                               for url in batch}
                
                batch_discoveries = 0
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        skin_links = future.result()
                        for skin_url in skin_links:
                            self.discovered_urls.put(skin_url)
                            total_discovered += 1
                            batch_discoveries += 1
                            with self._lock:
                                self.processing_stats['discovered_count'] += 1
                            
                            # Stop discovery if we have enough URLs (with generous buffer)
                            if max_urls and total_discovered >= max_urls * 2:
                                break
                        
                        if max_urls and total_discovered >= max_urls * 2:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Discovery error for {url}: {e}")
                
                # Check for stagnation (no new discoveries in this batch)
                if batch_discoveries == 0:
                    stagnant_batches += 1
                    self.logger.debug(f"Batch {i//batch_size + 1} found no new URLs. Stagnant count: {stagnant_batches}")
                else:
                    stagnant_batches = 0  # Reset if we found something
                    self.logger.info(f"Batch {i//batch_size + 1} discovered {batch_discoveries} new URLs. Total: {total_discovered}")
                
                # Intelligent completion detection
                if stagnant_batches >= max_stagnant_batches:
                    self.logger.info(f"Discovery appears complete - no new URLs found in {max_stagnant_batches} consecutive batches")
                    break
                
                # Check if we should stop processing more batches
                if max_urls and total_discovered >= max_urls:
                    self.logger.info(f"Reached discovery target with {total_discovered} URLs")
                    break
                
                # Check if we've found a reasonable number of skins
                if total_discovered >= 500:  # More than the claimed 394 we found before
                    remaining_batches = (len(category_urls) - i) // batch_size
                    if remaining_batches > 50:  # If many batches remain, check for diminishing returns
                        recent_rate = batch_discoveries / batch_size if batch_size > 0 else 0
                        if recent_rate < 0.02:  # Less than 2% discovery rate
                            self.logger.info(f"Discovery rate too low ({recent_rate:.1%}). Stopping early with {total_discovered} URLs")
                            break
                
                # Brief pause between batches to be respectful
                time.sleep(0.3)
        
        # Mark discovery as complete
        with self._lock:
            self.processing_stats['discovery_complete'] = True
        
        self.logger.info(f"Professional discovery complete. Found {total_discovered} unique skin URLs using intelligent completion detection")

    def extract_skin_details(self, skin_url):
        """Extract detailed information from a skin page (same as before but optimized)"""
        response = self.get_page(skin_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Initialize skin data structure
        skin_data = {
            'url': skin_url,
            'name': '',
            'description': '',
            'thumbnail_url': '',
            'download_url': '',
            'tags': '',
            'rating': '',
            'developer': '',
            'category': '',
            'downloads': '',
            'file_size': '',
            'last_updated': '',
            'version': '',
            'scraped_at': datetime.now().isoformat()
        }
        
        # Extract name from h1 title
        name_element = soup.select_one('h1.title')
        if name_element:
            name_text = name_element.get_text().strip()
            # Clean up "Rainmeter Theme" suffix
            name_text = re.sub(r'\s*rainmeter\s*theme\s*$', '', name_text, flags=re.IGNORECASE)
            skin_data['name'] = self.clean_text(name_text)
        
        # Extract description from the desc div
        desc_element = soup.select_one('div.desc p')
        if desc_element:
            desc_text = desc_element.get_text().strip()
            skin_data['description'] = self.clean_text(desc_text)
        
        # If no description found, try meta description
        if not skin_data['description']:
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc:
                skin_data['description'] = self.clean_text(meta_desc.get('content', ''))
        
        # Extract thumbnail from slider images
        img_element = soup.select_one('div.uk-slider-items img')
        if img_element:
            src = img_element.get('src')
            if src:
                skin_data['thumbnail_url'] = urljoin(self.base_url, src)
        
        # Extract download link and file info
        download_element = soup.select_one('a.uk-button-primary[href*=".rmskin"]')
        if download_element:
            href = download_element.get('href')
            if href:
                skin_data['download_url'] = urljoin(self.base_url, href)
                
                # Extract file size from download button text
                button_text = download_element.get_text()
                size_match = re.search(r'\(([^)]+)\)', button_text)
                if size_match:
                    skin_data['file_size'] = size_match.group(1)
        
        # Extract developer from infobox
        developer_elements = soup.select('dt')
        for dt in developer_elements:
            if dt.get_text().strip().upper() == 'DEVELOPER':
                dd_element = dt.find_next_sibling('dd')
                if dd_element:
                    # Get the link text or just the text content
                    dev_link = dd_element.select_one('a')
                    if dev_link:
                        skin_data['developer'] = self.clean_text(dev_link.get_text())
                    else:
                        skin_data['developer'] = self.clean_text(dd_element.get_text())
                    break
        
        # Extract rating
        rate_element = soup.select_one('div.ratetxt')
        if rate_element:
            rating_text = rate_element.get_text().strip()
            if 'not rated' not in rating_text.lower():
                skin_data['rating'] = self.clean_text(rating_text)
        
        # Extract date added
        date_elements = soup.select('dt')
        for dt in date_elements:
            if 'date added' in dt.get_text().strip().lower():
                dd_element = dt.find_next_sibling('dd')
                if dd_element:
                    skin_data['last_updated'] = self.clean_text(dd_element.get_text())
                    break
        
        # Extract tags from sidebar
        tag_elements = soup.select('div.tmenu a[href*="/tag/"]')
        tags = []
        for tag_elem in tag_elements:
            tag_text = tag_elem.get_text().strip()
            # Clean out SVG and other unwanted content
            if tag_text and len(tag_text) > 1 and not tag_text.startswith('<'):
                tags.append(tag_text)
        
        if tags:
            skin_data['tags'] = ', '.join(tags[:10])  # Limit to 10 tags
        
        # Extract category from breadcrumb or URL
        breadcrumb_elements = soup.select('ul.uk-breadcrumb a')
        for breadcrumb in breadcrumb_elements:
            href = breadcrumb.get('href', '')
            if '/tag/' in href:
                category = breadcrumb.get_text().strip()
                if category and category.lower() not in ['rainmeter skins']:
                    skin_data['category'] = self.clean_text(category)
                    break
        
        # Extract additional file information
        info_elements = soup.select('dt')
        for dt in info_elements:
            dt_text = dt.get_text().strip().upper()
            dd_element = dt.find_next_sibling('dd')
            
            if dd_element:
                dd_text = self.clean_text(dd_element.get_text())
                
                if 'FILENAME' in dt_text:
                    # Extract version from filename if available
                    version_match = re.search(r'(\d+[\._]\d+)', dd_text)
                    if version_match:
                        skin_data['version'] = version_match.group(1).replace('_', '.')
                
                elif 'FILE SIZE' in dt_text and not skin_data['file_size']:
                    skin_data['file_size'] = dd_text
        
        # Generate content hash for duplicate detection
        content_hash = hashlib.md5(
            f"{skin_data['name']}{skin_data['developer']}{skin_data['download_url']}".encode()
        ).hexdigest()
        skin_data['content_hash'] = content_hash
        
        return skin_data

    def scraping_worker(self):
        """Enhanced worker function for scraping skins with better error handling and performance"""
        consecutive_empty = 0
        max_consecutive_empty = 20  # Increased tolerance for large scraping jobs
        
        while True:
            try:
                # Get URL from queue with timeout
                skin_url = self.discovered_urls.get(timeout=5)
                consecutive_empty = 0  # Reset counter on successful get
                
                skin_data = self.extract_skin_details(skin_url)
                if skin_data:
                    with self._lock:
                        self.scraped_data.append(skin_data)
                        self.processing_stats['scraped_count'] += 1
                        
                    self.logger.debug(f"Successfully scraped: {skin_data.get('title', 'Unknown')}")
                
                # Mark task as done
                self.discovered_urls.task_done()
                
            except Empty:
                consecutive_empty += 1
                
                # Check if discovery is complete and queue is empty
                with self._lock:
                    discovery_complete = self.processing_stats.get('discovery_complete', False)
                    queue_size = self.discovered_urls.qsize()
                
                if discovery_complete and queue_size == 0:
                    self.logger.info("Scraping worker finished - discovery complete and queue empty")
                    break
                elif consecutive_empty >= max_consecutive_empty:
                    self.logger.warning("Scraping worker timeout - no URLs for extended period")
                    break
                else:
                    # Brief sleep before retrying
                    time.sleep(0.5)
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error in scraping worker: {e}")
                try:
                    self.discovered_urls.task_done()
                except ValueError:
                    pass  # Task wasn't gotten from queue
                time.sleep(0.5)

    def discover_categories(self):
        """Enhanced category discovery - now just returns initial seed URLs"""
        # Start with basic seed URLs - comprehensive discovery will expand these
        seed_urls = [
            f"{self.base_url}/",
            f"{self.base_url}/tag/themes/",
            f"{self.base_url}/tag/clock/",
            f"{self.base_url}/tag/visualizer/",
            f"{self.base_url}/tag/weather/",
            f"{self.base_url}/tag/launcher/",
            f"{self.base_url}/best-rainmeter-skins/",
        ]
        
        return seed_urls

    def scrape_all_skins_parallel(self, max_pages=None):
        """Enhanced main parallel scraping function with professional monitoring"""
        try:
            self.logger.info("Starting professional parallel Rainmeter skins scraping...")
            
            # Reset processing stats
            with self._lock:
                self.processing_stats = {
                    'discovered_count': 0,
                    'scraped_count': 0,
                    'discovery_complete': False,
                    'scraping_rate': 0,
                    'discovery_rate': 0
                }
            
            # Clear previous data
            self.scraped_data = []
            self.seen_urls = set()
            
            # Discover initial categories
            category_urls = self.discover_categories()
            
            # Start discovery worker in a separate thread
            discovery_thread = threading.Thread(
                target=self.discovery_worker, 
                args=(category_urls, max_pages)
            )
            discovery_thread.daemon = True
            discovery_thread.start()
            
            # Start scraping workers
            scraping_threads = []
            num_scraping_workers = min(self.max_workers, 12)  # Increased for large jobs
            
            for i in range(num_scraping_workers):
                thread = threading.Thread(target=self.scraping_worker)
                thread.daemon = True
                thread.start()
                scraping_threads.append(thread)
            
            # Enhanced monitoring with stall detection
            last_scraped_count = 0
            last_discovered_count = 0
            stall_counter = 0
            max_stalls = 10  # Increased tolerance
            
            # Monitor progress with detailed logging
            while True:
                time.sleep(2)  # Monitor every 2 seconds
                
                with self._lock:
                    discovered_count = self.processing_stats['discovered_count']
                    scraped_count = self.processing_stats['scraped_count']
                    discovery_complete = self.processing_stats['discovery_complete']
                
                queue_size = self.discovered_urls.qsize()
                
                # Log progress every 10 items or every 10 seconds
                if scraped_count % 10 == 0 or scraped_count != last_scraped_count:
                    self.logger.info(f"Progress: {discovered_count} URLs discovered, {scraped_count} skins scraped")
                
                # Check for completion
                if discovery_complete and queue_size == 0 and scraped_count >= discovered_count:
                    self.logger.info("All discovery and scraping complete")
                    break
                
                # Enhanced stall detection
                if (scraped_count == last_scraped_count and 
                    discovered_count == last_discovered_count and 
                    not discovery_complete):
                    stall_counter += 1
                    
                    if stall_counter >= max_stalls:
                        self.logger.warning("Scraping appears stalled. Checking status...")
                        
                        # Check if workers are still active
                        active_threads = sum(1 for t in scraping_threads if t.is_alive())
                        if active_threads == 0:
                            self.logger.warning("No active scraping workers. Restarting...")
                            
                            # Restart scraping workers
                            scraping_threads = []
                            for i in range(num_scraping_workers):
                                thread = threading.Thread(target=self.scraping_worker)
                                thread.daemon = True
                                thread.start()
                                scraping_threads.append(thread)
                        
                        if queue_size == 0 and not discovery_complete:
                            self.logger.warning("Queue empty but discovery not complete. May be finished.")
                        
                        stall_counter = 0  # Reset stall counter
                else:
                    stall_counter = 0
                
                last_scraped_count = scraped_count
                last_discovered_count = discovered_count
                
                # Safety timeout for very large jobs (2 hours max)
                if hasattr(self, 'start_time'):
                    elapsed = time.time() - self.start_time
                    if elapsed > 7200:  # 2 hours
                        self.logger.warning("Maximum scraping time reached. Stopping.")
                        break
                else:
                    self.start_time = time.time()
            
            # Wait for discovery to complete with generous timeout
            if discovery_thread.is_alive():
                discovery_thread.join(timeout=30)
                if discovery_thread.is_alive():
                    self.logger.warning("Discovery thread still running after timeout")
            
            # Wait for all scraping workers to finish
            for thread in scraping_threads:
                if thread.is_alive():
                    thread.join(timeout=15)
            
            # Final cleanup - wait for queue to empty
            try:
                self.discovered_urls.join()
            except:
                pass
            
            # Force stop any remaining workers
            remaining_workers = [t for t in scraping_threads if t.is_alive()]
            if remaining_workers:
                self.logger.info(f"Force-stopping {len(remaining_workers)} remaining workers")
            
            final_count = len(self.scraped_data)
            self.logger.info(f"Professional parallel scraping complete. Successfully scraped {final_count} skins")
            
            # Clean and deduplicate data
            cleaned_data = self.clean_data()
            
            return cleaned_data
            
        except Exception as e:
            self.logger.error(f"Error in parallel scraping: {e}")
            return self.scraped_data if hasattr(self, 'scraped_data') else []

    # Keep existing methods for compatibility
    def scrape_all_skins(self, max_pages=None):
        """Wrapper method that uses parallel scraping"""
        return self.scrape_all_skins_parallel(max_pages)

    def get_progress_stats(self):
        """Get current progress statistics"""
        with self._lock:
            return self.processing_stats.copy()

    def remove_duplicates(self):
        """Remove duplicate entries based on content hash"""
        seen_hashes = set()
        unique_data = []
        
        for item in self.scraped_data:
            content_hash = item.get('content_hash')
            if content_hash and content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_data.append(item)
        
        removed_count = len(self.scraped_data) - len(unique_data)
        self.scraped_data = unique_data
        self.logger.info(f"Removed {removed_count} duplicate entries")

    def clean_data(self):
        """Clean and validate scraped data"""
        cleaned_data = []
        
        for item in self.scraped_data:
            # Skip items without essential data
            if not item.get('name') or not item.get('url'):
                continue
            
            # Clean each field
            for key, value in item.items():
                if isinstance(value, str):
                    item[key] = self.clean_text(value)
            
            cleaned_data.append(item)
        
        self.scraped_data = cleaned_data
        self.logger.info(f"Cleaned data, {len(self.scraped_data)} items remaining")

    def save_to_csv(self, filename="rainmeter_skins.csv"):
        """Save scraped data to CSV file"""
        if not self.scraped_data:
            self.logger.warning("No data to save")
            return
        
        df = pd.DataFrame(self.scraped_data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        self.logger.info(f"Data saved to {filename}")

    def save_to_json(self, filename="rainmeter_skins.json"):
        """Save scraped data to JSON file"""
        if not self.scraped_data:
            self.logger.warning("No data to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Data saved to {filename}")

    def get_stats(self):
        """Get scraping statistics"""
        return {
            'total_scraped': len(self.scraped_data),
            'failed_urls': len(self.failed_urls),
            'unique_developers': len(set(item.get('developer', '') for item in self.scraped_data if item.get('developer'))),
            'with_downloads': len([item for item in self.scraped_data if item.get('download_url')]),
            'with_thumbnails': len([item for item in self.scraped_data if item.get('thumbnail_url')])
        } 