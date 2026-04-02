# OpenClaw 部署 SOP - 小崔的服务器

**文档生成时间：** 2026-03-11  
**服务器：** 阿里云 ECS (Alibaba Cloud Linux 3)  
**主机 ID：** iZuf6f7xfnj0pn5yovojifZ

---

## 📋 环境准备阶段

### 1. 系统依赖安装

```bash
# 安装基础开发工具
sudo yum install gcc make patch zlib-devel bzip2 bzip2-devel readline-devel \
    sqlite sqlite-devel openssl11-devel tk-devel libffi-devel xz-devel \
    libuuid-devel gdbm-libs libnsl2 -y

# 安装 Docker（可选）
sudo dnf -y install dnf-plugin-releasever-adapter --repo alinux3-plus
sudo dnf -y install docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker

# 安装防火墙（可选）
sudo systemctl enable firewalld --now
```

### 2. Python 环境（pyenv）

```bash
# 安装 pyenv 依赖后
pyenv install 3.12.11 --verbose
```

---

## 🚀 OpenClaw 安装阶段

### 方案 A：官方安装脚本（推荐）

```bash
# 方式 1：官方脚本
curl -fsSL https://openclaw.ai/install.sh | bash

# 方式 2：阿里云镜像脚本
curl -fsSL https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20260211/mqttum/openclaw_installer.sh \
    -o openclaw_installer.sh && bash openclaw_installer.sh

# 安装为系统服务（开机自启）
bash openclaw_installer.sh --install-daemon
```

### 配置 npm 全局路径

```bash
# 添加 npm 全局 bin 到 PATH
echo 'export PATH="/home/admin/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 验证安装
openclaw -v
openclaw -h
```

---

## ⚙️ 企业微信渠道配置

### 1. 安装企业微信插件

```bash
# 安装企业微信 OpenClaw 插件
openclaw plugins install @wecom/wecom-openclaw-plugin

# 如果依赖有问题，手动安装 SDK
npm install @wecom/aibot-node-sdk -g
# 或使用 cnpm（国内更快）
cnpm i @wecom/aibot-node-sdk
```

### 2. 配置企业微信机器人

```bash
# 方式 1：交互式配置
openclaw channels add

# 方式 2：命令行配置
openclaw config set channels.wecom.botId <YOUR_BOT_ID>
openclaw config set channels.wecom.secret <YOUR_BOT_SECRET>
openclaw config set channels.wecom.enabled true
```

### 3. 配对机器人

```bash
# 在企业微信管理后台获取配对码，然后执行
openclaw pairing approve wecom <PAIRING_CODE>
# 示例：openclaw pairing approve wecom WHAMJY6G
```

### 4. 重启网关

```bash
openclaw gateway restart
```

---

## 🔧 配置管理

### 配置文件位置

```
~/.openclaw/openclaw.json
```

### 常用配置命令

```bash
# 查看配置
openclaw config

# 编辑配置（手动）
vi ~/.openclaw/openclaw.json

# 验证配置
openclaw config validate

# 设置单项配置
openclaw config set <key> <value>
```

### 关键配置项

```json
{
  "channels": {
    "wecom": {
      "enabled": true,
      "botId": "aibOFNQOditruGrfxCvy_7hNuGprdhR6lWC",
      "secret": "mPVKgQG6D3CoKXBuOHRnCU8q2VGkcLorODFdLLi7M3K",
      "allowFrom": [],
      "dmPolicy": "pairing"
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan"
  }
}
```

---

## 🎯 服务管理

### Systemd 服务管理

```bash
# 查看状态
openclaw gateway status

# 启动/停止/重启
openclaw gateway start
openclaw gateway stop
openclaw gateway restart

# 直接 systemd 命令
systemctl --user start openclaw-gateway.service
systemctl --user stop openclaw-gateway.service
systemctl --user restart openclaw-gateway.service
```

### 日志查看

```bash
# 实时日志
openclaw logs --follow

# 日志文件位置
tail -f /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log
```

### 健康检查

