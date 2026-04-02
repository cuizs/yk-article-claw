#!/bin/bash
# 医疗健康行业热点抓取 - 每日自动执行脚本
# 执行时间：每天 8:00
# 功能：抓取新闻 → 生成文章 → 推送给用户

set -e

WORKSPACE="/home/admin/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"
DRAFTS_DIR="$WORKSPACE/articles/drafts"
LOG_FILE="$WORKSPACE/scripts/news_scraper.log"

echo "========================================" >> "$LOG_FILE"
echo "执行时间：$(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 1. 执行抓取脚本
cd "$WORKSPACE"
python3 "$SCRIPTS_DIR/healthcare_news_scraper.py" >> "$LOG_FILE" 2>&1

# 2. 获取今天生成的草稿文件名
TODAY=$(date '+%Y-%m-%d')
DRAFT_FILE="$DRAFTS_DIR/${TODAY}.md"

if [ -f "$DRAFT_FILE" ]; then
    echo "✅ 草稿生成成功：$DRAFT_FILE" >> "$LOG_FILE"
    echo "✅ 医疗健康行业热点日报已生成：${TODAY}.md"
    echo "📁 文件位置：$DRAFT_FILE"
    echo ""
    
    # 自动推送到钉钉
    echo "📤 正在自动推送到钉钉..." >> "$LOG_FILE"
    cd "$WORKSPACE"
    bash "$SCRIPTS_DIR/send_to_dingtalk.sh" "$TODAY" >> "$LOG_FILE" 2>&1
    echo "✅ 钉钉推送完成" >> "$LOG_FILE"
    
    # 自动发布到微信公众号（使用 AI 生成封面图）
    echo "📤 正在发布到微信公众号（AI 封面）..." >> "$LOG_FILE"
    cd "/home/admin/skills/wechat-article-publisher"
    python3 scripts/publish_wechat.py "$DRAFT_FILE" --publish --ai-cover >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ 微信公众号发布完成（AI 封面）" >> "$LOG_FILE"
    else
        echo "⚠️  微信公众号发布失败，请检查日志" >> "$LOG_FILE"
    fi
else
    echo "❌ 草稿生成失败" >> "$LOG_FILE"
    echo "❌ 未找到草稿文件：$DRAFT_FILE"
    exit 1
fi

echo "" >> "$LOG_FILE"
