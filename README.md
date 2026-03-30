# WordPress SEO Auto Poster (AI)

A fully automated, high-quality, SEO-optimized WordPress blog posting pipeline using Google Gemini.

## Features
- AI Content Generation (Info-blog style, complete with TOCs and tables).
- Text-based Pillow Thumbnail generation.
- Automated WordPress REST API publishing via JWT.
- Local Web Interface for manual topic typing and instant posting.

## Setup
1. Copy `.env.example` to `.env` and configure your API keys and WP credentials.
2. Install dependencies: `pip install -r requirements.txt`
3. Web UI: Run `python web_ui.py` to start the local Flask server on Port 5000.
4. Auto pipeline: Run `python auto_pipeline.py` to crawl/schedule posts.
