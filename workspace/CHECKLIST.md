# 配置清单 - 新机器部署核对表

## 📋 部署前准备

### 1. 账号与密钥准备
- [ ] 微信公众号 AppID
- [ ] 微信公众号 AppSecret
- [ ] 钉钉应用 ClientID（如需要）
- [ ] 钉钉应用 ClientSecret（如需要）
- [ ] 通义万相 API Key（可选，用于 AI 封面）

### 2. 服务器配置
- [ ] 服务器公网 IP 地址（用于微信 IP 白名单）
- [ ] Python 3.6+ 已安装
- [ ] OpenClaw Gateway 已安装并运行
- [ ] 网络连接正常（可访问生物谷、医药魔方等网站）

---

## 🚀 部署步骤核对

### 步骤 1：文件复制
```bash
# 从源机器复制文件
scp -r /home/admin/.openclaw/workspace/scripts/ user@new-server:/home/admin/.openclaw/workspace/
scp -r /home/admin/skills/wechat-article-publisher/ user@new-server:/home/admin/skills/
scp /home/admin/.openclaw/workspace/DEPLOYMENT_GUIDE.md user@new-server:/home/admin/.openclaw/workspace/
```

- [ ] 脚本文件已复制
- [ ] 技能文件已复制
- [ ] 文档已复制

---

### 步骤 2：安装依赖
```bash
pip3 install markdown requests beautifulsoup4 pyyaml Pillow
# 可选：pip3 install dashscope
```

- [ ] Python 依赖已安装
- [ ] 依赖测试通过（`python3 -c "import markdown; print('OK')"`)

---

### 步骤 3：配置微信公众号
编辑 `/home/admin/skills/wechat-article-publisher/config.json`：

```json
{
  "wechat": {
    "app_id": "wxdb1274509010f2ad",
    "app_secret": "a043df9e357847a4023b086243485e13",
    "author": ""
  }
}
```

- [ ] AppID 已配置
- [ ] AppSecret 已配置
- [ ] 配置文件权限正确（`chmod 600 config.json`）

---

### 步骤 4：配置微信 IP 白名单
登录微信公众平台 (mp.weixin.qq.com)：
1. 开发 → 基本配置
2. IP 白名单 → 添加服务器公网 IP

- [ ] 服务器 IP 已添加到白名单
- [ ] IP 白名单测试通过

---

### 步骤 5：配置钉钉（可选）
编辑 `/home/admin/.openclaw/openclaw.json`：

```json
{
  "channels": {
    "dingtalk": {
      "enabled": true,
      "clientId": "dinguuklt72ajqms6tvr",
      "clientSecret": "OdfxmDL4zQddZsIA-VfsfjzLrrzVG3cGyJptmWlEvWVq_kOYgGKwPOugOkJi_-Np",
      "dmPolicy": "open",
      "groupPolicy": "open",
      "messageType": "markdown"
    }
  }
}
```

- [ ] 钉钉 ClientID 已配置
- [ ] 钉钉 ClientSecret 已配置
- [ ] 运行 `openclaw doctor --fix` 应用配置

---

### 步骤 6：配置 AI 封面（可选）
```bash
export DASHSCOPE_API_KEY="sk-xxxxx"
# 或添加到 ~/.bashrc
echo "export DASHSCOPE_API_KEY=\"sk-xxxxx\"" >> ~/.bashrc
source ~/.bashrc
```

- [ ] API Key 已配置
- [ ] 测试：`python3 -c "import os; print(os.getenv('DASHSCOPE_API_KEY'))"`

---

### 步骤 7：测试抓取脚本
```bash
cd /home/admin/.openclaw/workspace
python3 scripts/healthcare_news_scraper.py
```

预期输出：
```
============================================================
✅ 完成！
============================================================
草稿文件：/home/admin/.openclaw/workspace/articles/drafts/YYYY-MM-DD.md
热点数量：10
```

- [ ] 新闻抓取成功
- [ ] 文章生成成功
- [ ] 草稿文件已创建

---

### 步骤 8：测试完整流程
```bash
cd /home/admin/.openclaw/workspace
bash scripts/daily_healthcare_news.sh
```

预期输出：
```
✅ 医疗健康行业热点日报已生成：YYYY-MM-DD.md
✅ 钉钉推送完成
✅ 微信公众号发布完成
```

- [ ] 钉钉推送成功
- [ ] 微信公众号发布成功
- [ ] 查看公众号后台确认文章已发布

---

### 步骤 9：配置定时任务
```bash
# 方式 1：使用 OpenClaw Cron
openclaw cron add --job /tmp/cron_job.json

# 方式 2：使用系统 Crontab
crontab -e
# 添加：30 11 * * * cd /home/admin/.openclaw/workspace && bash scripts/daily_healthcare_news.sh >> /home/admin/.openclaw/logs/healthcare_news.log 2>&1
```

- [ ] Cron 任务已创建
- [ ] 验证：`openclaw cron list`
- [ ] 确认下次执行时间正确

---

### 步骤 10：配置监控与日志
```bash
# 查看日志
tail -f /home/admin/.openclaw/workspace/scripts/news_scraper.log

# 查看 Cron 状态
openclaw cron status
openclaw cron list
```

- [ ] 日志文件可写入
- [ ] Cron 状态正常
- [ ] 设置日志轮转（可选）

---

## ✅ 最终验证

### 功能验证
- [ ] 新闻抓取正常（至少 2 个信息源）
- [ ] 热点筛选正常（10 条热点）
- [ ] 文章格式正确（Markdown）
- [ ] 钉钉推送正常
- [ ] 微信公众号发布正常
- [ ] 定时任务正常

### 性能验证
- [ ] 执行时间 < 5 分钟
- [ ] 无内存泄漏
- [ ] 日志文件大小正常

### 安全验证
- [ ] API 密钥权限正确（600）
- [ ] IP 白名单配置正确
- [ ] 无敏感信息泄露

---

## 📞 问题排查

### 常见问题
1. **微信公众号发布失败**
   - 检查 AppID/AppSecret
   - 检查 IP 白名单
   - 查看错误日志

2. **钉钉推送失败**
   - 检查 channel 配置
   - 运行 `openclaw doctor --fix`

3. **新闻抓取失败**
   - 检查网络连接
   - 检查网站可访问性
   - 查看日志中的具体错误

### 支持资源
- 部署文档：`/home/admin/.openclaw/workspace/DEPLOYMENT_GUIDE.md`
- OpenClaw 文档：https://docs.openclaw.ai
- 微信公众号 API：https://developers.weixin.qq.com/doc/

---

**部署完成日期：** ____________
**部署人员：** ____________
**服务器 IP：** ____________
**备注：** ____________
