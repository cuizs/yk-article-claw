#!/bin/bash
# 医疗健康行业热点 - 推送到企业微信
# 用法：./send_to_wecom.sh [日期]
# 示例：./send_to_wecom.sh 2026-03-11
#       ./send_to_wecom.sh  # 默认为今天

set -e

WORKSPACE="/home/admin/.openclaw/workspace"
DRAFTS_DIR="$WORKSPACE/articles/drafts"

# 获取日期参数
if [ -n "$1" ]; then
    DATE="$1"
else
    DATE=$(date '+%Y-%m-%d')
fi

DRAFT_FILE="$DRAFTS_DIR/${DATE}.md"

if [ ! -f "$DRAFT_FILE" ]; then
    echo "❌ 未找到草稿文件：$DRAFT_FILE"
    echo "请确认日期是否正确，或先运行抓取脚本生成草稿"
    exit 1
fi

echo "📤 正在推送 ${DATE} 的医疗健康行业热点日报..."
echo "📁 文件：$DRAFT_FILE"
echo ""

# 读取草稿内容
CONTENT=$(cat "$DRAFT_FILE")

# 使用 openclaw message 发送到企业微信
# 注意：需要指定目标用户
TARGET="${2:-@崔占山}"  # 默认发送给崔占山，可通过第二个参数指定

openclaw message send --channel wecom --target "$TARGET" --message "📰 *医疗健康行业热点日报 - ${DATE}*

${CONTENT}

---
⚠️ 以上为 AI 自动生成的内容，发布前请人工审核。"

echo ""
echo "✅ 推送完成！"
echo ""
echo "💡 提示：如需发送到公众号，请复制上述内容到公众号后台编辑发布"