```bash
# 诊断工具
openclaw doctor
openclaw doctor --fix

# 查看插件
openclaw plugins list

# 查看渠道
openclaw channels list
```

---

## 📦 插件管理

```bash
# 列出插件
openclaw plugins list

# 安装插件
openclaw plugins install <plugin-name>

# 卸载插件
openclaw plugins remove <plugin-name>

# 更新插件
openclaw plugins update <plugin-name>
```

### 已安装插件

| 插件 | 状态 | 版本 |
|------|------|------|
| 企业微信 (wecom-openclaw-plugin) | ✅ loaded | 1.0.5 |
| Memory Core | ✅ loaded | 2026.2.3-1 |
| Qwen OAuth | ✅ loaded | - |

---

## 🧪 测试命令

```bash
# 发送测试消息
openclaw message send --channel wecom --target @崔占山 --message "Hi"

# 使用 TUI 界面
openclaw tui

# 查看模型
openclaw models

# 查看帮助
openclaw --help
openclaw message --help
openclaw cron --help
```

---

## ⏰ 定时任务（Cron）

```bash
# 查看 cron 状态
openclaw cron status
openclaw cron list

# 添加定时任务
openclaw cron add --name <task-name> --cron "<cron-expr>" --message "<message>"

# 管理任务
openclaw cron disable <job-id>
openclaw cron rm <job-id>
```

---

## 🌐 浏览器自动化

```bash
# 启动浏览器
openclaw browser start

# 打开网页
openclaw browser open <URL>

# 截图
openclaw browser screenshot

# 查看帮助
openclaw browser --help
```

### 浏览器配置

```json
{
  "browser": {
    "enabled": true,
    "headless": true,
    "noSandbox": true,
    "defaultProfile": "clawd",
    "profiles": {
      "clawd": {
        "cdpPort": 18800
      }
    }
  }
}
```

---

## 🔍 故障排查

### 常见问题

1. **企业微信未启用**
   ```bash
   openclaw doctor --fix
   openclaw config set channels.wecom.enabled true
   openclaw gateway restart
   ```

2. **插件加载失败**
   ```bash
   # 重新安装插件
   openclaw plugins remove @wecom/wecom-openclaw-plugin
   rm -rf ~/.openclaw/extensions/wecom-openclaw-plugin
   openclaw plugins install @wecom/wecom-openclaw-plugin
   ```

3. **服务无法启动**
   ```bash
   # 查看日志
   openclaw logs --follow
   
   # 检查端口占用
   netstat -tlnp | grep 18789
   
   # 手动启动调试
   openclaw gateway --port 18789
   ```

### 有用的命令

```bash
# 查看运行状态
openclaw status

# 查看仪表盘
openclaw dashboard

# 查看历史命令
history | grep openclaw
```

---

## 📝 工作区文件

```
~/.openclaw/workspace/
├── AGENTS.md          # Agent 行为规范
├── SOUL.md            # 人格定义
├── USER.md            # 用户信息
├── IDENTITY.md        # 身份定义
├── TOOLS.md           # 工具配置笔记
├── HEARTBEAT.md       # 心跳任务
├── BOOTSTRAP.md       # 初始化脚本（已完成可删除）
├── scripts/           # 自定义脚本
├── skills/            # 自定义技能
└── articles/          # 生成的文章
```

---

## 🎯 快速参考

| 操作 | 命令 |
|------|------|
| 重启服务 | `openclaw gateway restart` |
| 查看日志 | `openclaw logs --follow` |
| 诊断修复 | `openclaw doctor --fix` |
| 发送消息 | `openclaw message send --channel wecom --target <用户> --message "内容"` |
| 编辑配置 | `vi ~/.openclaw/openclaw.json` |
| 查看状态 | `openclaw gateway status` |

---

## 📞 支持资源

- 官方文档：https://docs.openclaw.ai
- GitHub: https://github.com/openclaw/openclaw
- 社区 Discord: https://discord.com/invite/clawd
- ClawHub 插件市场：https://clawhub.com

---

**最后更新：** 2026-03-11  
**维护者：** 小布 (AI 助手)
