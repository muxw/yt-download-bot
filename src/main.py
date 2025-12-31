#!/usr/local/bin/python3
# coding: utf-8

# ytdlbot - new.py
# 8/14/21 14:37
#

__author__ = "Benny <benny.think@gmail.com>"

import logging
import os
import re
import threading
import time
import typing
from io import BytesIO
from typing import Any

import psutil
import pyrogram.errors
import yt_dlp
from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, enums, filters, types

from config import (
    APP_HASH,
    APP_ID,
    AUTHORIZED_USER,
    BOT_TOKEN,
    ENABLE_ARIA2,
    ENABLE_FFMPEG,
    M3U8_SUPPORT,
    ENABLE_VIP,
    OWNER,
    PROVIDER_TOKEN,
    TOKEN_PRICE,
    BotText,
    get_text,
    translate_setting,
    get_language_name,
)
from database.model import (
    credit_account,
    get_format_settings,
    get_free_quota,
    get_language_settings,
    get_paid_quota,
    get_quality_settings,
    init_user,
    reset_free,
    set_user_settings,
)
from engine import direct_entrance, youtube_entrance, special_download_entrance
from engine.generic import YoutubeDownload
from database import Redis
from utils import extract_url_and_name, sizeof_fmt, timeof_fmt

logging.info("Authorized users are %s", AUTHORIZED_USER)
logging.getLogger("apscheduler.executors.default").propagate = False


def create_app(name: str, workers: int = 64) -> Client:
    return Client(
        name,
        APP_ID,
        APP_HASH,
        bot_token=BOT_TOKEN,
        workers=workers,
        # max_concurrent_transmissions=max(1, WORKERS // 2),
        # https://github.com/pyrogram/pyrogram/issues/1225#issuecomment-1446595489
    )


app = create_app("main")


def private_use(func):
    def wrapper(client: Client, message: types.Message):
        chat_id = getattr(message.from_user, "id", None)

        # message type check
        if message.chat.type != enums.ChatType.PRIVATE and not getattr(message, "text", "").lower().startswith("/ytdl"):
            logging.debug("%s, it's annoying me...🙄️ ", message.text)
            return

        # authorized users check
        if AUTHORIZED_USER:
            users = [int(i) for i in AUTHORIZED_USER.split(",")]
        else:
            users = []

        if users and chat_id and chat_id not in users:
            lang = get_language_settings(chat_id) if chat_id else "en"
            message.reply_text(get_text("private_only", lang), quote=True)
            return

        return func(client, message)

    return wrapper


@app.on_message(filters.command(["start"]))
def start_handler(client: Client, message: types.Message):
    from_id = message.chat.id
    init_user(from_id)
    logging.info("%s welcome to youtube-dl bot!", message.from_user.id)
    client.send_chat_action(from_id, enums.ChatAction.TYPING)
    lang = get_language_settings(from_id)
    free, paid = get_free_quota(from_id), get_paid_quota(from_id)
    quota_text = get_text("quota_info", lang).format(free, paid)
    client.send_message(
        from_id,
        get_text("start", lang) + quota_text,
        disable_web_page_preview=True,
    )


@app.on_message(filters.command(["help"]))
def help_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    lang = get_language_settings(chat_id)
    client.send_message(chat_id, get_text("help", lang), disable_web_page_preview=True)


@app.on_message(filters.command(["about"]))
def about_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    lang = get_language_settings(chat_id)
    client.send_message(chat_id, get_text("about", lang))


@app.on_message(filters.command(["ping"]))
def ping_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    lang = get_language_settings(chat_id)

    def send_message_and_measure_ping():
        start_time = int(round(time.time() * 1000))
        reply: types.Message | typing.Any = client.send_message(chat_id, get_text("starting_ping", lang))

        end_time = int(round(time.time() * 1000))
        ping_time = int(round(end_time - start_time))
        message_sent = True
        if message_sent:
            message.reply_text(f"Ping: {ping_time:.2f} ms", quote=True)
        time.sleep(0.5)
        client.edit_message_text(chat_id=reply.chat.id, message_id=reply.id, text=get_text("ping_complete", lang))
        time.sleep(1)
        client.delete_messages(chat_id=reply.chat.id, message_ids=reply.id)

    thread = threading.Thread(target=send_message_and_measure_ping)
    thread.start()


