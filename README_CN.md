# ytdlbot

**[English](README.md)** | **[中文](README_CN.md)**

> **这是 [tgbot-collection/ytdlbot](https://github.com/tgbot-collection/ytdlbot) 的 Fork 版本，添加了额外功能。**

[![docker image](https://github.com/tgbot-collection/ytdlbot/actions/workflows/builder.yaml/badge.svg)](https://github.com/tgbot-collection/ytdlbot/actions/workflows/builder.yaml)

**YouTube 视频下载机器人🚀🎬⬇️**

这个 Telegram 机器人可以帮你下载 YouTube 和[其他支持网站](#支持的网站)的视频。

## Fork 版本新增功能

### 🌍 多语言支持（中文/English）
- 用户可以在 `/settings` 中切换中文和英文
- 所有机器人消息都支持双语

### 🎬 分辨率选择
- 发送视频链接时，机器人会分析可用的分辨率
- 显示分辨率选项和预估文件大小
- 用户可以在下载前选择想要的画质

### 🔗 自动提取链接
- 自动从包含其他文字的消息中提取链接
- 支持转发的包含链接的消息
- 示例："请帮我下载这个视频 https://youtube.com/xxx 谢谢" → 自动提取链接

---

# 使用方法

* 欧洲🇪🇺: [https://t.me/benny_2ytdlbot](https://t.me/benny_2ytdlbot)
* 新加坡🇸🇬: [https://t.me/benny_ytdlbot](https://t.me/benny_ytdlbot)

* 加入 Telegram 频道获取更新：https://t.me/ytdlbot0

直接发送链接给机器人即可。

# 支持的网站

* YouTube
* 所有 [yt-dlp 支持的网站](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

  ### 特定链接下载器（使用 /spdl 命令下载这些链接）
    * Instagram（视频、图片、Reels、IGTV 和轮播图）
    * Pixeldrain
    * KrakenFiles

# 功能特点

1. 快速下载和上传
2. 无广告
3. 下载和上传进度条
4. 画质选择
5. 上传格式：文件、视频、音频
6. 缓存机制 - 相同视频只需下载一次
7. 支持多种下载引擎（yt-dlp、aria2、requests）

> ## 限制
> 由于服务器和带宽的限制，免费服务有一些限制：
> * 每个用户每天限制 1 次免费下载

# 截图

## 普通下载

![](assets/1.jpeg)

## Instagram 下载

![](assets/instagram.png)

![](assets/2.jpeg)

# 如何部署？

这个机器人可以部署在任何支持 Python 的平台上。

## 在本地机器上运行

> 项目使用 PDM 管理依赖。

1. <details>
    <summary>安装 PDM</summary>

    可以使用 pip 安装：`pip install --user pdm`
    或查看详细说明：[官方文档](https://pdm-project.org/en/latest/#installation)

   </details>

2. 使用 PDM 安装模块：`pdm install`，或者用传统方式 `pip install -r requirements.txt`

> [!IMPORTANT]
> 所有想要从 YouTube 下载的用户，强烈建议安装 yt-dlp 支持的 JS 运行时（如 deno）。

3. <details>
    <summary>设置配置文件</summary>

    ```
    cp .env.example .env
    ```

    填写 `.env` 中的字段。更多信息请参阅 `.env.example` 文件中的注释。

    **- 必填字段**
    - `WORKERS`: Worker 数量（默认 100）
    - `APP_ID`: Telegram App ID
    - `APP_HASH`: Telegram App Hash
    - `BOT_TOKEN`: 你的 Telegram 机器人 Token
    - `OWNER`: 所有者 ID（多个用 `,` 分隔）
    - `AUTHORIZED_USER`: 授权用户 ID 列表（多个用 `,` 分隔）
    - `DB_DSN`: 数据库 URL（mysql+pymysql://user:pass@mysql/dbname）或 SQLite（sqlite:///db.sqlite）
    - `REDIS_HOST`: Redis 主机

    **- 可选字段**
    - `ENABLE_FFMPEG`: 启用 FFMPEG 视频处理（True/False）
    - `AUDIO_FORMAT`: 期望的音频格式（如：mp3、wav）
    - `ENABLE_ARIA2`: 启用 Aria2 下载（True/False）
    - `RCLONE_PATH`: Rclone 可执行文件路径
    - `ENABLE_VIP`: 启用 VIP 功能（True/False）
    - `PROVIDER_TOKEN`: Stripe 支付提供商 Token
    - `FREE_DOWNLOAD`: 每个用户允许的免费下载次数
    - `RATE_LIMIT`: 请求速率限制
    - `TMPFILE_PATH`: 临时/下载文件路径（确保目录存在且可写）
    - `TG_NORMAL_MAX_SIZE`: Telegram 上传最大大小（MB）
    - `CAPTION_URL_LENGTH_LIMIT`: 标题中 URL 最大长度
    - `POTOKEN`: 你的 PO Token。[PO-Token-指南](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)
    - `BROWSERS`: 用于处理"浏览器 cookies"的浏览器，如 firefox
  </details>

4. 激活 PDM 创建的虚拟环境：`source .venv/bin/activate`

5. 最后运行机器人：`python src/main.py`

## Docker

一行命令运行机器人：

```shell
docker run --env-file .env bennythink/ytdlbot
```

# 命令

```
start - 开始使用
about - 关于这个机器人
help - 帮助
spdl - 用于下载特定链接下载器支持的链接
direct - 使用 aria2/requests 引擎下载
ytdl - 在群组中下载视频
settings - 设置偏好
unsub - 取消订阅 YouTube 频道
ping - Ping 机器人
stats - 服务器和机器人统计
buy - 购买配额
```

# 测试数据

<details><summary>点击展开</summary>

## 测试视频

https://www.youtube.com/watch?v=V3RtA-1b_2E

## 测试播放列表

https://www.youtube.com/playlist?list=PL1Hdq7xjQCJxQnGc05gS4wzHWccvEJy0w

## 测试 Twitter

https://twitter.com/nitori_sayaka/status/1526199729864200192
https://twitter.com/BennyThinks/status/1475836588542341124

## 测试 Instagram

* 单张图片：https://www.instagram.com/p/CXpxSyOrWCA/
* 单个视频：https://www.instagram.com/p/Cah_7gnDVUW/
* Reels：https://www.instagram.com/p/C0ozGsjtY0W/
* 图片轮播：https://www.instagram.com/p/C0ozPQ5o536/
* 视频和图片轮播：https://www.instagram.com/p/C0ozhsVo-m8/

## 测试 Pixeldrain

https://pixeldrain.com/u/765ijw9i

## 测试 KrakenFiles

https://krakenfiles.com/view/oqmSTF0T5t/file.html

</details>

# 许可证

Apache License 2.0
