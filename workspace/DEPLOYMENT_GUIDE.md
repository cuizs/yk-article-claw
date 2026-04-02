# 医疗健康行业热点自动抓取与发布系统 - 部署指南

## 📋 系统概述

本系统自动抓取医疗健康行业热点新闻，生成公众号文章草稿，并自动发布到微信公众号和钉钉。

### 功能特性
- ✅ 自动抓取多个信息源（生物谷、医药魔方、动脉网）
- ✅ 智能筛选高价值热点（投资视角评分）
- ✅ 生成专业公众号文章（Markdown 格式）
- ✅ 自动推送到钉钉
- ✅ 自动发布到微信公众号
- ✅ 支持 AI 生成封面图（可选）
- ✅ 定时任务调度（每天 11:30）

---

## 🚀 部署步骤

### 1. 环境准备

#### 1.1 系统要求
- Python 3.6+
- OpenClaw Gateway
- Linux/Unix 系统

#### 1.2 安装依赖
```bash
# 进入工作目录
cd /home/admin/.openclaw/workspace

# 安装 Python 依赖
pip3 install markdown requests beautifulsoup4 pyyaml Pillow

# 可选：AI 封面生成依赖
pip3 install dashscope  # 如果需要使用通义万相 AI 生成封面
```

---

### 2. 文件结构

```
/home/admin/.openclaw/workspace/
├── scripts/
│   ├── healthcare_news_scraper.py    # 新闻抓取与文章生成脚本
│   ├── daily_healthcare_news.sh      # 每日自动执行脚本
│   ├── send_to_dingtalk.sh           # 钉钉推送脚本
│   └── news_scraper.log              # 执行日志
├── articles/
│   ├── README.md
│   └── drafts/                       # 文章草稿目录
│       └── YYYY-MM-DD.md
└── skills/
    └── wechat-article-publisher/     # 微信公众号发布技能
        ├── SKILL.md
        ├── config.json
        ├── scripts/
        │   ├── publish_wechat.py     # 微信发布脚本
        │   └── ai_image_generator.py # AI 封面生成脚本
        └── assets/
            └── generated_cover.jpg   # 生成的封面图
```

---

### 3. 配置文件

#### 3.1 微信公众号配置

编辑 `/home/admin/skills/wechat-article-publisher/config.json`：

```json
{
  "wechat": {
    "app_id": "你的微信公众号 AppID",
    "app_secret": "你的微信公众号 AppSecret",
    "author": "可选：作者名"
  }
}
```

**获取方式：**
1. 登录微信公众平台 (mp.weixin.qq.com)
2. 开发 → 基本配置
3. 获取 AppID 和 AppSecret

**IP 白名单配置：**
1. 微信公众平台 → 开发 → 基本配置
2. IP 白名单中添加服务器公网 IP

---

#### 3.2 钉钉推送配置

钉钉推送通过 OpenClaw 的 dingtalk channel 自动处理，无需额外配置。

确保 OpenClaw 配置中包含钉钉 channel：

```json
{
  "channels": {
    "dingtalk": {
      "enabled": true,
      "clientId": "你的钉钉应用 ClientID",
      "clientSecret": "你的钉钉应用 ClientSecret",
      "dmPolicy": "open",
      "groupPolicy": "open",
      "messageType": "markdown"
    }
  }
}
```

---

#### 3.3 抓取脚本配置

编辑 `/home/admin/.openclaw/workspace/scripts/healthcare_news_scraper.py`：

```python
CONFIG = {
    "sources": {
        "bioon": {
            "name": "生物谷",
            "url": "https://news.bioon.com/",
            "enabled": True,
        },
        "vbdata": {
            "name": "动脉网",
            "url": "https://www.vbdata.cn/",
            "enabled": True,  # 注意：动脉网是动态网站，需要浏览器支持
        },
        "bydrug": {
            "name": "医药魔方",
            "url": "https://bydrug.pharmcube.com/",
            "enabled": True,
        }
    },
    "output_dir": "/home/admin/.openclaw/workspace/articles/drafts",
    "max_articles_per_source": 15,  # 每源最大抓取数
    "selected_topics_count": 10,     # 精选热点数量
}
```

---

#### 3.4 AI 封面生成配置（可选）

如需使用 AI 生成封面图，需要配置通义万相 API 密钥：

**方式 1：环境变量**
```bash
export DASHSCOPE_API_KEY="你的通义万相 API 密钥"
```

**方式 2：OpenClaw 配置**
在 `/home/admin/.openclaw/openclaw.json` 的 models.providers.dashscope 中添加 apiKey。

---

### 4. 定时任务配置

#### 4.1 使用 OpenClaw Cron（推荐）

通过 OpenClaw API 创建定时任务：

```bash
# 创建定时任务（每天 11:30 执行）
curl -X POST http://localhost:18789/cron/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "医疗健康热点抓取",
    "schedule": {
      "kind": "cron",
      "expr": "30 11 * * *",
      "tz": "Asia/Shanghai"
    },
    "payload": {
      "kind": "agentTurn",
      "message": "请执行 /home/admin/.openclaw/workspace/scripts/daily_healthcare_news.sh 脚本抓取今日医疗健康行业热点，生成公众号文章草稿，自动推送到钉钉，并直接发布到微信公众号。执行完成后告诉我结果。",
      "timeoutSeconds": 300
    },
    "sessionTarget": "isolated",
    "enabled": true
  }'
```

