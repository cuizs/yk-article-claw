# 多 Agents 并行架构说明

## 📊 架构对比

### 原架构（串行）

```
主 Agent
  ↓
抓取生物谷 (2 分钟)
  ↓
抓取医药魔方 (2 分钟)
  ↓
生成文章 (1 分钟)
  ↓
发布微信 (1 分钟)
  ↓
推送钉钉 (30 秒)
  ↓
总耗时：~6-7 分钟
```

### 新架构（并行）

```
主 Agent（协调者）
  │
  ├─ Agent 1: 抓取生物谷 ─┐
  ├─ Agent 2: 抓取医药魔方 ─┼─→ (同时执行，2 分钟)
  │                        │
  └─ Agent 3: 生成文章 ←───┘
         ↓
  ├─ Agent 4: 微信发布 ─┐
  ├─ Agent 5: 钉钉推送 ─┼─→ (同时执行，1 分钟)
  │
  总耗时：~3-4 分钟（提升 50%）
```

---

## 🎯 Agents 分工

| Agent | 职责 | 执行时间 | 状态 |
|-------|------|----------|------|
| **Agent 1** | 抓取生物谷新闻 | ~2 分钟 | 并行 |
| **Agent 2** | 抓取医药魔方新闻 | ~2 分钟 | 并行 |
| **Agent 3** | 汇总新闻 + 生成文章 | ~1 分钟 | 串行 |
| **Agent 4** | 微信公众号发布 | ~1 分钟 | 并行 |
| **Agent 5** | 钉钉推送 | ~30 秒 | 并行 |

---

## 📁 文件结构

```
/home/admin/.openclaw/workspace/
├── scripts/
│   ├── multi_agent_news.sh        # 多 Agents 协调脚本（主入口）
│   ├── multi_agent_scraper.py     # Python 版本协调脚本（备选）
│   ├── healthcare_news_scraper.py # 新闻抓取核心脚本
│   ├── send_to_dingtalk.sh        # 钉钉推送脚本
│   └── daily_healthcare_news.sh   # 原串行脚本（保留备用）
├── articles/
│   ├── drafts/                    # 文章草稿
│   └── temp/                      # 临时数据（多 Agents 中间结果）
└── skills/
    └── wechat-article-publisher/
        └── scripts/
            └── publish_wechat.py  # 微信发布脚本
```

---

## 🚀 执行流程

### 阶段 1: 并行新闻抓取（~2 分钟）

```bash
# 同时启动 2 个后台进程
python3 -c "抓取生物谷" &  # PID 1
python3 -c "抓取医药魔方" &  # PID 2

# 等待所有进程完成
wait $PID1 $PID2
```

**输出：**
- `temp/bioon_news.json` - 生物谷新闻数据
- `temp/bydrug_news.json` - 医药魔方新闻数据

---

### 阶段 2: 汇总生成文章（~1 分钟）

```bash
# 读取所有 JSON，合并、去重、评分、排序
python3 -c "
读取 temp/*.json
合并新闻 → 去重 → 评分 → 排序 → Top 10
生成 Markdown 文章
保存至 drafts/YYYY-MM-DD.md
"
```

---

### 阶段 3: 并行发布（~1 分钟）

```bash
# 同时启动 2 个后台进程
python3 publish_wechat.py article.md --publish &  # 微信
bash send_to_dingtalk.sh YYYY-MM-DD &             # 钉钉

# 等待完成
wait
```

---

## ⚙️ 配置说明

### Cron 任务配置

```json
{
  "id": "a6020214-974d-442d-9ede-4a0348e8b2a8",
  "name": "微信公众号发布（多 Agents）",
  "schedule": {
    "kind": "cron",
    "expr": "0 8 * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "请执行 /home/admin/.openclaw/workspace/scripts/multi_agent_news.sh ...",
    "timeoutSeconds": 600
  },
  "sessionTarget": "isolated"
}
```

**关键参数：**
- `expr`: `0 8 * * *` = 每天早上 8:00
- `timeoutSeconds`: 600 秒 = 10 分钟（足够完成所有任务）
- `sessionTarget`: `isolated` = 隔离会话执行

---

## 📈 性能对比

| 指标 | 串行版本 | 多 Agents 版本 | 提升 |
|------|----------|---------------|------|
| **总耗时** | 6-7 分钟 | 3-4 分钟 | ⬆️ 50% |
| **新闻抓取** | 4 分钟（顺序） | 2 分钟（并行） | ⬆️ 100% |
| **发布推送** | 1.5 分钟（顺序） | 1 分钟（并行） | ⬆️ 33% |
| **CPU 利用** | 单核 | 多核 | 更优 |
| **可靠性** | 单点故障 | 任务隔离 | 更高 |

