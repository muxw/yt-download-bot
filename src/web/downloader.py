#!/usr/bin/env python3
# coding: utf-8

"""
Web video downloader - standalone downloader for web interface
"""

import logging
import os
import re
import tempfile
import uuid
from pathlib import Path
from typing import Callable

import yt_dlp


def is_youtube(url: str) -> bool:
    """Check if URL is a YouTube URL"""
    from urllib.parse import urlparse
    try:
        if not url or not isinstance(url, str):
            return False
        parsed = urlparse(url)
        return parsed.netloc.lower() in {'youtube.com', 'www.youtube.com', 'youtu.be'}
    except Exception:
        return False


def sizeof_fmt(num: int, suffix="B") -> str:
    """Format bytes to human readable string"""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


class DownloadTask:
    """Represents a download task with its state"""

    def __init__(self, task_id: str, url: str):
        self.task_id = task_id
        self.url = url
        self.status = "pending"  # pending, downloading, completed, error
        self.progress = 0
        self.speed = ""
        self.eta = ""
        self.filename = ""
        self.filepath = ""
        self.error = ""
        self.title = ""
        self.filesize = 0


class WebDownloader:
    """Standalone video downloader for web interface"""

    # Store active tasks
    tasks: dict[str, DownloadTask] = {}

    # Max file size (2GB)
    MAX_FILE_SIZE = 2000 * 1024 * 1024

    def __init__(self, url: str):
        self.url = url
        self._tempdir = tempfile.mkdtemp(prefix="ytdl-web-")
        self._progress_callback: Callable | None = None

    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates"""
        self._progress_callback = callback

    def _get_ydl_opts(self) -> dict:
        """Get yt-dlp options with cookie/token config for YouTube"""
        opts = {
            "quiet": True,
            "no_warnings": True,
        }

        if is_youtube(self.url):
            # Browser cookies
            if browsers := os.getenv("BROWSERS"):
                opts["cookiesfrombrowser"] = browsers.split(",")

            # Cookie file
            cookie_file = "youtube-cookies.txt"
            if os.path.isfile(cookie_file) and os.path.getsize(cookie_file) > 100:
                opts["cookiefile"] = cookie_file

            # PO Token
            if potoken := os.getenv("POTOKEN"):
                opts["extractor_args"] = {
                    "youtube": ["player-client=web,default", f"po_token=web+{potoken}"]
                }

        return opts

    def get_video_info(self) -> dict:
        """Get video information and available formats"""
        ydl_opts = self._get_ydl_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.url, download=False)

        duration = info.get("duration", 0)

        # Filter and organize formats
        formats = []
        for f in info.get("formats", []):
            height = f.get("height")
            vcodec = f.get("vcodec", "none")

            # Only keep formats with video
            if height and vcodec != "none":
                filesize = f.get("filesize") or f.get("filesize_approx", 0)

                # Estimate filesize if not available
                if not filesize and duration:
                    tbr = f.get("tbr", 0)
                    if tbr:
                        filesize = int(tbr * 1000 / 8 * duration)

                formats.append({
                    "format_id": f["format_id"],
                    "height": height,
                    "ext": f.get("ext", "mp4"),
                    "filesize": filesize,
                    "filesize_str": sizeof_fmt(filesize) if filesize else "Unknown",
                    "vcodec": vcodec,
                })

        # Deduplicate by height, keep best quality for each resolution
        seen = set()
        unique_formats = []
        for f in sorted(formats, key=lambda x: (x["height"], x["filesize"] or 0), reverse=True):
            if f["height"] not in seen:
                seen.add(f["height"])
                unique_formats.append(f)

        return {
            "title": info.get("title", "Unknown"),
            "duration": duration,
            "thumbnail": info.get("thumbnail", ""),
            "uploader": info.get("uploader", ""),
            "formats": unique_formats[:6],  # Max 6 options
        }

    def _progress_hook(self, d: dict):
        """Handle download progress"""
        if d["status"] == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)

            if total > self.MAX_FILE_SIZE:
                raise Exception(f"File size {sizeof_fmt(total)} exceeds limit")

            progress = int(downloaded / total * 100) if total else 0
            speed = self._remove_bash_color(d.get("_speed_str", "N/A"))
            eta = self._remove_bash_color(d.get("_eta_str", ""))

            if self._progress_callback:
                self._progress_callback({
                    "status": "downloading",
                    "progress": progress,
                    "speed": speed,
                    "eta": eta,
                    "downloaded": sizeof_fmt(downloaded),
                    "total": sizeof_fmt(total) if total else "Unknown",
                })

        elif d["status"] == "finished":
            if self._progress_callback:
                self._progress_callback({
                    "status": "processing",
                    "progress": 100,
                    "message": "Processing video...",
                })

    @staticmethod
    def _remove_bash_color(text: str) -> str:
        """Remove ANSI color codes from string"""
        return re.sub(r"\u001b|\[0;94m|\u001b\[0m|\[0;32m|\[0m|\[0;33m", "", str(text))

    def download(self, format_id: str = None, height: int = None) -> str:
        """
        Download video and return filepath

        Args:
            format_id: Specific format ID to download, or None for best quality
            height: Video height limit (e.g., 720 for 720p)

        Returns:
            Path to downloaded file
        """
        import logging
        logger = logging.getLogger(__name__)

        output = Path(self._tempdir, "%(title).70s.%(ext)s").as_posix()

        ydl_opts = self._get_ydl_opts()
        ydl_opts.update({
            "progress_hooks": [self._progress_hook],
            "outtmpl": output,
            "restrictfilenames": False,
            "quiet": True,
            "concurrent_fragments": 16,
            "buffersize": 4194304,
            "retries": 6,
            "fragment_retries": 6,
            "skip_unavailable_fragments": True,
            "embed_metadata": True,
        })

        # Set format - 使用 <=? 可选过滤器
        # 参考: https://github.com/yt-dlp/yt-dlp#format-selection
        if height:
            # <=? 是可选过滤器，如果没有匹配格式不会失败
            format_list = [
                f"bestvideo[height<=?{height}]+bestaudio/best[height<=?{height}]"
            ]
            logger.info(f"Downloading with height limit: {height}p")
        elif format_id:
            format_list = [f"{format_id}+bestaudio", format_id]
            logger.info(f"Downloading with format_id: {format_id}")
        else:
            format_list = [
                "bestvideo[ext=mp4][vcodec!*=av01][vcodec!*=vp09]+bestaudio[ext=m4a]",
                "bestvideo+bestaudio",
                "best",
            ]
            logger.info("Downloading with default best quality")

        # Google Drive special handling
        if self.url.startswith("https://drive.google.com"):
            format_list = ["source"] + format_list

        # Try each format until one succeeds
        last_error = None
        for fmt in format_list:
            ydl_opts["format"] = fmt
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.url])
                files = list(Path(self._tempdir).glob("*"))
                if files:
                    return str(files[0])
            except Exception as e:
                logger.warning(f"Format {fmt} failed: {e}, trying next...")
                last_error = e
                continue

        if last_error:
            raise last_error
        raise Exception("Download failed: no file found")

    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        try:
            shutil.rmtree(self._tempdir, ignore_errors=True)
        except Exception:
            pass

    @classmethod
    def create_task(cls, url: str) -> DownloadTask:
        """Create a new download task"""
        task_id = uuid.uuid4().hex[:12]
        task = DownloadTask(task_id, url)
        cls.tasks[task_id] = task
        return task

    @classmethod
    def get_task(cls, task_id: str) -> DownloadTask | None:
        """Get task by ID"""
        return cls.tasks.get(task_id)

    @classmethod
    def remove_task(cls, task_id: str):
        """Remove task from memory"""
        cls.tasks.pop(task_id, None)