**OpenClaw Cron 配置说明：**
- `schedule.expr`: Cron 表达式（`30 11 * * *` = 每天 11:30）
- `payload.message`: 执行指令
- `sessionTarget`: "isolated"（隔离会话）
- `timeoutSeconds`: 超时时间（秒）

---

#### 4.2 使用系统 Crontab（备选）

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天 11:30 执行）
30 11 * * * cd /home/admin/.openclaw/workspace && bash scripts/daily_healthcare_news.sh >> /home/admin/.openclaw/logs/healthcare_news.log 2>&1
```

---

### 5. 手动测试

#### 5.1 测试新闻抓取
```bash
cd /home/admin/.openclaw/workspace
python3 scripts/healthcare_news_scraper.py
```

#### 5.2 测试完整流程
```bash
cd /home/admin/.openclaw/workspace
bash scripts/daily_healthcare_news.sh
```

#### 5.3 测试微信公众号发布
```bash
cd /home/admin/skills/wechat-article-publisher
python3 scripts/publish_wechat.py /home/admin/.openclaw/workspace/articles/drafts/2026-03-17.md --publish
```

#### 5.4 测试 AI 封面生成
```bash
cd /home/admin/skills/wechat-article-publisher
python3 scripts/ai_image_generator.py --title "医疗健康行业热点" --test
```

---

### 6. 日志与监控

#### 6.1 日志文件位置
- 抓取日志：`/home/admin/.openclaw/workspace/scripts/news_scraper.log`
- 网关日志：`/home/admin/.openclaw/logs/gateway.log`
- Cron 日志：`/home/admin/.openclaw/cron/jobs.json`

#### 6.2 查看执行状态
```bash
# 查看最新日志
tail -50 /home/admin/.openclaw/workspace/scripts/news_scraper.log

# 查看 Cron 任务状态
openclaw cron list

# 查看 Cron 执行历史
openclaw cron runs --jobId YOUR_JOB_ID
```

---

### 7. 常见问题排查

#### 7.1 微信公众号发布失败
**错误：** `errcode: 40001` 或 `invalid credential`
- 检查 AppID 和 AppSecret 是否正确
- 确认 IP 地址在白名单中
- 确认 access_token 未过期（脚本会自动刷新）

**错误：** `errcode: 45003` 标题过长
- 标题限制 64 个字符，脚本会自动截断

#### 7.2 钉钉推送失败
- 检查 OpenClaw 配置中 dingtalk channel 是否启用
- 检查 ClientID 和 ClientSecret 是否正确
- 运行 `openclaw doctor --fix` 修复配置

#### 7.3 新闻抓取失败
- 检查网络连接
- 检查网站是否可访问
- 查看日志中的具体错误信息

#### 7.4 AI 封面生成失败
- 检查 DASHSCOPE_API_KEY 是否配置
- 确认 API 配额是否充足
- 脚本会自动回退到 PIL 备用方案

---

### 8. 配置调优

#### 8.1 调整热点数量
编辑 `healthcare_news_scraper.py`：
```python
"selected_topics_count": 10,  # 修改为你想要的数量
```

#### 8.2 调整抓取源
编辑 `healthcare_news_scraper.py`：
```python
"bioon": {"enabled": True},   # 启用/禁用生物谷
"vbdata": {"enabled": False}, # 启用/禁用动脉网
"bydrug": {"enabled": True},  # 启用/禁用医药魔方
```

#### 8.3 调整执行时间
修改 Cron 表达式：
```json
"schedule": {
  "expr": "30 11 * * *"  // 每天 11:30
  // 改为 "0 9 * * *" = 每天 9:00
}
```

#### 8.4 调整文章风格
编辑 `publish_wechat.py`：
```python
template = (args.template or "viral").strip().lower()
// "viral" = 病毒式风格（彩色标题框）
// "standard" = 标准风格
```

---

### 9. 备份与迁移

#### 9.1 备份配置
```bash
# 备份脚本
tar -czf healthcare_news_backup.tar.gz \
  /home/admin/.openclaw/workspace/scripts/ \
  /home/admin/skills/wechat-article-publisher/config.json \
  /home/admin/.openclaw/openclaw.json
```

#### 9.2 迁移到新机器
```bash
# 解压备份
tar -xzf healthcare_news_backup.tar.gz -C /

# 安装依赖
pip3 install markdown requests beautifulsoup4 pyyaml Pillow

# 配置 API 密钥
# - 微信公众号 AppID/AppSecret
# - 钉钉 ClientID/ClientSecret
# - 通义万相 API Key（可选）

# 配置定时任务
openclaw cron add ...
```

---

### 10. 安全注意事项

1. **API 密钥安全**
   - 不要将 config.json 提交到版本控制
   - 使用环境变量存储敏感信息
   - 定期轮换 API 密钥

2. **IP 白名单**
   - 微信公众号后台配置服务器 IP
   - 避免使用动态 IP

3. **发布频率限制**
   - 微信公众号每天限制发布 1 次（订阅号）
   - 避免短时间内频繁调用 API

4. **数据备份**
   - 定期备份生成的文章草稿
   - 保留执行日志便于排查问题

---

## 📞 技术支持

- OpenClaw 文档：https://docs.openclaw.ai
- 微信公众号 API 文档：https://developers.weixin.qq.com/doc/offiaccount/
- 通义万相 API 文档：https://help.aliyun.com/zh/dashscope/

---

## 📝 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-03-17 | 初始版本，包含完整部署流程 |

---

**最后更新：** 2026-03-17
