# 🕷️ Rainmeter Skins Scraper Pro

A professional web scraping tool designed to extract comprehensive data from [VisualSkins.com](https://visualskins.com/) - the premier destination for Rainmeter skins and customizations.

## ✨ Features

### 🎯 Professional Scraping Engine

- **Bulk scraping** with intelligent rate limiting
- **Robust error handling** with retry mechanisms
- **Duplicate detection** and automatic removal
- **Data validation** and cleaning
- **Progress tracking** with real-time updates

### 📊 Data Extraction

Extracts complete skin information including:

- **Skin names** and detailed descriptions
- **High-quality thumbnails** and preview images
- **Download links** (direct and external)
- **Developer information** and attribution
- **Ratings and reviews** data
- **Categories and tags** for organization
- **Additional metadata** (file size, version, etc.)

### 🖥️ Professional Web Interface

- **Modern responsive design** with Bootstrap 5
- **Real-time progress monitoring** with live updates
- **Interactive data viewer** with search and filtering
- **Grid and list view modes** for data browsing
- **Export functionality** (CSV/JSON formats)
- **Professional dashboard** with statistics

### ⚡ Command Line Interface

- **Flexible CLI** with comprehensive options
- **Batch processing** capabilities
- **Custom output formats** and naming
- **Verbose logging** for debugging

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd rainmeter-scraper
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Create necessary directories:**

```bash
mkdir -p data templates/static
```

## 📖 Usage

### 🌐 Web Interface (Recommended)

1. **Start the web application:**

```bash
python app.py
```

2. **Open your browser** and navigate to:

```
http://localhost:5000
```

3. **Use the interface:**
   - **Dashboard**: View statistics and quick actions
   - **Scraper**: Configure and start scraping jobs
   - **Data Viewer**: Browse, search, and export scraped data

### 💻 Command Line Interface

**Basic usage:**

```bash
python run_scraper.py
```

**Advanced options:**

```bash
# Limit to 50 pages with 2-second delay
python run_scraper.py --max-pages 50 --delay 2

# Custom output filename
python run_scraper.py --output my_custom_skins

# JSON output only with verbose logging
python run_scraper.py --format json --verbose

# Skip data cleaning (faster, but may include duplicates)
python run_scraper.py --no-cleanup
```

**All CLI options:**

```bash
python run_scraper.py --help
```

## 📁 Output Data Structure

### CSV Format

```csv
name,description,thumbnail_url,download_url,tags,rating,developer,category,scraped_at
"Elegant Clock","Beautiful minimalist clock skin","https://...",https://...","clock,minimal","4.5","DevName","Clock","2024-01-15T10:30:00"
```

### JSON Format

```json
{
  "name": "Elegant Clock",
  "description": "Beautiful minimalist clock skin for desktop customization",
  "thumbnail_url": "https://visualskins.com/preview/elegant-clock.jpg",
  "download_url": "https://visualskins.com/download/elegant-clock.rmskin",
  "tags": "clock, minimal, elegant",
  "rating": "4.5",
  "developer": "DevName",
  "category": "Clock",
  "downloads": "15,342",
  "file_size": "2.3 MB",
  "last_updated": "2024-01-10",
  "version": "1.2",
  "scraped_at": "2024-01-15T10:30:00.123456"
}
```

## 🛠️ Configuration

### Web Interface Settings

Configure scraping parameters through the web interface:

- **Max Pages**: Limit the number of pages to scrape
- **Request Delay**: Time between requests (be respectful!)
- **Output Options**: Choose between CSV, JSON, or both

### Environment Variables

```bash
FLASK_ENV=development  # Set to 'production' for production use
FLASK_PORT=5000       # Port for web interface
SCRAPER_DELAY=1       # Default delay between requests
```

## 📊 Data Quality Features

### 🧹 Automatic Data Cleaning

- **Text normalization**: Removes extra whitespace and special characters
- **URL validation**: Ensures download and thumbnail links are valid
- **Encoding handling**: Proper UTF-8 encoding for international content

### 🔍 Duplicate Detection

- **Content-based hashing**: Identifies duplicates by content similarity
- **Smart deduplication**: Keeps the most complete record when duplicates found
- **Statistics tracking**: Reports number of duplicates removed

## 🚦 Rate Limiting & Ethics

This scraper is designed to be **respectful** of the target website:

- ✅ **Default 1-second delay** between requests
- ✅ **Randomized user agents** to avoid detection
- ✅ **Retry logic** with exponential backoff
- ✅ **Error handling** to gracefully handle failures
- ✅ **Session management** for efficient connections

**Please be responsible:**

- Don't set delay below 0.5 seconds
- Monitor your usage and respect robots.txt
- Use scraped data ethically and legally

## 🔧 Technical Architecture

### Core Components

```
rainmeter-scraper/
├── scraper/
│   └── rainmeter_scraper.py    # Main scraping engine
├── templates/                   # Web interface templates
│   ├── base.html               # Base template
│   ├── index.html              # Dashboard
│   ├── scraper.html            # Scraper control
│   └── viewer.html             # Data viewer
├── data/                       # Output directory
├── app.py                      # Flask web application
├── run_scraper.py              # CLI interface
└── requirements.txt            # Dependencies
```

### Key Technologies

- **BeautifulSoup4**: HTML parsing and data extraction
- **Requests**: HTTP client with session management
- **Pandas**: Data manipulation and CSV export
- **Flask**: Web framework for GUI interface
- **Bootstrap 5**: Modern responsive UI framework

## 🐛 Troubleshooting

### Common Issues

**"No data scraped" error:**

- Check internet connection
- Verify website is accessible
- Try increasing delay with `--delay 2`

**Permission errors:**

- Ensure write permissions in project directory
- Create `data/` directory manually

**Memory issues with large datasets:**

- Use `--max-pages` to limit scope
- Process data in smaller batches

### Debug Mode

Enable verbose logging:

```bash
python run_scraper.py --verbose
```

## 📄 License

This project is for educational purposes. Please respect the target website's terms of service and use the scraped data responsibly.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 🆘 Support

For issues and questions:

1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed information

---

**Built with ❤️ for the Rainmeter community**
# SkinsCux
