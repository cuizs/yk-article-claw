#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗健康行业热点抓取系统
每天自动抓取新闻并生成公众号文章草稿

信息来源：
- 生物谷 (news.bioon.com) ✅ 正常
- 动脉网 (www.vbdata.cn) ⚠️ 动态渲染网站，需要浏览器支持
- 医药魔方 (bydrug.pharmcube.com) ✅ 正常

配置说明：
- 热点数量：10 条
- 每源最大抓取：15 条
- 执行时间：每天 11:30

文章结构：核心摘要→热点事件→行业影响→数据支撑→投资视角→一句话总结
"""

import os
import re
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import hashlib

# 配置
CONFIG = {
    "sources": {
        "bioon": {
            "name": "生物谷",
            "url": "https://news.bioon.com/",
            "enabled": True,
            "article_pattern": r'http://news\.bioon\.com/article/[a-z0-9]+\.html',
        },
        "vbdata": {
            "name": "动脉网",
            "url": "https://www.vbdata.cn/",
            "enabled": True,
            "article_pattern": r'https://www\.vbdata\.cn/.*',
        },
        "bydrug": {
            "name": "医药魔方",
            "url": "https://bydrug.pharmcube.com/",
            "enabled": True,
            "article_pattern": r'https://bydrug\.pharmcube\.com/.*',
        }
    },
    "output_dir": "/home/admin/.openclaw/workspace/articles/drafts",
    "max_articles_per_source": 15,
    "selected_topics_count": 10,
}

def fetch_url(url: str, timeout: int = 30) -> str:
    """使用 curl 抓取网页内容"""
    try:
        result = subprocess.run(
            ["curl", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "-H", "Accept: text/html,application/xhtml+xml", "-H", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8", "--max-time", str(timeout), url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=timeout + 5
        )
        return result.stdout
    except Exception as e:
        print(f"抓取失败 {url}: {e}")
        return ""

def parse_bioon_news(html: str) -> List[Dict]:
    """解析生物谷新闻列表"""
    news_list = []
    
    # HTML 结构：
    # <div class="item-content">
    #     <h2>
    #         <a href=" http://news.bioon.com/article/xxxx.html " ...>标题</a>
    #     </h2>
    #     <p class="text-justify">摘要</p>
    #     <span class="item-meta"><span class="item-meta-item">日期</span></span>
    # </div>
    
    # 匹配新闻条目块 - 注意 href 中可能有空格
    title_pattern = r'<div\s+class="item-content">.*?<h2>.*?<a[^>]*href="\s*(http://news\.bioon\.com/article/[a-z0-9]+\.html)\s*"[^>]*>([^<]+)</a>.*?</h2>.*?<p[^>]*>([^<]+)</p>.*?item-meta-item">\s*([0-9]{4}-[0-9]{2}-[0-9]{2})'
    
    matches = re.findall(title_pattern, html, re.DOTALL)
    
    print(f"  正则匹配到 {len(matches)} 条新闻")
    
    for link, title, summary, date in matches[:CONFIG["max_articles_per_source"]]:
        news_list.append({
            "source": "生物谷",
            "title": title.strip(),
            "link": link.strip(),
            "summary": summary.strip()[:200],  # 限制摘要长度
            "date": date,
            "category": infer_category(title, summary)
        })
    
    return news_list

def infer_category(title: str, summary: str) -> str:
    """根据标题和摘要推断新闻类别"""
    text = (title + " " + summary).lower()
    
    categories = {
        "创新药": ["创新药", "新药", "drug", "疗法", "靶向"],
        "医疗器械": ["器械", "设备", "device", "诊断"],
        "生物技术": ["基因", "细胞", "生物", "biotech", "合成生物学"],
        "AI+ 医疗": ["AI", "人工智能", "算法", "机器学习", "智能"],
        "投融资": ["融资", "投资", "IPO", "上市", "估值"],
        "政策监管": ["政策", "监管", "审批", "医保", "集采"],
        "临床研究": ["临床", "试验", "患者", "疗效"],
        "其他": []
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text:
                return category
    
    return "其他"

def parse_vbdata_news(html: str) -> List[Dict]:
    """解析动脉网新闻列表"""
    news_list = []
    
    # 尝试多种模式匹配动脉网新闻
    # 模式 1: 新闻列表项
    patterns = [
        # 模式 1: post 链接
        r'<a[^>]*href="(https://www\.vbdata\.cn/post/\d+)"[^>]*>([^<]+)</a>',
        # 模式 2: 数字 ID 链接
        r'<a[^>]*href="(/(\d+))"[^>]*title="([^"]+)"',
        # 模式 3: 通用新闻链接
        r'<a[^>]*href="(https://www\.vbdata\.cn/(\d+))"[^>]*>([^<]+)</a>',
    ]
    
    matches = []
    for pattern in patterns:
        matches = re.findall(pattern, html, re.DOTALL)
        if matches:
            break
    
    print(f"  正则匹配到 {len(matches)} 条新闻")
    
    for match in matches[:CONFIG["max_articles_per_source"]]:
        if len(match) == 2:
            link, title = match
        elif len(match) == 3:
            link, _, title = match
        else:
            continue
        
        # 清理标题
        title = re.sub(r'<[^>]+>', '', title).strip()
        if not title or len(title) < 5:
            continue
        
        # 尝试提取摘要
        summary = ""
        summary_match = re.search(rf'{re.escape(title[:20])}.*?<p[^>]*>([^<]+)</p>', html, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()[:200]
        
        news_list.append({
            "source": "动脉网",
            "title": title,
            "link": link if link.startswith("http") else f"https://www.vbdata.cn{link}",
            "summary": summary,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": infer_category(title, summary)
        })
    
    return news_list


def parse_bydrug_news(html: str) -> List[Dict]:
    """解析医药魔方新闻列表"""
    news_list = []
    
    # 医药魔方 HTML 结构（常见模式）
    # <a href="https://bydrug.pharmcube.com/xxx" class="title">标题</a>
    # <p class="summary">摘要</p>
    
    pattern = r'<a[^>]*href="(https://bydrug\.pharmcube\.com/[^"]+)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    print(f"  正则匹配到 {len(matches)} 条新闻")
    
    for link, title in matches[:CONFIG["max_articles_per_source"]]:
        # 尝试提取摘要
        summary_match = re.search(rf'{re.escape(title)}.*?<p[^>]*class="[^"]*summary[^"]*"[^>]*>([^<]+)</p>', html, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else ""
        
        news_list.append({
            "source": "医药魔方",
            "title": title.strip(),
            "link": link.strip(),
            "summary": summary[:200],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": infer_category(title, summary)
        })
    
    return news_list


def fetch_all_news() -> List[Dict]:
    """从所有启用的源抓取新闻"""
    all_news = []
    
    for source_id, source_config in CONFIG["sources"].items():
        if not source_config["enabled"]:
            print(f"跳过 {source_config.get('name', source_id)} (未启用)")
            continue
        
        print(f"正在抓取 {source_config['name']}...")
        html = fetch_url(source_config["url"])
        
        if not html:
            print(f"  抓取失败")
            continue
        
        # 解析新闻
        if source_id == "bioon":
            news_list = parse_bioon_news(html)
        elif source_id == "vbdata":
            news_list = parse_vbdata_news(html)
        elif source_id == "bydrug":
            news_list = parse_bydrug_news(html)
        else:
            news_list = []
        
        all_news.extend(news_list)
        print(f"  抓取到 {len(news_list)} 条新闻")
    
    return all_news

def score_investment_value(news: Dict) -> int:
    """评估新闻的投资价值分数"""
    score = 0
    text = (news["title"] + " " + news["summary"]).lower()
    
    # 高价值关键词
    high_value_keywords = [
        ("临床", 5), ("获批", 8), ("上市", 8), ("融资", 7), ("IPO", 10),
        ("突破", 6), ("首创", 8), ("全球", 5), ("重磅", 7), ("里程碑", 8),
        ("三期", 6), ("二期", 4), ("FDA", 7), ("NMPA", 7), ("专利", 5),
        ("合作", 4), ("授权", 5), ("收购", 6), ("并购", 6), ("估值", 5),
        ("肿瘤", 4), ("癌症", 4), ("心血管", 4), ("神经", 4), ("代谢", 3),
        ("疫苗", 5), ("抗体", 4), ("细胞治疗", 6), ("基因治疗", 6),
        ("AI", 5), ("人工智能", 5), ("诊断", 4), ("器械", 4),
    ]
    
    for keyword, points in high_value_keywords:
        if keyword.lower() in text:
            score += points
    
    # 期刊加分
    journal_keywords = ["Nature", "Science", "Cell", "NEJM", "Lancet"]
    for journal in journal_keywords:
        if journal in news["title"]:
            score += 5
    
    return score

def select_top_topics(news_list: List[Dict], count: int = 3) -> List[Dict]:
    """选择最有投资价值的热点"""
    # 为每条新闻打分
    for news in news_list:
        news["investment_score"] = score_investment_value(news)
    
    # 去重（相似标题只保留一个）
    unique_news = []
    seen_titles = set()
    for news in sorted(news_list, key=lambda x: x["investment_score"], reverse=True):
        # 简单去重：标题前 20 个字符
        title_key = news["title"][:20]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(news)
    
    # 返回得分最高的
    return sorted(unique_news, key=lambda x: x["investment_score"], reverse=True)[:count]

def generate_article_draft(topics: List[Dict], date: str) -> str:
    """生成文章草稿"""
    
    # 核心摘要
    core_summary = generate_core_summary(topics)
    
    # 热点事件
    hot_events = generate_hot_events(topics)
    
    # 行业影响
    industry_impact = generate_industry_impact(topics)
    
    # 数据支撑
    data_support = generate_data_support(topics)
    
    # 投资视角
    investment_view = generate_investment_view(topics)
    
    # 一句话总结
    one_line_summary = generate_one_line_summary(topics)
    
    draft = f"""# 医疗健康行业热点日报

