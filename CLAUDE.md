# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Telegram bot** for downloading videos from YouTube and other platforms, with an integrated **FastAPI web interface**. It's a fork of tgbot-collection/ytdlbot with additional features including multi-language support (Chinese/English), resolution selection, and automatic URL extraction.

## Key Architecture

### Unified Deployment Model

The project supports running both Telegram Bot and Web API in a **single process**:

- **Entry Point**: `src/main.py`
  - Main thread: Pyrogram Telegram bot (blocking)
  - Background daemon thread: FastAPI web server (if `ENABLE_WEB=true`)
  - Both services share: database, Redis cache, configurations, and yt-dlp core

### Core Components

1. **Download Engine Hierarchy**:
   - `src/engine/base.py`: `BaseDownloader` - Abstract base class for all downloaders
   - `src/engine/generic.py`: `YoutubeDownload` - YouTube-specific downloader with format selection
   - `src/engine/direct.py`: `DirectDownload` - For direct file downloads
   - `src/engine/instagram.py`: `InstagramDownload` - Instagram media downloader
   - `src/engine/pixeldrain.py`, `krakenfiles.py` - Specialized downloaders
   - `src/engine/__init__.py`: Entry point functions (`youtube_entrance`, `direct_entrance`, `special_download_entrance`)

2. **Dual Download Engines**:
   - **TG Bot Engine**: Uses `BaseDownloader` subclasses with Pyrogram client
   - **Web Engine**: `src/web/downloader.py` - Standalone `WebDownloader` class
   - Both use yt-dlp underneath but have different interfaces and progress handling

3. **Database Layer**:
   - `src/database/model.py`: SQLAlchemy models for users, quotas, settings
   - `src/database/cache.py`: Redis wrapper for caching downloads and pending tasks
   - Supports MySQL/PostgreSQL (production) and SQLite (development)

4. **Configuration System**:
   - `src/config/config.py`: Environment variable parsing with type coercion
   - `src/config/i18n.py`: `BotText` class for multi-language support
   - `.env` file required (copy from `.env.example`)

### Web API Structure

- **FastAPI App**: `src/web/app.py`
  - REST endpoints: `/api/info`, `/api/download`, `/api/download/{task_id}`, `/api/file/{task_id}`
  - WebSocket: `/ws/{task_id}` for real-time download progress
  - Serves `index.html` from project root or `src/web/static/`
- **Task Management**: In-memory task storage in `WebDownloader.tasks` dict
- **Background Cleanup**: Async task removes temp files older than 1 hour

## Development Commands

### Setup

```bash
# Install dependencies (preferred)
pdm install

# Or traditional method
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with required values (see Required Configuration below)

# Activate virtual environment (if using PDM)
source .venv/bin/activate
```

### Running the Application

```bash
# Run both TG Bot + Web Server (recommended)
python3 src/main.py

# Run only TG Bot
ENABLE_WEB=false python3 src/main.py

# Run only Web Server
python3 src/web/app.py
# or
uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Test unified deployment configuration
python3 test_unified.py

# Test web server (after starting main.py in another terminal)
python3 test_unified.py --test-web

# Manual yt-dlp test
python3 src/test.py  # Downloads a hardcoded YouTube URL
```

### Docker

```bash
# Run with docker-compose (includes Redis + MySQL)
docker-compose up -d

# View logs
docker-compose logs -f ytdl

# Run standalone (requires external Redis/DB)
docker run --env-file .env bennythink/ytdlbot
```

## Required Configuration

**Must-have environment variables**:
- `APP_ID`, `APP_HASH`, `BOT_TOKEN` - Telegram bot credentials
- `OWNER` - Owner user ID(s), comma-separated
- `DB_DSN` - Database connection (e.g., `sqlite:///db.sqlite` or `mysql+pymysql://user:pass@host/db`)
- `REDIS_HOST` - Redis hostname

**Important optional variables**:
- `ENABLE_WEB` - Enable web server (default: `true`)
- `WEB_PORT` - Web server port (default: `8000`)
- `AUTHORIZED_USER` - Comma-separated user IDs for access control
- `POTOKEN` - YouTube PO Token (see [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide))
- `BROWSERS` - Browser for cookie extraction (e.g., `firefox`)
- `TMPFILE_PATH` - Temporary file directory (default: `/tmp`)

## Critical Development Notes

### YouTube Download Requirements

- **JS Runtime**: Users should install a JS runtime (deno, node) for yt-dlp to handle YouTube properly
- **Cookies/Tokens**: YouTube downloads may require:
  - `youtube-cookies.txt` file in project root
  - Browser cookies via `BROWSERS` env var
  - PO Token via `POTOKEN` env var

### Download Flow

1. **TG Bot**: User sends URL → Handler in `main.py` → Engine entrance function → `BaseDownloader` subclass → Download via yt-dlp → Upload to Telegram → Cache result
2. **Web API**: POST to `/api/download` → Create task → Background async download via `WebDownloader` → Progress via WebSocket → File available at `/api/file/{task_id}`

### Format Selection Architecture

- **TG Bot**: `YoutubeDownload.get_available_formats()` extracts formats → Creates inline keyboard → User callback triggers `resolution_selection_callback()` → Downloads with `_start(user_format_id, user_height)`
- **Web**: `WebDownloader.get_video_info()` returns formats → Frontend shows options → POST with `format_id`/`height` → Downloads with specified format

### Cache Mechanism

- Cache key: MD5 hash of `url + quality + format`
- Stored in Redis with fields: `file_id` (Telegram file ID), `meta` (video metadata)
- Shared between TG bot downloads only (Web downloads don't use cache)

### Progress Reporting

- **TG Bot**: `BaseDownloader.download_hook()` → `edit_text()` with debouncing (max every 5 seconds)
- **Web**: `WebDownloader._progress_hook()` → Callback → Queue → WebSocket push

## File Structure Context

- `src/main.py` - Telegram bot handlers and unified startup
- `src/web/` - FastAPI web application (separate download engine)
- `src/engine/` - Download engine implementations (shared TG bot logic)
- `src/database/` - Database models and Redis cache
- `src/config/` - Configuration and internationalization
- `src/utils/` - Utility functions (file size formatting, URL extraction, etc.)
- `index.html` - Web interface UI (project root)
- `UNIFIED_DEPLOYMENT.md` - Detailed deployment guide
- `test_unified.py` - Deployment verification script

## Special Commands in TG Bot

- `/spdl <url>` - Use special downloader (Instagram, Pixeldrain, KrakenFiles)
- `/direct <url>` - Force aria2/requests download engine instead of yt-dlp
- `/ytdl <url>` - Explicit YouTube download in groups
- `/settings` - User preferences (format: video/audio/document, quality: high/medium/low, language: en/zh)

## Quota System

- Free daily quota per user (default: 3, configurable via `FREE_DOWNLOAD`)
- Paid quota via Stripe integration (requires `PROVIDER_TOKEN` and `ENABLE_VIP=true`)
- Tracked in database `User` model
- Reset daily via APScheduler job at midnight

## Multi-language Support

- Two languages: English (`en`) and Chinese (`zh`)
- All UI strings in `src/config/i18n.py` as `BotText` dataclass
- User preference stored in database, switchable via `/settings`
- Helper functions: `get_text(key, lang)`, `translate_setting()`, `get_language_name()`
