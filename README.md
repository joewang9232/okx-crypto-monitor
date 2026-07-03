# OKX 加密货币异动监控器

实时监控OKX交易所U本位永续合约的5分钟涨跌幅，发现异常波动时通过Telegram推送。

## 功能

- **并发扫描** — 秒级扫描394个U本位合约的5分钟K线
- **异动推送** — 5分钟涨跌幅≥5%的币种实时推送到Telegram
- **精确触发** — 每小时 `:00 / :05 / :10` 三次快检，覆盖整点前后关键窗口
- **持续运行** — 通过 OpenClaw cron 定时器托管，无需额外服务

## 快速开始

### 1. 配置 TG Bot

```bash
# 在 Telegram 中
1. 搜索 @BotFather，发送 /newbot 创建 Bot
2. 获取 Bot Token（如: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11）
3. 搜索你的 Bot 发一条消息
4. 访问 https://api.telegram.org/bot<TOKEN>/getUpdates 获取 chat_id
```

### 2. 配置脚本

编辑 `okx_5min_quick.py`，替换配置：

```python
TG_BOT_TOKEN = "你的BotToken"
TG_CHAT_ID = "你的ChatID"
CHANGE_THRESHOLD = 5.0   # 涨跌幅阈值（%）
```

### 3. 手动运行测试

```bash
python okx_5min_quick.py
```

### 4. 部署定时任务（OpenClaw）

```bash
# 每整点运行
openclaw cron add --name "OKX :00 快检" --cron "0 * * * *" --session isolated --message "python okx_5min_quick.py"

openclaw cron add --name "OKX :05 快检" --cron "5 * * * *" --session isolated --message "python okx_5min_quick.py"

openclaw cron add --name "OKX :10 快检" --cron "10 * * * *" --session isolated --message "python okx_5min_quick.py"
```

## 技术细节

| 项目 | 说明 |
|------|------|
| **数据源** | OKX V5 API (`/api/v5/market/candles`, `/api/v5/market/tickers`) |
| **K线周期** | 5分钟 (bar=5m) |
| **并发方式** | `ThreadPoolExecutor` (20线程) |
| **扫描速度** | 394个合约约12秒 |
| **推送** | Telegram Bot API (Parse Mode: HTML) |

## 文件结构

```
├── okx_5min_quick.py    # 主脚本（并发扫描+TG推送）
└── README.md            # 本文件
```

## License

MIT
