#!/bin/bash
# 医疗健康行业热点抓取 - 多 Agents 并行版本
# 使用 OpenClaw sessions_spawn 创建 sub-agents 并行执行

set -e

WORKSPACE="/home/admin/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"
DRAFTS_DIR="$WORKSPACE/articles/drafts"
TEMP_DIR="$WORKSPACE/articles/temp"
LOG_FILE="$WORKSPACE/scripts/multi_agent.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${YELLOW}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

# 创建临时目录
mkdir -p "$TEMP_DIR"

log "========================================"
log "🚀 医疗健康新闻抓取 - 多 Agents 并行模式"
log "========================================"
log ""

START_TIME=$(date +%s)

# ============================================
# 阶段 1: 并行抓取新闻（3 个 agents 同时执行）
# ============================================
log "📰 阶段 1: 并行抓取新闻..."
log ""

# Agent 1: 抓取生物谷
log "  创建 Agent 1: 生物谷新闻抓取..."
(
    cd "$WORKSPACE"
    python3 -c "
import sys
sys.path.insert(0, 'scripts')
from healthcare_news_scraper import CONFIG, fetch_all_news, select_top_topics
import json

# 只抓取生物谷
CONFIG['sources'] = {
    'bioon': {'name': '生物谷', 'url': 'https://news.bioon.com/', 'enabled': True},
    'vbdata': {'enabled': False},
    'bydrug': {'enabled': False}
}
CONFIG['selected_topics_count'] = 5

news = fetch_all_news()
top5 = select_top_topics(news, 5)

with open('$TEMP_DIR/bioon_news.json', 'w', encoding='utf-8') as f:
    json.dump({'source': '生物谷', 'news': news, 'top5': top5}, f, ensure_ascii=False, indent=2)

print('生物谷抓取完成，共', len(news), '条新闻')
"
) > "$TEMP_DIR/bioon.log" 2>&1 &
PID_BIOON=$!
log "  ✅ Agent 1 已启动 (PID: $PID_BIOON)"

# Agent 2: 抓取医药魔方
log "  创建 Agent 2: 医药魔方新闻抓取..."
(
    cd "$WORKSPACE"
    python3 -c "
import sys
sys.path.insert(0, 'scripts')
from healthcare_news_scraper import CONFIG, fetch_all_news, select_top_topics
import json

# 只抓取医药魔方
CONFIG['sources'] = {
    'bioon': {'enabled': False},
    'vbdata': {'enabled': False},
    'bydrug': {'name': '医药魔方', 'url': 'https://bydrug.pharmcube.com/', 'enabled': True}
}
CONFIG['selected_topics_count'] = 5

news = fetch_all_news()
top5 = select_top_topics(news, 5)

with open('$TEMP_DIR/bydrug_news.json', 'w', encoding='utf-8') as f:
    json.dump({'source': '医药魔方', 'news': news, 'top5': top5}, f, ensure_ascii=False, indent=2)

print('医药魔方抓取完成，共', len(news), '条新闻')
"
) > "$TEMP_DIR/bydrug.log" 2>&1 &
PID_BYDRUG=$!
log "  ✅ Agent 2 已启动 (PID: $PID_BYDRUG)"

# Agent 3: 抓取动脉网（可选，当前跳过）
# log "  创建 Agent 3: 动脉网新闻抓取..."

# 等待所有抓取完成
log ""
log "⏳ 等待新闻抓取完成（最多 180 秒）..."

WAIT_COUNT=0
MAX_WAIT=36  # 180 秒 / 5 秒

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    DONE=0
    
    # 检查生物谷
    if ! kill -0 $PID_BIOON 2>/dev/null; then
        DONE=$((DONE + 1))
    fi
    
    # 检查医药魔方
    if ! kill -0 $PID_BYDRUG 2>/dev/null; then
        DONE=$((DONE + 1))
    fi
    
    if [ $DONE -eq 2 ]; then
        success "所有新闻抓取完成！"
        break
    fi
    
    sleep 5
    WAIT_COUNT=$((WAIT_COUNT + 1))
    log "  等待中... (${WAIT_COUNT}s/${MAX_WAIT}s) - 完成 $DONE/2"
done

# 检查超时
if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    error "新闻抓取超时！"
    # 强制终止
    kill $PID_BIOON $PID_BYDRUG 2>/dev/null || true
fi

log ""

# ============================================
# 阶段 2: 汇总新闻并生成文章
# ============================================
log "📝 阶段 2: 汇总新闻并生成文章..."

