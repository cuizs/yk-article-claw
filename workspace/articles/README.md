# 医疗健康行业热点抓取系统

## 📋 系统说明

本系统自动抓取医疗健康行业热点新闻，生成公众号文章草稿，支持定时执行和一键推送。

### 信息来源

| 网站 | 状态 | 说明 |
|------|------|------|
| 生物谷 (news.bioon.com) | ✅ 已启用 | 主要新闻源 |
| 动脉网 (vcbeat.cn) | ⏸️ 待启用 | 域名暂时无法访问 |
| 医药魔方 (pharmcube.com) | ⏸️ 待启用 | 主要是数据平台，无公开新闻栏目 |

### 文章风格

- **受众：** 投资人
- **风格：** 专业深度型（数据多、分析深）
- **结构：** 核心摘要 → 热点事件 → 行业影响 → 数据支撑 → 投资视角 → 一句话总结

---

## ⏰ 定时任务

### 自动抓取时间

**每天 8:30** 自动执行抓取并生成草稿

Cron 表达式：`30 8 * * *` (Asia/Shanghai 时区)

### 自动推送

**每天 8:00** 抓取完成后**自动推送到钉钉**（用户：崔占山）

### 发布时间

**每天 9:30** 推送至公众号（需人工确认后发送）

---

## 📁 文件说明

```
/home/admin/.openclaw/workspace/
├── scripts/
│   ├── healthcare_news_scraper.py    # 核心抓取脚本
│   ├── daily_healthcare_news.sh      # 每日自动执行包装脚本
│   ├── send_to_dingtalk.sh           # 推送到钉钉脚本
│   └── send_to_wecom.sh              # 推送到企业微信脚本 (备用)
└── articles/
    └── drafts/                        # 草稿存储目录
        ├── 2026-03-11.md
        ├── 2026-03-12.md
        └── ...
```

---

## 🚀 使用指南

### 手动执行抓取

```bash
cd /home/admin/.openclaw/workspace
python3 scripts/healthcare_news_scraper.py
```

### 查看今日草稿

```bash
cat /home/admin/.openclaw/workspace/articles/drafts/$(date +%Y-%m-%d).md
```

### 推送到钉钉（手动）

```bash
# 推送今天的草稿
./scripts/send_to_dingtalk.sh

# 推送指定日期的草稿
./scripts/send_to_dingtalk.sh 2026-03-11

# 推送给指定用户（钉钉 conversationId）
./scripts/send_to_dingtalk.sh 2026-03-11 542362185123584037
```

### 查看定时任务状态

```bash
openclaw cron list
openclaw cron status --id <job-id>
```

---

## 📝 工作流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  8:30 AM    │ →  │  抓取新闻   │ →  │  生成草稿   │ →  │  通知用户   │
│  定时触发   │    │  生物谷等   │    │  Markdown   │    │  企业微信   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  发布到     │ ←  │  人工审核   │ ←  │  9:30 AM    │ ←  │  用户查看   │
│  公众号     │    │  编辑调整   │    │  推送时间   │    │  草稿内容   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 🔧 配置选项

### 修改抓取源

编辑 `scripts/healthcare_news_scraper.py`：

```python
CONFIG = {
    "sources": {
        "bioon": {
            "name": "生物谷",
            "url": "https://news.bioon.com/",
            "enabled": True,  # 改为 False 禁用
        },
        # ... 其他源
    },
    "max_articles_per_source": 10,  # 每个源最多抓取文章数
    "selected_topics_count": 3,     # 精选热点数量
}
```

### 修改推送时间

```bash
# 删除现有任务
openclaw cron remove <job-id>

# 添加新任务（修改 cron 表达式）
openclaw cron add --name "医疗健康热点抓取" \
    --cron "0 9 * * *" \
    --message "请执行抓取脚本..."
```

---

## 📊 文章质量优化

### 投资价值评分

系统自动为每条新闻打分，评分维度包括：

| 关键词类型 | 示例 | 分值 |
|-----------|------|------|
| 临床进展 | 临床、三期、二期 | 4-6 分 |
| 获批上市 | 获批、上市、FDA、NMPA | 7-8 分 |
| 资本动态 | 融资、IPO、估值 | 5-10 分 |
| 技术突破 | 突破、首创、全球 | 5-8 分 |
| 顶级期刊 | Nature、Science、Cell | +5 分 |

### 类别自动识别

系统自动识别新闻类别：
- 创新药
- 医疗器械
- 生物技术
- AI+ 医疗
- 投融资
- 政策监管
- 临床研究

---

## ⚠️ 注意事项

1. **人工审核：** AI 生成内容仅供参考，发布前务必人工审核
2. **版权合规：** 抓取内容请注意版权问题，建议改写后发布
3. **信息准确性：** 投资相关数据请核实原始来源
4. **定时任务：** 确保服务器 8:30 处于运行状态

---

## 🆘 故障排查

### 抓取失败

```bash
# 检查网络连接
curl -I https://news.bioon.com/

# 手动运行脚本查看详细错误
python3 scripts/healthcare_news_scraper.py
```

### 定时任务未执行

```bash
# 查看 cron 任务列表
openclaw cron list

# 查看任务状态
openclaw cron status --id <job-id>

# 查看网关日志
openclaw logs --follow
```

### 推送失败

```bash
# 检查企业微信配置
openclaw channels list

# 测试发送消息
openclaw message send --channel wecom --message "测试消息"
```

---

## 📞 技术支持

- 脚本位置：`/home/admin/.openclaw/workspace/scripts/`
- 草稿目录：`/home/admin/.openclaw/workspace/articles/drafts/`
- 日志文件：`/home/admin/.openclaw/workspace/scripts/news_scraper.log`

---

**最后更新：** 2026-03-11  
**维护者：** 小布 (AI 助手)
