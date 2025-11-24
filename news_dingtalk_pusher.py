import os
import time
import hmac
import hashlib
import base64
import requests
import feedparser
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量（本地开发用）
load_dotenv()

# 配置
BBC_RSS_URL = "https://feeds.bbci.co.uk/news/rss.xml"  # BBC国际新闻RSS
ARCHIVE_DIR = "news_archive"  # 存档目录名
MAX_NEWS_ITEMS = 5  # 最大新闻数量
DINGTALK_KEYWORD = "BBC新闻"  # 钉钉消息关键词

# 创建存档目录
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def get_bbc_news():
    """从BBC RSS获取新闻"""
    try:
        # 使用GitHub Actions海外IP直接访问
        response = requests.get(BBC_RSS_URL, timeout=15)
        response.encoding = "utf-8"
        
        feed = feedparser.parse(response.text)
        if not feed.entries:
            return None, "未获取到BBC新闻内容"
        
        # 解析新闻条目
        news_list = []
        for i, entry in enumerate(feed.entries[:MAX_NEWS_ITEMS], 1):
            news_list.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "summary": entry.summary
            })
        
        # 生成Markdown内容
        md_content = f"# {DINGTALK_KEYWORD} ({datetime.now().strftime('%Y-%m-%d')})\n\n"
        for item in news_list:
            md_content += f"## {item['title']}\n\n"
            md_content += f"{item['summary']}\n\n"
            md_content += f"[阅读原文]({item['link']}) | 发布时间：{item['published']}\n\n---\n\n"
        
        return md_content, None
        
    except Exception as e:
        return None, f"获取失败: {str(e)}"

def save_news_to_github(content):
    """保存新闻到GitHub仓库"""
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(ARCHIVE_DIR, f"{today}.md")
    
    # 检查文件是否已存在且内容相同
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            if f.read() == content:
                return "unchanged"  # 内容未变化
    
    # 保存新内容
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return "updated"  # 内容已更新

def send_to_dingtalk(content):
    """发送到钉钉机器人"""
    webhook = os.getenv("DINGTALK_WEBHOOK")
    secret = os.getenv("DINGTALK_SECRET")
    
    if not webhook or not secret:
        return "环境变量未配置"
    
    # 计算签名
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    sign = base64.b64encode(hmac.new(secret_enc, string_to_sign, hashlib.sha256).digest()).decode()
    
    # 发送请求
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"{DINGTALK_KEYWORD} {datetime.now().strftime('%Y-%m-%d')}",
            "text": content[:3000]  # 钉钉消息长度限制
        }
    }
    
    try:
        response = requests.post(
            f"{webhook}&timestamp={timestamp}&sign={sign}",
            json=data,
            headers=headers,
            timeout=10
        )
        return f"推送成功: {response.json()}"
    except Exception as e:
        return f"推送失败: {str(e)}"

if __name__ == "__main__":
    # 主流程
    news_content, error = get_bbc_news()
    if error:
        print(f"新闻获取错误: {error}")
        send_to_dingtalk(f"⚠️ {error}")
        exit(1)
    
    # 存档新闻
    save_result = save_news_to_github(news_content)
    if save_result == "unchanged":
        print("新闻内容未更新，无需推送")
        exit(0)
    
    # 推送消息
    send_result = send_to_dingtalk(news_content)
    print(f"推送结果: {send_result}")