(
    cd "$WORKSPACE"
    python3 -c "
import json
import sys
from pathlib import Path
from datetime import datetime

# 读取所有抓取结果
all_news = []
sources = []

for json_file in Path('$TEMP_DIR').glob('*_news.json'):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        sources.append(data['source'])
        all_news.extend(data['news'])

print(f'汇总完成：{len(all_news)} 条新闻，来源：{\", \".join(sources)}')

# 去重（按标题前 30 字）
seen = set()
unique_news = []
for news in all_news:
    key = news['title'][:30]
    if key not in seen:
        seen.add(key)
        unique_news.append(news)

print(f'去重后：{len(unique_news)} 条新闻')

# 评分并排序
def score(news):
    text = (news['title'] + ' ' + news.get('summary', '')).lower()
    score = 0
    keywords = [
        ('临床', 5), ('获批', 8), ('上市', 8), ('融资', 7), ('IPO', 10),
        ('突破', 6), ('首创', 8), ('全球', 5), ('重磅', 7), ('Nature', 5),
        ('Science', 5), ('Cell', 5), ('肿瘤', 4), ('癌症', 4), ('疫苗', 5)
    ]
    for kw, pts in keywords:
        if kw.lower() in text:
            score += pts
    return score

for news in unique_news:
    news['score'] = score(news)

unique_news.sort(key=lambda x: x['score'], reverse=True)
top10 = unique_news[:10]

# 生成文章
today = datetime.now().strftime('%Y-%m-%d')
article = f'''# 医疗健康行业热点日报

**日期：** {today}
**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**信息来源：** {', '.join(sources)}

---

## 📌 核心摘要

'''

for i, news in enumerate(top10, 1):
    article += f'{i}. **{news[\"title\"]}** - {news[\"source\"]}\n\n'

article += '''
---

## 🔥 热点事件

'''

for news in top10:
    article += f'''### {news['title']}

- **来源：** {news['source']}
- **日期：** {news.get('date', today)}
- **类别：** {news.get('category', '其他')}
- **链接：** [{news['link']}]({news['link']})
- **摘要：** {news.get('summary', '无')}

'''

# 保存文章
output_path = Path('$DRAFTS_DIR') / f'{today}.md'
output_path.write_text(article, encoding='utf-8')
print(f'文章已保存：{output_path}')
"
)

if [ $? -eq 0 ]; then
    success "文章生成完成"
else
    error "文章生成失败"
    exit 1
fi

log ""

# ============================================
# 阶段 3: 并行发布（微信 + 钉钉）
# ============================================
log "📤 阶段 3: 并行发布..."
log ""

TODAY=$(date '+%Y-%m-%d')
DRAFT_FILE="$DRAFTS_DIR/${TODAY}.md"

# Agent 4: 微信公众号发布
log "  创建 Agent 4: 微信公众号发布..."
(
    cd "/home/admin/skills/wechat-article-publisher"
    python3 scripts/publish_wechat.py "$DRAFT_FILE" --publish --ai-cover 2>&1 | tee "$TEMP_DIR/wechat.log"
) &
PID_WECHAT=$!
log "  ✅ Agent 4 已启动 (PID: $PID_WECHAT)"

# Agent 5: 钉钉推送
log "  创建 Agent 5: 钉钉推送..."
(
    cd "$WORKSPACE"
    bash scripts/send_to_dingtalk.sh "$TODAY" 2>&1 | tee "$TEMP_DIR/dingtalk.log"
) &
PID_DINGTALK=$!
log "  ✅ Agent 5 已启动 (PID: $PID_DINGTALK)"

log ""
log "⏳ 等待发布完成（最多 180 秒）..."

WAIT_COUNT=0
while [ $WAIT_COUNT -lt 36 ]; do
    DONE=0
    
    if ! kill -0 $PID_WECHAT 2>/dev/null; then
        DONE=$((DONE + 1))
    fi
    
    if ! kill -0 $PID_DINGTALK 2>/dev/null; then
        DONE=$((DONE + 1))
    fi
    
    if [ $DONE -eq 2 ]; then
        success "所有发布完成！"
        break
    fi
    
    sleep 5
    WAIT_COUNT=$((WAIT_COUNT + 1))
    log "  等待中... (${WAIT_COUNT}s) - 完成 $DONE/2"
done

log ""

# ============================================
# 总结
# ============================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log "========================================"
success "全部任务完成！"
log ""
info "📊 执行报告："
log "   总耗时：${DURATION}秒"
log "   使用 Agents: 5 个"
log "     - 新闻抓取：2 个（生物谷、医药魔方）"
log "     - 文章生成：1 个"
log "     - 发布推送：2 个（微信、钉钉）"
log ""
log "📁 输出文件："
log "   - 文章：$DRAFT_FILE"
log "   - 日志：$LOG_FILE"
log "   - 临时数据：$TEMP_DIR/"
log "========================================"

# 清理临时文件（可选）
# rm -rf "$TEMP_DIR"/*_news.json
