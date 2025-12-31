#!/usr/bin/env python3
# coding: utf-8

"""
Bridge between web API and Telegram bot download engine
Allows web interface to use the same download engine as Telegram bot
"""

import logging
from typing import Callable, Any
from types import SimpleNamespace
from pathlib import Path


class MockMessage:
    """Mock Pyrogram Message object for web downloads"""

    def __init__(self, message_id: int, chat_id: int):
        self.id = message_id
        self.chat = SimpleNamespace(id=chat_id, type=SimpleNamespace(name="PRIVATE"))
        self.from_user = SimpleNamespace(id=chat_id)
        self.reply_to_message = None
        self._text = ""
        self._edit_callback = None

    def edit_text(self, text: str):
        """Called by BaseDownloader to update progress"""
        self._text = text
        if self._edit_callback:
            self._edit_callback(text)

    def delete(self):
        """Mock delete method"""
        pass

    def reply_text(self, text: str, quote=False):
        """Mock reply method"""
        pass

    def set_edit_callback(self, callback: Callable):
        """Set callback for when message is edited (for progress updates)"""
        self._edit_callback = callback


class MockClient:
    """Mock Pyrogram Client for web downloads"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_chat_action(self, chat_id: int, action):
        """Mock send_chat_action - no-op for web"""
        pass

    def send_document(self, **kwargs):
        """Mock send_document - returns file info"""
        file_path = kwargs.get('document')
        return self._create_mock_sent_message(file_path)

    def send_video(self, **kwargs):
        """Mock send_video - returns file info"""
        file_path = kwargs.get('video')
        return self._create_mock_sent_message(file_path)

    def send_audio(self, **kwargs):
        """Mock send_audio - returns file info"""
        file_path = kwargs.get('audio')
        return self._create_mock_sent_message(file_path)

    def send_animation(self, **kwargs):
        """Mock send_animation - returns file info"""
        file_path = kwargs.get('animation')
        return self._create_mock_sent_message(file_path)

    def send_photo(self, **kwargs):
        """Mock send_photo - returns file info"""
        file_path = kwargs.get('photo')
        return self._create_mock_sent_message(file_path)

    def send_media_group(self, chat_id, media_list):
        """Mock send_media_group - returns list of file info"""
        files = [m.media for m in media_list]
        return [self._create_mock_sent_message(f) for f in files]

    def send_message(self, chat_id, text, **kwargs):
        """Mock send_message"""
        msg = MockMessage(999, chat_id)
        msg._text = text
        return msg

    @staticmethod
    def _create_mock_sent_message(file_path):
        """Create a mock sent message with file info"""
        return SimpleNamespace(
            document=SimpleNamespace(file_id=f"file_{Path(file_path).name}"),
            video=SimpleNamespace(file_id=f"file_{Path(file_path).name}"),
            audio=SimpleNamespace(file_id=f"file_{Path(file_path).name}"),
            animation=SimpleNamespace(file_id=f"file_{Path(file_path).name}"),
            photo=SimpleNamespace(file_id=f"file_{Path(file_path).name}"),
        )


class WebDownloadBridge:
    """
    Bridge that connects web API to Telegram bot download engine
    Converts web download requests to use TG bot's download functions
    """

    def __init__(self):
        self.mock_client = MockClient()
        self.logger = logging.getLogger(__name__)

    def download_with_engine(
        self,
        url: str,
        download_func: Callable,
        progress_callback: Callable[[str], None] = None,
        chat_id: int = 1,
        format_id: str = None,
        height: int = None,
    ) -> tuple[str, dict]:
        """
        Use TG bot's download engine to download for web

        Args:
            url: Video URL
            download_func: TG bot download function (youtube_entrance, direct_entrance, etc.)
            progress_callback: Callback for progress updates (receives text)
            chat_id: Fake chat ID for web user (default: 1)
            format_id: Optional format ID for YouTube downloads
            height: Optional height limit for YouTube downloads

        Returns:
            tuple: (file_path, metadata)
        """
        # Create mock message with progress callback
        mock_message = MockMessage(message_id=100, chat_id=chat_id)
        if progress_callback:
            mock_message.set_edit_callback(progress_callback)

        try:
            # For YoutubeDownload with specific format, we need special handling
            if format_id or height:
                from engine.generic import YoutubeDownload
                downloader = YoutubeDownload(self.mock_client, mock_message, url)
                # Temporarily override user settings for this download
                if format_id or height:
                    # Call the internal _start method with custom format
                    downloader._start(user_format_id=format_id, user_height=height)
                else:
                    downloader.start()
            else:
                # Use the standard entrance functions
                download_func(self.mock_client, mock_message, url)

            # Get the downloaded file from temp directory
            # The BaseDownloader stores files in self._tempdir
            # Since we can't directly access it, we'll need to modify this approach

            # For now, return None to indicate we need to refactor the approach
            self.logger.warning("Download completed but file path extraction needs implementation")
            return None, {}

        except Exception as e:
            self.logger.error(f"Download failed: {e}", exc_info=True)
            raise


# Global bridge instance
_bridge = None


def get_bridge() -> WebDownloadBridge:
    """Get or create global bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = WebDownloadBridge()
    return _bridge
