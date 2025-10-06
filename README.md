# JD Growth Scraper

A Facebook group automation tool for admins to efficiently manage group engagement.

## Features
- Automated Facebook login
- Group post scraping
- Automated admin comment posting
- Rate limiting and safety features
- Configurable messages and settings

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your settings:
```bash
cp .env.example .env
# Edit .env with your Facebook credentials and preferences
```

3. Run the scraper:
```bash
python main.py
```

## Configuration

Edit the `.env` file to customize:
- Your Facebook login credentials
- Group ID and URL
- Comment templates
- Timing and rate limiting settings
- Browser behavior

## Safety Features

- Rate limiting between actions
- Duplicate comment detection
- Error handling and retry logic
- Comprehensive logging
- Respect for Facebook's rate limits

## Disclaimer

This tool is for legitimate group administration purposes. Ensure you comply with:
- Facebook's Terms of Service
- Your group's rules and guidelines
- Applicable laws and regulations

Use responsibly and ethically.