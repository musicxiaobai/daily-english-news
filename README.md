![da1c6e4f6eca83b26db47c0bbda9b8d7](https://github.com/user-attachments/assets/697fa38f-cea5-4cb0-a375-6369fff5f514)# daily-english-news README

## 项目概述
本项目是一个自动化英语新闻推送工具，通过GitHub Actions定时任务从**国内可用的英文新闻源**获取最新资讯，并通过钉钉机器人推送到指定群组。解决了国内用户无法直接访问部分海外新闻源的问题，同时提供地道的英语学习材料。

**核心功能**：
- 每日自动抓取权威英文新闻
- 支持多新闻源切换（内置国内可访问链接）
- 定时推送至钉钉群（默认每天早8点）
- 完全基于GitHub免费服务，零服务器成本

**国内可用新闻源**：
- **BBC News 中文网**（推荐）：https://www.bbc.com/zhongwen/simp
- **CNN International**：https://edition.cnn.com/international
- **经济学人Espresso**：https://espresso.economist.com
- **路透社中文网**：https://cn.reuters.com

## 安装步骤

### 环境要求
- Python 3.8+
- Git
- GitHub账号
- 钉钉账号

### 本地开发环境搭建
1. **克隆仓库**
```bash
   git clone https://github.com/your-username/daily-english-news.git
   cd daily-english-news
```

2. **安装依赖**
```bash
   pip install -r requirements.txt
```

3. **配置环境变量**  
创建`.env`文件，添加以下内容：
```ini
   DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
   DINGTALK_SECRET=YOUR_SECRET
   NEWS_SOURCE=https://www.bbc.com/zhongwen/simp
```

## 配置说明

### 必要环境变量
| 变量名 | 说明 | 获取方式 |
|--------|------|----------|
| `DINGTALK_WEBHOOK` | 钉钉机器人Webhook地址 | 钉钉群设置 → 智能群助手 → 自定义机器人 → 复制Webhook |
| `DINGTALK_SECRET` | 钉钉机器人加签密钥 | 创建机器人时选择"加签"获取，若使用关键词模式可不填 |
| `NEWS_SOURCE` | 新闻源URL（国内可访问） | 可使用内置选项：BBC中文网/CNN国际版/路透社中文网 |

### 新闻源配置示例
```python
# 支持的新闻源配置（在news_dingtalk_pusher.py中修改）
NEWS_SOURCES = {
    "bbc_chinese": "https://www.bbc.com/zhongwen/simp",
    "cnn_international": "https://edition.cnn.com/international",
    "reuters_chinese": "https://cn.reuters.com"
}
```

### GitHub Actions配置
工作流文件路径：`.github/workflows/daily_news_workflow.yml`
```yaml
name: Daily English News Push

on:
  schedule:
    - cron: '0 0 * * *'  # UTC时间0点（北京时间8点）执行
  workflow_dispatch:  # 允许手动触发

jobs:
  push_news:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run news pusher
        env:
          DINGTALK_WEBHOOK: ${{ secrets.DINGTALK_WEBHOOK }}
          DINGTALK_SECRET: ${{ secrets.DINGTALK_SECRET }}
          NEWS_SOURCE: ${{ secrets.NEWS_SOURCE || 'https://www.bbc.com/zhongwen/simp' }}
        run: python news_dingtalk_pusher.py
```

## 使用方法

### 本地手动运行
```bash
# 直接运行推送脚本
python news_dingtalk_pusher.py

# 指定新闻源运行
python news_dingtalk_pusher.py --source https://edition.cnn.com/international
```

### GitHub自动部署流程
1. **Fork本仓库**  
访问 [GitHub仓库地址](https://github.com/your-username/daily-english-news) 点击"Fork"

2. **配置Secrets**  
在仓库页面依次点击：  
**Settings → Secrets and variables → Actions → New repository secret**  
添加以下 secrets：
- `DINGTALK_WEBHOOK`: 钉钉机器人Webhook完整地址
- `DINGTALK_SECRET`: 钉钉机器人加签密钥
- `NEWS_SOURCE`: 可选，指定新闻源URL

3. **启用工作流**  
进入 **Actions** 标签，点击左侧工作流名称，启用自动运行

4. **验证结果**
- 每天北京时间8点自动推送新闻
- 可在Actions页面手动触发测试：  
**Run workflow → 选择分支 → Run workflow**

## 故障排除

### 工作流执行失败
| 错误类型 | 可能原因 | 解决方案 |
|----------|----------|----------|
| `403 Forbidden` | 钉钉Webhook或密钥错误 | 重新检查Secrets配置，确保Webhook包含完整URL |
| `News fetch failed` | 新闻源链接不可访问 | 更换为国内可访问源（如BBC中文网），检查网络代理设置 |
| `No module named 'xxx'` | 依赖包未安装 | 确保requirements.txt包含所有依赖，或在工作流中添加`pip install`步骤 |

### 钉钉消息接收问题
1. **安全设置冲突**
   - 若使用"关键词"安全设置，确保新闻内容包含对应关键词
   - 切换为"加签"模式可避免关键词限制（推荐）

2. **消息格式错误**  
检查脚本中消息构造部分是否符合钉钉要求：
```python
   # 正确的Markdown消息格式
   {
       "msgtype": "markdown",
       "markdown": {
           "title": "每日英语新闻",
           "text": "### 今日头条\n- [标题](链接)"
       }
   }
```

3. **网络访问限制**  
GitHub Actions服务器可能无法访问部分国内网站，推荐使用：
   - BBC中文网（https://www.bbc.com/zhongwen/simp）
   - 路透社中文网（https://cn.reuters.com）

### 新闻源切换指南
1. 访问 [项目设置Secrets](https://github.com/your-username/daily-english-news/settings/secrets/actions)
2. 添加或修改 `NEWS_SOURCE` 变量，值为目标新闻源URL
3. 手动触发工作流测试效果

## 常见问题

### Q: 为什么选择GitHub Actions而不是其他定时任务服务？
A: 完全免费且无需服务器维护，适合个人或小团队使用。GitHub提供每月2000分钟免费运行时间，本项目每天仅需1-2分钟。

### Q: 如何修改推送时间？
A: 修改工作流文件中的cron表达式，格式为`分 时 日 月 周`（UTC时间）：
```yaml
   # 北京时间早上7点推送（UTC时间23点）
   - cron: '0 23 * * *'
```

### Q: 新闻内容能否自定义格式？
A: 可以修改`news_dingtalk_pusher.py`中的`format_news`函数，支持Markdown格式：
```python
   def format_news(articles):
       text = "### 今日英语新闻\n\n"
       for idx, article in enumerate(articles[:5]):  # 只取前5条
           text += f"{idx+1}. [{article['title']}]({article['link']})\n\n"
       return text
```

### Q: 国内还有哪些可用的英文新闻源？
A: 推荐：
- **南华早报**：https://www.scmp.com
- **联合早报**：https://www.zaobao.com
- **China Daily**：https://www.chinadaily.com.cn

## 许可证
本项目采用MIT许可证 - 详情参见 [LICENSE](LICENSE) 文件

## 致谢
- 新闻源数据来自各媒体公开RSS Feed
- 定时任务基于GitHub Actions实现
- 消息推送使用钉钉开放平台API

- 支持方式：
- ![da1c6e4f6eca83b26db47c0bbda9b8d7](https://github.com/user-attachments/assets/678644c8-5c12-41da-9e05-67365a39db6a)
