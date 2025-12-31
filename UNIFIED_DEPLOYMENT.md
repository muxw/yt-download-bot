# 统一部署指南 - Web + Telegram Bot

本项目现在支持在一个进程中同时运行Web应用和Telegram Bot。

## 功能特性

- ✅ 一个进程同时运行Web服务和Telegram Bot
- ✅ Web和TG Bot各自独立的下载引擎
- ✅ 通过环境变量灵活控制
- ✅ 简化部署和资源管理

## 快速开始

### 1. 环境变量配置

创建或编辑 `.env` 文件，添加以下配置：

```bash
# Telegram Bot 配置（必需）
APP_ID=your_app_id
APP_HASH=your_app_hash
BOT_TOKEN=your_bot_token

# Web 服务配置（可选）
ENABLE_WEB=true          # 是否启用Web服务，默认: true
WEB_HOST=0.0.0.0         # Web服务监听地址，默认: 0.0.0.0
WEB_PORT=8000            # Web服务端口，默认: 8000

# 其他配置
TMPFILE_PATH=/tmp        # 临时文件目录
```

### 2. 启动方式

#### 方式一：同时启动 Web + TG Bot（推荐）

```bash
python src/main.py
```

这将会：
- 在后台线程启动 FastAPI Web 服务（默认端口 8000）
- 在主线程运行 Telegram Bot

#### 方式二：仅启动 Telegram Bot

```bash
ENABLE_WEB=false python src/main.py
```

#### 方式三：仅启动 Web 服务

```bash
python src/web/app.py
# 或
uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```

### 3. 访问服务

启动后，你可以通过以下方式访问：

- **Web界面**: `http://localhost:8000`
- **Web API文档**: `http://localhost:8000/docs`
- **Telegram Bot**: 在Telegram中搜索你的bot

## Web API 端点

### 获取视频信息
```bash
POST /api/info
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=xxx"
}
```

### 开始下载
```bash
POST /api/download
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=xxx",
  "format_id": "137",  # 可选
  "height": 720        # 可选
}
```

### 查询下载状态
```bash
GET /api/download/{task_id}
```

### 下载文件
```bash
GET /api/file/{task_id}
```

### WebSocket 实时进度
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{task_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.progress, data.status);
};
```

## Docker 部署

### 使用 Docker Compose

编辑 `docker-compose.yml`，确保包含Web端口映射：

```yaml
services:
  ytdlbot:
    build: .
    environment:
      - ENABLE_WEB=true
      - WEB_PORT=8000
    ports:
      - "8000:8000"  # Web服务端口
    volumes:
      - ./:/app
```

启动：
```bash
docker-compose up -d
```

## 架构说明

### 当前架构

```
┌─────────────────────────────────────┐
│         main.py (主进程)             │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ Pyrogram Bot │  │ FastAPI Web │ │
│  │  (主线程)     │  │  (守护线程)  │ │
│  └──────────────┘  └─────────────┘ │
│         │                 │         │
│         ▼                 ▼         │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ BaseDownloader│ │WebDownloader│ │
│  │  (TG引擎)     │  │  (Web引擎)  │ │
│  └──────────────┘  └─────────────┘ │
│         │                 │         │
│         └────────┬────────┘         │
│                  ▼                  │
│         ┌────────────────┐          │
│         │   yt-dlp核心    │          │
│         └────────────────┘          │
└─────────────────────────────────────┘
```

### 关键组件

1. **main.py**: 统一入口
   - 启动 Telegram Bot（主线程，阻塞）
   - 启动 Web 服务器（守护线程，后台运行）
   - 管理调度器和定时任务

2. **TG Bot 下载引擎**:
   - `BaseDownloader`: 基类
   - `YoutubeDownload`: YouTube下载
   - `DirectDownload`: 直接下载
   - 支持配额系统、缓存、用户设置

3. **Web 下载引擎**:
   - `WebDownloader`: 独立的下载器
   - 支持格式选择、进度回调
   - WebSocket 实时进度推送

## 优势

1. **简化部署**: 一条命令启动所有服务
2. **资源共享**: 共享数据库、Redis缓存、配置
3. **灵活配置**: 可以单独启用或禁用Web/TG功能
4. **独立维护**: Web和TG各自的下载逻辑相互独立

## 故障排查

### Web服务无法访问

1. 检查端口是否被占用：
```bash
lsof -i :8000
```

2. 检查环境变量：
```bash
echo $ENABLE_WEB
echo $WEB_PORT
```

3. 查看日志：
```bash
# 日志中应该看到：
# Starting web server on 0.0.0.0:8000
# Web server started in background thread
```

### Telegram Bot 无法工作

1. 检查必需的环境变量：
```bash
echo $BOT_TOKEN
echo $APP_ID
echo $APP_HASH
```

2. 查看错误信息：
```bash
python src/main.py 2>&1 | grep -i error
```

## 下一步计划

未来可以考虑的改进：

- [ ] 让Web应用使用TG Bot的配额系统
- [ ] Web界面添加用户认证
- [ ] 统一Web和TG的下载引擎为一个共享模块
- [ ] 添加下载任务队列管理
- [ ] 支持分布式部署（多实例）

## 贡献

欢迎提交Issue和Pull Request！
