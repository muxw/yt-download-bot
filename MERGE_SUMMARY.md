# Web + Telegram Bot 统一部署

## 更新摘要

现在Web应用和Telegram Bot已经合并到一起，可以在同一个进程中运行。

## 快速开始

### 1. 启动服务（Web + TG Bot）

```bash
python3 src/main.py
```

这将同时启动：
- Telegram Bot（主线程）
- Web服务器（后台线程，默认端口8000）

### 2. 访问Web界面

浏览器打开: `http://localhost:8000`

### 3. 使用Telegram Bot

在Telegram中搜索你的bot并开始使用

## 环境变量配置

在 `.env` 文件中配置：

```bash
# Telegram Bot（必需）
APP_ID=your_app_id
APP_HASH=your_app_hash
BOT_TOKEN=your_bot_token

# Web服务（可选）
ENABLE_WEB=true    # 是否启用Web，默认true
WEB_PORT=8000      # Web端口，默认8000
WEB_HOST=0.0.0.0   # Web监听地址，默认0.0.0.0
```

## 独立启动选项

### 仅启动Telegram Bot
```bash
ENABLE_WEB=false python3 src/main.py
```

### 仅启动Web服务
```bash
python3 src/web/app.py
```

## 测试部署

运行测试脚本检查配置：
```bash
python3 test_unified.py
```

测试Web服务器（在另一个终端运行main.py后）：
```bash
python3 test_unified.py --test-web
```

## 文件说明

- `src/main.py` - 统一入口，同时启动Web和TG Bot
- `src/web/app.py` - FastAPI Web应用
- `src/web/downloader.py` - Web下载引擎
- `src/web/bridge.py` - Web和TG引擎的桥接（预留，暂未使用）
- `UNIFIED_DEPLOYMENT.md` - 详细部署文档
- `test_unified.py` - 部署测试脚本

## 主要改动

1. **src/main.py**:
   - 新增 `start_web_server()` 函数
   - 在主函数中启动Web服务的守护线程
   - 添加 `ENABLE_WEB` 环境变量控制

2. **src/web/app.py**:
   - 修正静态文件路径查找逻辑
   - 支持从多个位置加载 index.html

3. **新增文件**:
   - `UNIFIED_DEPLOYMENT.md` - 完整部署指南
   - `test_unified.py` - 自动化测试脚本
   - `src/web/bridge.py` - 桥接模块（预留）

## 架构

```
主进程 (main.py)
├─ Telegram Bot (主线程，阻塞)
│  └─ BaseDownloader (TG下载引擎)
└─ FastAPI Web (守护线程，后台)
   └─ WebDownloader (Web下载引擎)
```

两个服务共享：
- 数据库连接
- Redis缓存
- 环境配置
- yt-dlp核心

## 优势

✅ 简化部署 - 一条命令启动所有服务
✅ 资源共享 - 共享配置、数据库、缓存
✅ 灵活控制 - 可独立启用/禁用Web或Bot
✅ 向下兼容 - 现有功能不受影响

## 下一步

未来可以考虑：
- [ ] Web添加用户认证和配额系统
- [ ] 统一Web和TG的下载引擎
- [ ] 添加任务队列系统
- [ ] 支持集群部署

## 详细文档

查看 `UNIFIED_DEPLOYMENT.md` 获取更多信息。