**日期：** {date}
**生成时间：** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**信息来源：** 生物谷、动脉网、医药魔方

---

## 📌 核心摘要

{core_summary}

---

## 🔥 热点事件

{hot_events}

---

## 📊 行业影响

{industry_impact}

---

## 📈 数据支撑

{data_support}

---

## 💰 投资视角

{investment_view}

---

## 💡 一句话总结

{one_line_summary}

---

*本报告由自动抓取系统生成，仅供参考。投资有风险，决策需谨慎。*
"""
    
    return draft

def generate_core_summary(topics: List[Dict]) -> str:
    """生成核心摘要"""
    if not topics:
        return "今日暂无重要热点新闻。"
    
    summary_parts = []
    for i, topic in enumerate(topics, 1):
        summary_parts.append(f"{i}. **{topic['title']}** - {topic['source']}")
    
    return "\n\n".join(summary_parts)

def generate_hot_events(topics: List[Dict]) -> str:
    """生成热点事件详情"""
    if not topics:
        return "无"
    
    events = []
    for topic in topics:
        event = f"""### {topic['title']}

- **来源：** {topic['source']}
- **日期：** {topic['date']}
- **类别：** {topic['category']}
- **链接：** [{topic['link']}]({topic['link']})
- **摘要：** {topic['summary']}
"""
        events.append(event)
    
    return "\n".join(events)

def generate_industry_impact(topics: List[Dict]) -> str:
    """分析行业影响"""
    if not topics:
        return "无显著行业影响。"
    
    impacts = []
    
    # 根据类别分析影响
    category_count = {}
    for topic in topics:
        cat = topic["category"]
        category_count[cat] = category_count.get(cat, 0) + 1
    
    for cat, count in category_count.items():
        if cat == "创新药":
            impacts.append(f"- **创新药领域**：{count} 项新进展，显示研发活跃度持续，可能带来新的治疗选择和市场竞争格局变化。")
        elif cat == "投融资":
            impacts.append(f"- **资本市场**：{count} 项融资动态，反映投资者对医疗健康领域的持续关注。")
        elif cat == "生物技术":
            impacts.append(f"- **生物技术**：{count} 项技术突破，可能推动行业技术创新和产业升级。")
        elif cat == "政策监管":
            impacts.append(f"- **政策环境**：{count} 项政策动态，可能影响行业准入门槛和市场竞争。")
        else:
            impacts.append(f"- **{cat}**：{count} 项相关动态。")
    
    if not impacts:
        impacts.append("- 今日热点事件整体显示行业持续创新发展态势。")
    
    return "\n".join(impacts)

def generate_data_support(topics: List[Dict]) -> str:
    """提供数据支撑"""
    if not topics:
        return "暂无具体数据。"
    
    data_points = []
    
    # 统计信息
    data_points.append(f"- **今日抓取新闻总数：** 从各源共获取多条新闻，精选 {len(topics)} 条高价值热点")
    data_points.append(f"- **高价值关键词出现频次：** 临床/获批/融资等关键词频繁出现，显示行业活跃度")
    
    # 期刊统计
    journals = []
    for topic in topics:
        for journal in ["Nature", "Science", "Cell", "NEJM", "Lancet"]:
            if journal in topic["title"]:
                journals.append(journal)
    
    if journals:
        data_points.append(f"- **顶级期刊发表：** {', '.join(set(journals))} 等顶级期刊有新研究成果发表")
    
    # 类别分布
    categories = set(t["category"] for t in topics)
    data_points.append(f"- **热点分布领域：** {', '.join(categories)}")
    
    return "\n".join(data_points)

def generate_investment_view(topics: List[Dict]) -> str:
    """投资视角分析"""
    if not topics:
        return "暂无投资建议。"
    
    views = []
    
    # 根据热点类型给出投资视角
    has_clinical = any("临床" in t["title"] or "获批" in t["title"] for t in topics)
    has_funding = any("融资" in t["title"] or "投资" in t["title"] for t in topics)
    has_tech = any("技术" in t["title"] or "突破" in t["title"] for t in topics)
    
    if has_clinical:
        views.append("- **临床进展关注：** 有药物/器械取得临床进展，建议关注相关企业的后续商业化潜力。")
    
    if has_funding:
        views.append("- **资本动向：** 融资事件显示资本对特定赛道的偏好，可关注同领域其他标的。")
    
    if has_tech:
        views.append("- **技术创新：** 技术突破可能带来行业格局变化，关注技术领先企业的竞争优势。")
    
    # 通用建议
    views.append("- **风险提示：** 医疗健康行业研发周期长、监管严格，投资需谨慎评估风险收益比。")
    views.append("- **长期视角：** 建议从长期产业发展趋势出发，关注具有核心技术和商业化能力的企业。")
    
    return "\n".join(views)

def generate_one_line_summary(topics: List[Dict]) -> str:
    """生成一句话总结"""
    if not topics:
        return "今日医疗健康行业暂无重大热点事件。"
    
    # 提取最核心的信息
    top_topic = topics[0]
    return f"{top_topic['category']}领域{top_topic['title'][:30]}... 显示行业持续创新发展。"

def save_draft(draft: str, date: str) -> str:
    """保存文章草稿"""
    output_dir = Path(CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{date}.md"
    filepath = output_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(draft)
    
    return str(filepath)

def main():
    """主函数"""
    print("=" * 60)
    print("医疗健康行业热点抓取系统")
    print("=" * 60)
    
    # 获取今天日期
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n执行日期：{today}")
    
    # 抓取新闻
    print("\n[1/4] 正在抓取新闻...")
    all_news = fetch_all_news()
    
    if not all_news:
        print("⚠️  未抓取到任何新闻，生成空报告")
        draft = generate_article_draft([], today)
        filepath = save_draft(draft, today)
        print(f"\n草稿已保存：{filepath}")
        return
    
    print(f"共抓取到 {len(all_news)} 条新闻")
    
    # 选择热点
    print("\n[2/4] 正在筛选高价值热点...")
    top_topics = select_top_topics(all_news, CONFIG["selected_topics_count"])
    print(f"精选 {len(top_topics)} 条热点")
    
    for i, topic in enumerate(top_topics, 1):
        print(f"  {i}. [{topic['investment_score']}分] {topic['title'][:50]}...")
    
    # 生成文章
    print("\n[3/4] 正在生成文章草稿...")
    draft = generate_article_draft(top_topics, today)
    
    # 保存草稿
    print("\n[4/4] 正在保存草稿...")
    filepath = save_draft(draft, today)
    
    print("\n" + "=" * 60)
    print("✅ 完成！")
    print("=" * 60)
    print(f"草稿文件：{filepath}")
    print(f"热点数量：{len(top_topics)}")
    print(f"信息来源：{', '.join(set(t['source'] for t in top_topics))}")

if __name__ == "__main__":
    main()