---

## 🔍 日志与监控

### 日志文件

| 文件 | 内容 | 路径 |
|------|------|------|
| `multi_agent.log` | 主协调脚本日志 | `scripts/` |
| `bioon.log` | 生物谷抓取日志 | `temp/` |
| `bydrug.log` | 医药魔方抓取日志 | `temp/` |
| `wechat.log` | 微信发布日志 | `temp/` |
| `dingtalk.log` | 钉钉推送日志 | `temp/` |

### 查看执行状态

```bash
# 查看最新日志
tail -50 /home/admin/.openclaw/workspace/scripts/multi_agent.log

# 查看 Cron 任务状态
openclaw cron list

# 查看执行历史
openclaw cron runs --jobId a6020214-974d-442d-9ede-4a0348e8b2a8
```

---

## 🛠️ 手动测试

### 测试多 Agents 脚本

```bash
cd /home/admin/.openclaw/workspace
bash scripts/multi_agent_news.sh
```

### 测试单个 Agent

```bash
# 测试生物谷抓取
cd /home/admin/.openclaw/workspace
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from healthcare_news_scraper import CONFIG, fetch_all_news

CONFIG['sources'] = {
    'bioon': {'name': '生物谷', 'url': 'https://news.bioon.com/', 'enabled': True},
    'vbdata': {'enabled': False},
    'bydrug': {'enabled': False}
}

news = fetch_all_news()
print(f'抓取到 {len(news)} 条新闻')
"
```

---

## 📝 故障排查

### 问题 1: 某个 Agent 卡住

**症状：** 等待超时，某个进程一直不结束

**解决：**
```bash
# 查看进程
ps aux | grep python3

# 强制终止
kill -9 <PID>

# 重新执行
bash scripts/multi_agent_news.sh
```

---

### 问题 2: 新闻抓取失败

**症状：** `temp/` 目录下缺少某个 JSON 文件

**解决：**
```bash
# 检查对应日志
cat temp/bioon.log  # 或 bydrug.log

# 手动测试抓取
cd /home/admin/.openclaw/workspace
python3 scripts/healthcare_news_scraper.py
```

---

### 问题 3: 发布失败

**症状：** 微信或钉钉推送报错

**解决：**
```bash
# 查看发布日志
cat temp/wechat.log
cat temp/dingtalk.log

# 手动测试发布
cd /home/admin/skills/wechat-article-publisher
python3 scripts/publish_wechat.py /home/admin/.openclaw/workspace/articles/drafts/2026-03-18.md --publish
```

---

## 🔄 回滚方案

如果多 Agents 版本出现问题，可以回滚到原串行版本：

### 方式 1: 修改 Cron 任务

```bash
openclaw cron update --jobId a6020214-974d-442d-9ede-4a0348e8b2a8 \
  --patch '{"payload": {"message": "请执行 /home/admin/.openclaw/workspace/scripts/daily_healthcare_news.sh ..."}}'
```

### 方式 2: 临时手动执行

```bash
# 使用原串行脚本
cd /home/admin/.openclaw/workspace
bash scripts/daily_healthcare_news.sh
```

---

## 📊 监控指标

### 关键指标

| 指标 | 目标值 | 告警阈值 |
|------|--------|----------|
| 执行时长 | < 4 分钟 | > 6 分钟 |
| 新闻抓取成功率 | 100% | < 80% |
| 发布成功率 | 100% | < 100% |
| 文章质量 | 10 条热点 | < 8 条 |

### 监控脚本

```bash
#!/bin/bash
# 检查最新执行结果
LOG_FILE="/home/admin/.openclaw/workspace/scripts/multi_agent.log"

if grep -q "全部任务完成" "$LOG_FILE"; then
    echo "✅ 执行成功"
    grep "总耗时" "$LOG_FILE"
else
    echo "❌ 执行失败"
    tail -20 "$LOG_FILE"
fi
```

---

## 🎯 优化建议

### 进一步优化方向

1. **增加信息源** - 添加动脉网、其他行业网站
2. **智能去重** - 使用 NLP 技术识别相似新闻
3. **质量评分** - 引入 ML 模型评估新闻价值
4. **自动摘要** - 使用 LLM 生成新闻摘要
5. **多渠道发布** - 增加知乎、头条等平台

### 资源优化

```bash
# 限制并发数，避免资源耗尽
export MAX_CONCURRENT_AGENTS=4

# 设置超时时间
export AGENT_TIMEOUT=180  # 秒
```

---

**文档版本：** 1.0  
**最后更新：** 2026-03-18  
**维护人员：** 系统管理员
