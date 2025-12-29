#!/usr/local/bin/python3
# coding: utf-8

# ytdlbot - i18n.py
# Internationalization support for multiple languages

__author__ = "Benny <benny.think@gmail.com>"

TEXTS = {
    "en": {
        # Start and Help messages
        "start": """
Welcome to YouTube Download bot. Type /help for more information.
EU: @benny_2ytdlbot
SG: @benny_ytdlbot

Join https://t.me/ytdlbot0 for updates.

""",
        "help": """
1. For YouTube and any websites supported by yt-dlp, just send the link and we will download and send it to you.

2. For specific links use `/spdl {URL}`. More info at https://github.com/tgbot-collection/ytdlbot#supported-websites

3. If the bot doesn't work, try again or join https://t.me/ytdlbot0 for updates.

4. Want to deploy it yourself?
Here's the source code: https://github.com/tgbot-collection/ytdlbot
""",
        "about": "YouTube Downloader by @BennyThink.\n\nOpen source on GitHub: https://github.com/tgbot-collection/ytdlbot",
        "settings": """
Please choose the preferred format and video quality for your video. These settings only **apply to YouTube videos**.
High: 1080P
Medium: 720P
Low: 480P

If you choose to send the video as a document, Telegram client will not be able stream it.

Your current settings:
Video quality: {}
Sending type: {}
Language: {}
""",
        # Status messages
        "task_received": "Task received.",
        "direct_download_received": "Direct download request received.",
        "spdl_received": "SPDL request received.",
        "group_download_received": "Group download request received.",
        "starting_ping": "Starting Ping...",
        "ping_complete": "Ping Calculation Complete.",
        "success": "Success",

        # Download messages
        "starting_download": "Starting download...",
        "download_failed": "Download failed!",
        "processing": "Processing...",
        "aria2_starting": "Aria2 download starting...",
        "processing_link": "Processing download link...",

        # Error messages
        "send_correct_link": "Send me a correct LINK.",
        "check_url": "Check your URL.",
        "something_wrong": "Something wrong.\nCheck your URL and send me again.",
        "something_went_wrong": "Something went wrong. Please contact the admin.",
        "private_only": "This bot is for authorized users only.",

        # Settings UI
        "send_as_document": "send as document",
        "send_as_video": "send as video",
        "send_as_audio": "send as audio",
        "high_quality": "High Quality",
        "medium_quality": "Medium Quality",
        "low_quality": "Low Quality",

        # Language
        "language": "Language",
        "language_set_to": "Your language was set to English",
        "choose_amount": "Please choose the amount you want to buy.",

        # Quota
        "quota_info": "You have {} free and {} paid quota.",

        # Callback answers
        "send_type_set": "Your send type was set to {}",
        "quality_set": "Your default quality was set to {}",

        # Resolution selection
        "analyzing_video": "Analyzing video formats...",
        "choose_resolution": "Please choose video quality:",
        "unknown_size": "Unknown",
        "format_expired": "Selection expired. Please send the link again.",
    },

    "zh": {
        # 开始和帮助消息
        "start": """
欢迎使用 YouTube 下载机器人。输入 /help 获取更多信息。
欧盟: @benny_2ytdlbot
新加坡: @benny_ytdlbot

加入 https://t.me/ytdlbot0 获取更新。

""",
        "help": """
1. 对于 YouTube 和其他 yt-dlp 支持的网站，直接发送链接即可下载。

2. 对于特定链接，使用 `/spdl {URL}`。更多信息请访问 https://github.com/tgbot-collection/ytdlbot#supported-websites

3. 如果机器人不工作，请重试或加入 https://t.me/ytdlbot0 获取更新。

4. 想要自己部署？
源代码在这里: https://github.com/tgbot-collection/ytdlbot
""",
        "about": "YouTube 下载器 by @BennyThink。\n\n开源地址: https://github.com/tgbot-collection/ytdlbot",
        "settings": """
请选择您偏好的视频格式和质量。这些设置仅**适用于 YouTube 视频**。
高: 1080P
中: 720P
低: 480P

如果您选择以文档形式发送，Telegram 客户端将无法在线播放。

您当前的设置:
视频质量: {}
发送类型: {}
语言: {}
""",
        # 状态消息
        "task_received": "任务已接收。",
        "direct_download_received": "直接下载请求已接收。",
        "spdl_received": "SPDL 请求已接收。",
        "group_download_received": "批量下载请求已接收。",
        "starting_ping": "正在测试延迟...",
        "ping_complete": "延迟测试完成。",
        "success": "成功",

        # 下载消息
        "starting_download": "开始下载...",
        "download_failed": "下载失败！",
        "processing": "处理中...",
        "aria2_starting": "Aria2 下载开始...",
        "processing_link": "正在处理下载链接...",

        # 错误消息
        "send_correct_link": "请发送正确的链接。",
        "check_url": "请检查您的链接。",
        "something_wrong": "出错了。\n请检查您的链接后重试。",
        "something_went_wrong": "出错了。请联系管理员。",
        "private_only": "此机器人仅供授权用户使用。",

        # 设置界面
        "send_as_document": "发送为文档",
        "send_as_video": "发送为视频",
        "send_as_audio": "发送为音频",
        "high_quality": "高质量",
        "medium_quality": "中等质量",
        "low_quality": "低质量",

        # 语言
        "language": "语言",
        "language_set_to": "您的语言已设置为中文",
        "choose_amount": "请选择您想购买的数量。",

        # 配额
        "quota_info": "您有 {} 次免费配额和 {} 次付费配额。",

        # 回调回复
        "send_type_set": "您的发送类型已设置为 ",
        "quality_set": "您的默认质量已设置为 {}",

        # 分辨率选择
        "analyzing_video": "正在解析视频格式...",
        "choose_resolution": "请选择视频质量：",
        "unknown_size": "未知",
        "format_expired": "选择已过期，请重新发送链接。",
    }
}

# Translation mapping for settings values
SETTINGS_TRANSLATION = {
    "en": {
        "high": "High",
        "medium": "Medium",
        "low": "Low",
        "audio": "Audio",
        "custom": "Custom",
        "video": "Video",
        "document": "Document",
    },
    "zh": {
        "high": "高",
        "medium": "中",
        "low": "低",
        "audio": "音频",
        "custom": "自定义",
        "video": "视频",
        "document": "文档",
    }
}

LANGUAGE_NAMES = {
    "en": "English",
    "zh": "中文"
}


def get_text(key: str, lang: str = "en") -> str:
    """Get localized text by key and language."""
    texts = TEXTS.get(lang, TEXTS["en"])
    return texts.get(key, TEXTS["en"].get(key, key))


def translate_setting(value: str, lang: str = "en") -> str:
    """Translate setting value to localized text."""
    translations = SETTINGS_TRANSLATION.get(lang, SETTINGS_TRANSLATION["en"])
    return translations.get(value, value)


def get_language_name(lang: str) -> str:
    """Get the display name for a language code."""
    return LANGUAGE_NAMES.get(lang, lang)