@app.on_message(filters.command(["buy"]))
def buy(client: Client, message: types.Message):
    chat_id = message.chat.id
    lang = get_language_settings(chat_id)
    markup = types.InlineKeyboardMarkup(
        [
            [  # First row
                types.InlineKeyboardButton("10-$1", callback_data="buy-10-1"),
                types.InlineKeyboardButton("20-$2", callback_data="buy-20-2"),
                types.InlineKeyboardButton("40-$3.5", callback_data="buy-40-3.5"),
            ],
            [  # second row
                types.InlineKeyboardButton("50-$4", callback_data="buy-50-4"),
                types.InlineKeyboardButton("75-$6", callback_data="buy-75-6"),
                types.InlineKeyboardButton("100-$8", callback_data="buy-100-8"),
            ],
        ]
    )
    message.reply_text(get_text("choose_amount", lang), reply_markup=markup)


@app.on_callback_query(filters.regex(r"buy.*"))
def send_invoice(client: Client, callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    _, count, price = data.split("-")
    price = int(float(price) * 100)
    client.send_invoice(
        chat_id,
        f"{count} permanent download quota",
        "Please make a payment via Stripe",
        f"{count}",
        "USD",
        [types.LabeledPrice(label="VIP", amount=price)],
        provider_token=os.getenv("PROVIDER_TOKEN"),
        protect_content=True,
        start_parameter="no-forward-placeholder",
    )


@app.on_pre_checkout_query()
def pre_checkout(client: Client, query: types.PreCheckoutQuery):
    client.answer_pre_checkout_query(query.id, ok=True)


@app.on_message(filters.successful_payment)
def successful_payment(client: Client, message: types.Message):
    who = message.chat.id
    lang = get_language_settings(who)
    amount = message.successful_payment.total_amount  # in cents
    quota = int(message.successful_payment.invoice_payload)
    ch = message.successful_payment.provider_payment_charge_id
    free, paid = credit_account(who, amount, quota, ch)
    if paid > 0:
        message.reply_text(get_text("quota_info", lang).format(free, paid))
    else:
        message.reply_text(get_text("something_went_wrong", lang))
    message.delete()


@app.on_message(filters.command(["stats"]))
def stats_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    cpu_usage = psutil.cpu_percent()
    total, used, free, disk = psutil.disk_usage("/")
    swap = psutil.swap_memory()
    memory = psutil.virtual_memory()
    boot_time = psutil.boot_time()

    owner_stats = (
        "\n\n⌬─────「 Stats 」─────⌬\n\n"
        f"<b>╭🖥️ **CPU Usage »**</b>  __{cpu_usage}%__\n"
        f"<b>├💾 **RAM Usage »**</b>  __{memory.percent}%__\n"
        f"<b>╰🗃️ **DISK Usage »**</b>  __{disk}%__\n\n"
        f"<b>╭📤Upload:</b> {sizeof_fmt(psutil.net_io_counters().bytes_sent)}\n"
        f"<b>╰📥Download:</b> {sizeof_fmt(psutil.net_io_counters().bytes_recv)}\n\n\n"
        f"<b>Memory Total:</b> {sizeof_fmt(memory.total)}\n"
        f"<b>Memory Free:</b> {sizeof_fmt(memory.available)}\n"
        f"<b>Memory Used:</b> {sizeof_fmt(memory.used)}\n"
        f"<b>SWAP Total:</b> {sizeof_fmt(swap.total)} | <b>SWAP Usage:</b> {swap.percent}%\n\n"
        f"<b>Total Disk Space:</b> {sizeof_fmt(total)}\n"
        f"<b>Used:</b> {sizeof_fmt(used)} | <b>Free:</b> {sizeof_fmt(free)}\n\n"
        f"<b>Physical Cores:</b> {psutil.cpu_count(logical=False)}\n"
        f"<b>Total Cores:</b> {psutil.cpu_count(logical=True)}\n\n"
        f"<b>🤖Bot Uptime:</b> {timeof_fmt(time.time() - botStartTime)}\n"
        f"<b>⏲️OS Uptime:</b> {timeof_fmt(time.time() - boot_time)}\n"
    )

    user_stats = (
        "\n\n⌬─────「 Stats 」─────⌬\n\n"
        f"<b>╭🖥️ **CPU Usage »**</b>  __{cpu_usage}%__\n"
        f"<b>├💾 **RAM Usage »**</b>  __{memory.percent}%__\n"
        f"<b>╰🗃️ **DISK Usage »**</b>  __{disk}%__\n\n"
        f"<b>╭📤Upload:</b> {sizeof_fmt(psutil.net_io_counters().bytes_sent)}\n"
        f"<b>╰📥Download:</b> {sizeof_fmt(psutil.net_io_counters().bytes_recv)}\n\n\n"
        f"<b>Memory Total:</b> {sizeof_fmt(memory.total)}\n"
        f"<b>Memory Free:</b> {sizeof_fmt(memory.available)}\n"
        f"<b>Memory Used:</b> {sizeof_fmt(memory.used)}\n"
        f"<b>Total Disk Space:</b> {sizeof_fmt(total)}\n"
        f"<b>Used:</b> {sizeof_fmt(used)} | <b>Free:</b> {sizeof_fmt(free)}\n\n"
        f"<b>🤖Bot Uptime:</b> {timeof_fmt(time.time() - botStartTime)}\n"
    )

    if message.from_user.id in OWNER:
        message.reply_text(owner_stats, quote=True)
    else:
        message.reply_text(user_stats, quote=True)


@app.on_message(filters.command(["settings"]))
def settings_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    lang = get_language_settings(chat_id)
    markup = types.InlineKeyboardMarkup(
        [
            [  # First row - format
                types.InlineKeyboardButton(get_text("send_as_document", lang), callback_data="document"),
                types.InlineKeyboardButton(get_text("send_as_video", lang), callback_data="video"),
                types.InlineKeyboardButton(get_text("send_as_audio", lang), callback_data="audio"),
            ],
            [  # Second row - quality
                types.InlineKeyboardButton(get_text("high_quality", lang), callback_data="high"),
                types.InlineKeyboardButton(get_text("medium_quality", lang), callback_data="medium"),
                types.InlineKeyboardButton(get_text("low_quality", lang), callback_data="low"),
            ],
            [  # Third row - language
                types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
                types.InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
            ],
        ]
    )

    quality = get_quality_settings(chat_id)
    send_type = get_format_settings(chat_id)
    quality_display = translate_setting(quality, lang)
    format_display = translate_setting(send_type, lang)
    lang_display = get_language_name(lang)
    client.send_message(chat_id, get_text("settings", lang).format(quality_display, format_display, lang_display), reply_markup=markup)


@app.on_message(filters.command(["direct"]))
def direct_download(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    lang = get_language_settings(chat_id)
    message_text = message.text
    url, new_name = extract_url_and_name(message_text)
    logging.info("Direct download using aria2/requests start %s", url)
    if url is None or not re.findall(r"^https?://", url.lower()):
        message.reply_text(get_text("send_correct_link", lang), quote=True)
        return
    bot_msg = message.reply_text(get_text("direct_download_received", lang), quote=True)
    try:
        direct_entrance(client, bot_msg, url)
    except ValueError as e:
        message.reply_text(e.__str__(), quote=True)
        bot_msg.delete()
        return


@app.on_message(filters.command(["spdl"]))
def spdl_handler(client: Client, message: types.Message):
    chat_id = message.chat.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    lang = get_language_settings(chat_id)
    message_text = message.text
    url, new_name = extract_url_and_name(message_text)
    logging.info("spdl start %s", url)
    if url is None or not re.findall(r"^https?://", url.lower()):
        message.reply_text(get_text("something_wrong", lang), quote=True)
        return
    bot_msg = message.reply_text(get_text("spdl_received", lang), quote=True)
    try:
        special_download_entrance(client, bot_msg, url)
    except ValueError as e:
        message.reply_text(e.__str__(), quote=True)
        bot_msg.delete()
        return


@app.on_message(filters.command(["ytdl"]) & filters.group)
def ytdl_handler(client: Client, message: types.Message):
    # for group only
    chat_id = message.from_user.id
    init_user(chat_id)
    client.send_chat_action(message.chat.id, enums.ChatAction.TYPING)
    lang = get_language_settings(chat_id)
    message_text = message.text
    url, new_name = extract_url_and_name(message_text)
    logging.info("ytdl start %s", url)
    if url is None or not re.findall(r"^https?://", url.lower()):
        message.reply_text(get_text("check_url", lang), quote=True)
        return

    bot_msg = message.reply_text(get_text("group_download_received", lang), quote=True)
    try:
        youtube_entrance(client, bot_msg, url)
    except ValueError as e:
        message.reply_text(e.__str__(), quote=True)
        bot_msg.delete()
        return


def check_link(url: str):
    ytdl = yt_dlp.YoutubeDL()
    if re.findall(r"^https://www\.youtube\.com/channel/", url) or "list" in url:
        # TODO maybe using ytdl.extract_info
        raise ValueError("Playlist or channel download are not supported at this moment.")

    if not M3U8_SUPPORT and (re.findall(r"m3u8|\.m3u8|\.m3u$", url.lower())):
        return "m3u8 links are disabled."


@app.on_message(filters.incoming & filters.text)
@private_use
def download_handler(client: Client, message: types.Message):
    chat_id = message.from_user.id
    init_user(chat_id)
    client.send_chat_action(chat_id, enums.ChatAction.TYPING)
    lang = get_language_settings(chat_id)

    # 从消息文本中提取URL（支持消息中包含其他文字的情况）
    message_text = message.text
    extracted_url, _ = extract_url_and_name(message_text)

    # 也尝试从消息 entities 中提取URL（处理转发消息等情况）
    if not extracted_url and message.entities:
        for entity in message.entities:
            if entity.type.name == "URL":
                extracted_url = message_text[entity.offset:entity.offset + entity.length]
                break
            elif entity.type.name == "TEXT_LINK":
                extracted_url = entity.url
                break

    # 如果提取到URL就用提取的，否则用整个消息文本
    url = extracted_url if extracted_url else message_text
    logging.info("start %s (extracted from: %s)", url, message_text[:50] if len(message_text) > 50 else message_text)

    try:
        check_link(url)
        bot_msg: types.Message | Any = message.reply_text(get_text("analyzing_video", lang), quote=True)

        # 尝试获取可用格式
        try:
            downloader = YoutubeDownload(client, bot_msg, url)
            formats = downloader.get_available_formats()

            if formats and len(formats) > 1:
                # 存储URL以便回调时使用
                redis = Redis()
                redis.store_pending_download(chat_id, bot_msg.id, url)

                # 创建分辨率选择按钮
                buttons = []
                for f in formats:
                    size_str = sizeof_fmt(f["filesize"]) if f["filesize"] else get_text("unknown_size", lang)
                    # 显示: 分辨率 | 编码 | 格式 | 大小
                    vcodec = f.get("vcodec", "unknown")[:8]  # 限制编码名称长度
                    ext = f.get("ext", "mp4").upper()
                    label = f"{f['height']}p | {vcodec} | {ext} | {size_str}"
                    # callback_data 格式: fmt_{format_id}_{height}_{msg_id}
                    buttons.append(types.InlineKeyboardButton(
                        label,
                        callback_data=f"fmt_{f['format_id']}_{f['height']}_{bot_msg.id}"
                    ))

                # 每行2个按钮
                markup_rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
                bot_msg.edit_text(
                    get_text("choose_resolution", lang),
                    reply_markup=types.InlineKeyboardMarkup(markup_rows)
                )
                return
        except Exception as e:
            logging.warning("Failed to get formats, falling back to default: %s", e)

        # 无法获取格式或只有一个格式，使用默认下载
        bot_msg.edit_text(get_text("task_received", lang))
        client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)
        youtube_entrance(client, bot_msg, url)

    except pyrogram.errors.Flood as e:
        f = BytesIO()
        f.write(str(e).encode())
        f.write(b"Your job will be done soon. Just wait!")
        f.name = "Please wait.txt"
        message.reply_document(f, caption=f"Flood wait! Please wait {e} seconds...", quote=True)
        f.close()
        client.send_message(OWNER, f"Flood wait! {e} seconds....")
        time.sleep(e.value)
    except ValueError as e:
        message.reply_text(e.__str__(), quote=True)
    except Exception as e:
        logging.error("Download failed", exc_info=True)
        message.reply_text(f"❌ {get_text('download_failed', lang)}: {e}", quote=True)


@app.on_callback_query(filters.regex(r"document|video|audio"))
def format_callback(client: Client, callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    lang = get_language_settings(chat_id)
    logging.info("Setting %s file type to %s", chat_id, data)
    callback_query.answer(get_text("send_type_set", lang).format(translate_setting(data, lang)))
    set_user_settings(chat_id, "format", data)


@app.on_callback_query(filters.regex(r"high|medium|low"))
def quality_callback(client: Client, callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    lang = get_language_settings(chat_id)
    logging.info("Setting %s download quality to %s", chat_id, data)
    callback_query.answer(get_text("quality_set", lang).format(translate_setting(data, lang)))
    set_user_settings(chat_id, "quality", data)


@app.on_callback_query(filters.regex(r"lang_.*"))
def language_callback(client: Client, callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    new_lang = data.replace("lang_", "")
    logging.info("Setting %s language to %s", chat_id, new_lang)
    set_user_settings(chat_id, "language", new_lang)
    callback_query.answer(get_text("language_set_to", new_lang))
    # Update the settings message with the new language
    quality = get_quality_settings(chat_id)
    send_type = get_format_settings(chat_id)
    quality_display = translate_setting(quality, new_lang)
    format_display = translate_setting(send_type, new_lang)
    lang_display = get_language_name(new_lang)
    markup = types.InlineKeyboardMarkup(
        [
            [  # First row - format
                types.InlineKeyboardButton(get_text("send_as_document", new_lang), callback_data="document"),
                types.InlineKeyboardButton(get_text("send_as_video", new_lang), callback_data="video"),
                types.InlineKeyboardButton(get_text("send_as_audio", new_lang), callback_data="audio"),
            ],
            [  # Second row - quality
                types.InlineKeyboardButton(get_text("high_quality", new_lang), callback_data="high"),
                types.InlineKeyboardButton(get_text("medium_quality", new_lang), callback_data="medium"),
                types.InlineKeyboardButton(get_text("low_quality", new_lang), callback_data="low"),
            ],
            [  # Third row - language
                types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
                types.InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
            ],
        ]
    )
    callback_query.message.edit_text(
        get_text("settings", new_lang).format(quality_display, format_display, lang_display),
        reply_markup=markup
    )


@app.on_callback_query(filters.regex(r"fmt_.*"))
def resolution_selection_callback(client: Client, callback_query: types.CallbackQuery):
    """处理用户选择的分辨率"""
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    lang = get_language_settings(chat_id)

    # 解析 callback_data: fmt_{format_id}_{height}_{msg_id}
    # format_id 可能包含下划线，height 和 msg_id 是数字
    parts = data.split("_")
    if len(parts) < 4:
        callback_query.answer("Invalid selection")
        return

    msg_id = int(parts[-1])  # 最后一个是 msg_id
    height = int(parts[-2])  # 倒数第二个是 height
    format_id = "_".join(parts[1:-2])  # 中间所有部分是 format_id
    logging.info(f"User selected format_id: {format_id}, height: {height}p for msg_id: {msg_id}")

    # 从 Redis 获取存储的 URL
    redis = Redis()
    url = redis.get_pending_download(chat_id, msg_id)

    if not url:
        callback_query.answer(get_text("format_expired", lang))
        callback_query.message.edit_text(get_text("format_expired", lang))
        return

    # 删除待处理记录
    redis.delete_pending_download(chat_id, msg_id)

    # 更新消息并开始下载
    callback_query.answer(get_text("starting_download", lang))
    bot_msg = callback_query.message
    bot_msg.edit_text(get_text("task_received", lang))

    try:
        client.send_chat_action(chat_id, enums.ChatAction.UPLOAD_VIDEO)
        # 使用用户选择的格式下载（优先使用 height 限制）
        downloader = YoutubeDownload(client, bot_msg, url)
        downloader._start(user_format_id=format_id, user_height=height)
    except Exception as e:
        logging.error("Download failed", exc_info=True)
        bot_msg.edit_text(f"❌ {get_text('download_failed', lang)}: {e}")


def start_web_server():
    """Start FastAPI web server in a separate thread"""
    import uvicorn
    from web.app import app as fastapi_app

    # Get port from environment or use default
    port = int(os.getenv("WEB_PORT", "8000"))
    host = os.getenv("WEB_HOST", "0.0.0.0")

    logging.info(f"Starting web server on {host}:{port}")
    uvicorn.run(fastapi_app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    botStartTime = time.time()
    scheduler = BackgroundScheduler()
    scheduler.add_job(reset_free, "cron", hour=0, minute=0)
    scheduler.start()
    banner = f"""
▌ ▌         ▀▛▘     ▌       ▛▀▖              ▜            ▌
▝▞  ▞▀▖ ▌ ▌  ▌  ▌ ▌ ▛▀▖ ▞▀▖ ▌ ▌ ▞▀▖ ▌  ▌ ▛▀▖ ▐  ▞▀▖ ▝▀▖ ▞▀▌
 ▌  ▌ ▌ ▌ ▌  ▌  ▌ ▌ ▌ ▌ ▛▀  ▌ ▌ ▌ ▌ ▐▐▐  ▌ ▌ ▐  ▌ ▌ ▞▀▌ ▌ ▌
 ▘  ▝▀  ▝▀▘  ▘  ▝▀▘ ▀▀  ▝▀▘ ▀▀  ▝▀   ▘▘  ▘ ▘  ▘ ▝▀  ▝▀▘ ▝▀▘

By @BennyThink, VIP Mode: {ENABLE_VIP}
Web Server: http://0.0.0.0:{os.getenv("WEB_PORT", "8000")}
    """
    print(banner)

    # Check if web server should be enabled
    enable_web = os.getenv("ENABLE_WEB", "true").lower() in ("true", "1", "yes")

    if enable_web:
        # Start web server in a separate thread
        web_thread = threading.Thread(target=start_web_server, daemon=True)
        web_thread.start()
        logging.info("Web server started in background thread")

    # Run Telegram bot (blocking)
    app.run()
