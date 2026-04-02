#!/bin/bash
# 医疗健康行业热点系统 - 快速配置脚本
# 使用方法：bash setup_quick_config.sh

set -e

echo "=========================================="
echo "医疗健康行业热点系统 - 快速配置"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
WORKSPACE="/home/admin/.openclaw/workspace"
SKILLS_DIR="/home/admin/skills"
WECHAT_SKILL_DIR="$SKILLS_DIR/wechat-article-publisher"

echo "📁 工作目录：$WORKSPACE"
echo "📁 技能目录：$WECHAT_SKILL_DIR"
echo ""

# 1. 检查目录
echo "1️⃣  检查目录结构..."
mkdir -p "$WORKSPACE/articles/drafts"
mkdir -p "$WECHAT_SKILL_DIR/assets"
mkdir -p "$WECHAT_SKILL_DIR/scripts"
echo -e "${GREEN}✅ 目录结构创建完成${NC}"
echo ""

# 2. 安装依赖
echo "2️⃣  安装 Python 依赖..."
pip3 install markdown requests beautifulsoup4 pyyaml Pillow --quiet
echo -e "${GREEN}✅ 基础依赖安装完成${NC}"
echo ""

# 3. 配置微信公众号
echo "3️⃣  配置微信公众号..."
echo "请输入微信公众号 AppID:"
read -r APP_ID
echo "请输入微信公众号 AppSecret:"
read -r APP_SECRET

cat > "$WECHAT_SKILL_DIR/config.json" << EOF
{
  "wechat": {
    "app_id": "$APP_ID",
    "app_secret": "$APP_SECRET",
    "author": ""
  }
}
EOF
echo -e "${GREEN}✅ 微信公众号配置完成${NC}"
echo ""

# 4. 配置 AI 封面（可选）
echo "4️⃣  配置 AI 封面生成（可选，直接回车跳过）..."
read -r -p "请输入通义万相 API Key (可选): " DASHSCOPE_KEY

if [ -n "$DASHSCOPE_KEY" ]; then
    echo "export DASHSCOPE_API_KEY=\"$DASHSCOPE_KEY\"" >> ~/.bashrc
    source ~/.bashrc
    echo -e "${GREEN}✅ AI 封面配置完成${NC}"
else
    echo -e "${YELLOW}⚠️  跳过 AI 封面配置，将使用 PIL 备用方案${NC}"
fi
echo ""

# 5. 配置定时任务
echo "5️⃣  配置定时任务..."
echo "请选择执行时间："
echo "1) 每天 11:30 (默认)"
echo "2) 每天 9:00"
echo "3) 每天 8:00"
echo "4) 自定义"
read -r -p "请输入选项 (1-4, 默认 1): " TIME_OPTION

case $TIME_OPTION in
    2) CRON_EXPR="0 9 * * *" ;;
    3) CRON_EXPR="0 8 * * *" ;;
    4) 
        read -r -p "请输入 Cron 表达式 (例如：30 11 * * *): " CRON_EXPR
        ;;
    *) CRON_EXPR="30 11 * * *" ;;
esac

echo ""
echo "正在创建 OpenClaw Cron 任务..."

# 创建 Cron 任务（需要 OpenClaw API）
cat > /tmp/cron_job.json << EOF
{
  "name": "医疗健康热点抓取",
  "schedule": {
    "kind": "cron",
    "expr": "$CRON_EXPR",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "agentTurn",
    "message": "请执行 $WORKSPACE/scripts/daily_healthcare_news.sh 脚本抓取今日医疗健康行业热点，生成公众号文章草稿，自动推送到钉钉，并直接发布到微信公众号。执行完成后告诉我结果。",
    "timeoutSeconds": 300
  },
  "sessionTarget": "isolated",
  "enabled": true
}
EOF

echo -e "${YELLOW}⚠️  Cron 任务配置已生成，请手动执行以下命令创建：${NC}"
echo ""
echo "openclaw cron add --job /tmp/cron_job.json"
echo ""

# 6. 测试配置
echo "6️⃣  测试配置..."
echo ""
echo "测试新闻抓取..."
cd "$WORKSPACE" && python3 scripts/healthcare_news_scraper.py 2>&1 | tail -10
echo ""

# 7. 完成提示
echo "=========================================="
echo -e "${GREEN}✅ 配置完成！${NC}"
echo "=========================================="
echo ""
echo "📋 下一步操作："
echo "1. 创建 Cron 任务："
echo "   openclaw cron add --job /tmp/cron_job.json"
echo ""
echo "2. 测试完整流程："
echo "   cd $WORKSPACE && bash scripts/daily_healthcare_news.sh"
echo ""
echo "3. 查看执行日志："
echo "   tail -50 $WORKSPACE/scripts/news_scraper.log"
echo ""
echo "4. 配置钉钉推送（如未配置）："
echo "   编辑 /home/admin/.openclaw/openclaw.json"
echo "   添加 dingtalk channel 配置"
echo ""
echo "📖 详细文档：$WORKSPACE/DEPLOYMENT_GUIDE.md"
echo ""
