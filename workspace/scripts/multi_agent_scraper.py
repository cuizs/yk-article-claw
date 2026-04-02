#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗健康行业热点抓取 - 多 Agents 并行版本
使用 OpenClaw sessions_spawn 创建多个 sub-agents 并行执行任务
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = "/home/admin/.openclaw/workspace"
SCRIPTS_DIR = f"{WORKSPACE}/scripts"
DRAFTS_DIR = f"{WORKSPACE}/articles/drafts"
LOG_FILE = f"{WORKSPACE}/scripts/multi_agent_scraper.log"

# 信息源配置
SOURCES = [
    {"id": "bioon", "name": "生物谷", "url": "https://news.bioon.com/", "enabled": True},
    {"id": "bydrug", "name": "医药魔方", "url": "https://bydrug.pharmcube.com/", "enabled": True},
    # {"id": "vbdata", "name": "动脉网", "url": "https://www.vbdata.cn/", "enabled": False},  # 动态网站，暂时跳过
]


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")


def spawn_news_scraper_agent(source_id: str, source_name: str, source_url: str) -> str:
    """
    创建新闻抓取 sub-agent
    
    Returns:
        sessionKey: sub-agent 的会话密钥
    """
    task = f"""请抓取 {source_name} 的医疗健康新闻：
1. 访问网站：{source_url}
2. 抓取最新 15 条新闻（标题、链接、摘要、日期）
3. 按投资价值评分筛选出 top 5 热点
4. 将结果保存为 JSON 格式到：/home/admin/.openclaw/workspace/articles/temp/{source_id}_news.json

抓取要求：
- 使用 curl 或 requests 获取网页
- 使用正则或 BeautifulSoup 解析 HTML
- 提取新闻标题、链接、摘要、发布日期
- 根据关键词评分（临床、获批、上市、融资、IPO、突破、首创等高分）
- 保存 JSON 格式：{{"source": "{source_name}", "news": [...], "top5": [...]}}
"""
    
    try:
        # 使用 sessions_spawn 创建 sub-agent
        result = subprocess.run(
            ["openclaw", "sessions", "spawn", 
             "--task", task,
             "--label", f"news-scraper-{source_id}",
             "--timeout", "180",
             "--cleanup", "delete"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log(f"✅ 已创建 {source_name} 抓取 agent")
            return result.stdout.strip()
        else:
            log(f"❌ 创建 {source_name} 抓取 agent 失败：{result.stderr}")
            return None
            
    except Exception as e:
        log(f"❌ 创建 {source_name} 抓取 agent 异常：{e}")
        return None


def spawn_article_generator_agent() -> str:
    """
    创建文章生成 sub-agent
    
    Returns:
        sessionKey: sub-agent 的会话密钥
    """
    task = """请汇总所有新闻抓取结果，生成公众号文章：
1. 读取所有 /home/admin/.openclaw/workspace/articles/temp/*.json 文件
2. 合并所有新闻，去重，按评分排序
3. 选择 top 10 热点
4. 生成 Markdown 格式文章，包含：
   - 标题：医疗健康行业热点日报
   - 日期：今天
   - 核心摘要（10 条热点标题）
   - 热点事件详情（每条包含：来源、日期、类别、链接、摘要）
   - 行业影响分析
   - 投资视角
5. 保存到：/home/admin/.openclaw/workspace/articles/drafts/YYYY-MM-DD.md

文章风格：专业深度型，面向投资人，数据多、分析深
"""
    
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "spawn",
             "--task", task,
             "--label", "article-generator",
             "--timeout", "180",
             "--cleanup", "delete"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log("✅ 已创建文章生成 agent")
            return result.stdout.strip()
        else:
            log(f"❌ 创建文章生成 agent 失败：{result.stderr}")
            return None
            
    except Exception as e:
        log(f"❌ 创建文章生成 agent 异常：{e}")
        return None


def spawn_wechat_publisher_agent(article_path: str) -> str:
    """
    创建微信公众号发布 sub-agent
    """
    task = f"""请将文章发布到微信公众号：
1. 读取文章：{article_path}
2. 使用 wechat-article-publisher 技能发布
3. 使用 AI 生成封面图（如果可用）
4. 直接发布（不是保存草稿）
5. 返回 publish_id 和发布状态

执行命令：
cd /home/admin/skills/wechat-article-publisher
python3 scripts/publish_wechat.py {article_path} --publish --ai-cover
"""
    
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "spawn",
             "--task", task,
             "--label", "wechat-publisher",
             "--timeout", "180",
             "--cleanup", "delete"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log("✅ 已创建微信发布 agent")
            return result.stdout.strip()
        else:
            log(f"❌ 创建微信发布 agent 失败：{result.stderr}")
            return None
            
    except Exception as e:
        log(f"❌ 创建微信发布 agent 异常：{e}")
        return None


def spawn_dingtalk_sender_agent(article_path: str) -> str:
    """
    创建钉钉推送 sub-agent
    """
    task = f"""请将文章推送到钉钉：
1. 读取文章：{article_path}
2. 使用 openclaw message 发送到钉钉
3. 发送给：542362185123584037（崔占山）
4. 返回发送状态和消息 ID

执行命令：
cd /home/admin/.openclaw/workspace
bash scripts/send_to_dingtalk.sh $(date +%Y-%m-%d)
"""
    
    try:
        result = subprocess.run(
            ["openclaw", "sessions", "spawn",
             "--task", task,
             "--label", "dingtalk-sender",
             "--timeout", "120",
             "--cleanup", "delete"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            log("✅ 已创建钉钉推送 agent")
            return result.stdout.strip()
        else:
            log(f"❌ 创建钉钉推送 agent 失败：{result.stderr}")
            return None
            
    except Exception as e:
        log(f"❌ 创建钉钉推送 agent 异常：{e}")
        return None


def wait_for_agents(agent_keys: list, timeout_seconds: int = 300) -> dict:
    """
    等待所有 sub-agents 完成
    
    Returns:
        结果字典：{sessionKey: status}
    """
    import time
    
    results = {}
    start_time = time.time()
    
    log(f"⏳ 等待 {len(agent_keys)} 个 agents 完成（超时：{timeout_seconds}秒）...")
    
    while time.time() - start_time < timeout_seconds:
        all_done = True
        
        for key in agent_keys:
            if key in results:
                continue
            
            # 检查 agent 状态
            try:
                result = subprocess.run(
                    ["openclaw", "sessions", "list", "--limit", "100"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # 简单判断：如果会话不存在，则认为已完成
                if key not in result.stdout:
                    results[key] = "completed"
                    log(f"✅ Agent {key} 完成")
                else:
                    all_done = False
                    
            except Exception as e:
                log(f"检查 agent 状态异常：{e}")
                all_done = False
        
        if all_done:
            log("✅ 所有 agents 完成")
            break
        
        time.sleep(5)
    
    return results


def main():
    """主函数：协调多 agents 并行执行"""
    log("=" * 60)
    log("🚀 医疗健康新闻抓取 - 多 Agents 并行模式")
    log("=" * 60)
    
    start_time = datetime.now()
    
    # 1. 创建临时目录
    temp_dir = Path(f"{WORKSPACE}/articles/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    log(f"📁 临时目录：{temp_dir}")
    
    # 2. 并行创建新闻抓取 agents
    log("\n📰 阶段 1: 创建新闻抓取 agents...")
    scraper_agents = []
    
    for source in SOURCES:
        if source["enabled"]:
            agent_key = spawn_news_scraper_agent(
                source["id"], 
                source["name"], 
                source["url"]
            )
            if agent_key:
                scraper_agents.append(agent_key)
    
    log(f"✅ 已创建 {len(scraper_agents)} 个新闻抓取 agents\n")
    
    # 3. 等待新闻抓取完成
    log("⏳ 阶段 2: 等待新闻抓取完成...")
    scraper_results = wait_for_agents(scraper_agents, timeout_seconds=180)
    log(f"✅ 新闻抓取完成：{len(scraper_results)}/{len(scraper_agents)} 成功\n")
    
    # 4. 创建文章生成 agent
    log("📝 阶段 3: 创建文章生成 agent...")
    generator_agent = spawn_article_generator_agent()
    
    if generator_agent:
        log("⏳ 阶段 4: 等待文章生成完成...")
        generator_results = wait_for_agents([generator_agent], timeout_seconds=180)
        log(f"✅ 文章生成完成\n")
    else:
        log("❌ 文章生成 agent 创建失败")
        return
    
    # 5. 获取生成的文章路径
    today = datetime.now().strftime("%Y-%m-%d")
    article_path = f"{DRAFTS_DIR}/{today}.md"
    
    if not Path(article_path).exists():
        log(f"❌ 文章文件不存在：{article_path}")
        return
    
    log(f"📄 文章已生成：{article_path}\n")
    
    # 6. 并行创建发布 agents
    log("📤 阶段 5: 创建发布 agents...")
    publisher_agents = []
    
    # 微信发布
    wechat_agent = spawn_wechat_publisher_agent(article_path)
    if wechat_agent:
        publisher_agents.append(wechat_agent)
    
    # 钉钉推送
    dingtalk_agent = spawn_dingtalk_sender_agent(article_path)
    if dingtalk_agent:
        publisher_agents.append(dingtalk_agent)
    
    log(f"✅ 已创建 {len(publisher_agents)} 个发布 agents\n")
    
    # 7. 等待发布完成
    log("⏳ 阶段 6: 等待发布完成...")
    publisher_results = wait_for_agents(publisher_agents, timeout_seconds=180)
    log(f"✅ 发布完成：{len(publisher_results)}/{len(publisher_agents)} 成功\n")
    
    # 8. 总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    log("=" * 60)
    log("✅ 全部任务完成！")
    log(f"📊 执行时长：{duration:.1f}秒")
    log(f"📈 Agents 使用情况:")
    log(f"   - 新闻抓取：{len(scraper_agents)} 个")
    log(f"   - 文章生成：1 个")
    log(f"   - 发布推送：{len(publisher_agents)} 个")
    log(f"   - 总计：{len(scraper_agents) + 1 + len(publisher_agents)} 个")
    log("=" * 60)


if __name__ == "__main__":
    main()
