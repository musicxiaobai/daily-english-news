import os
import time
import hmac
import hashlib
import base64
import requests
import feedparser
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 配置参数 ====================
BBC_RSS_URL = "https://feeds.bbci.co.uk/news/rss.xml"
MAX_NEWS_ITEMS = 5
ARCHIVE_DIR = "news_archive"
REPO_OWNER = os.getenv("REPO_OWNER", "musicxiaobai")  # 替换为你的GitHub用户名
REPO_NAME = os.getenv("REPO_NAME", "daily-english-news")  # 替换为你的仓库名
DINGTALK_KEYWORD = "BBC新闻"
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET")

# ==================== 目录初始化 ====================
# 确保存档目录存在并输出调试信息
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)
    print(f"[DEBUG] 创建存档目录: {os.path.abspath(ARCHIVE_DIR)}")
else:
    print(f"[DEBUG] 存档目录已存在: {os.path.abspath(ARCHIVE_DIR)}")

# ==================== 核心函数 ====================
def get_bbc_news():
    try:
        response = requests.get(BBC_RSS_URL, timeout=15)
        response.encoding = "utf-8"
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            return None, "未获取到BBC新闻内容"
        
        today = datetime.now().strftime("%Y-%m-%d")
        archive_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/main/{ARCHIVE_DIR}/{today}.md"
        
        md_content = f"# {DINGTALK_KEYWORD} ({today})\n\n"
        for i, entry in enumerate(feed.entries[:MAX_NEWS_ITEMS], 1):
            md_content += f"## {i}. {entry.title}\n\n"
            md_content += f"{entry.summary}\n\n"
            md_content += f"[国内阅读存档]({archive_url}) | 原始链接：{entry.link}\n\n---\n\n"
        
        return md_content, None
        
    except Exception as e:
        return None, f"获取失败: {str(e)}"

def save_news_to_github(content):
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(ARCHIVE_DIR, f"{today}.md")
    
    # 保存文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    # 验证文件是否存在
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"[DEBUG] 存档文件生成成功: {file_path} (大小: {file_size} bytes)")
        return "updated"
    else:
        print(f"[DEBUG] 存档文件生成失败: {file_path}")
        return "failed"

def send_to_dingtalk(content):
    if not DINGTALK_WEBHOOK or not DINGTALK_SECRET:
        return "错误：未配置环境变量"
    
    timestamp = str(round(time.time() * 1000))
    secret_enc = DINGTALK_SECRET.encode("utf-8")
    string_to_sign = f"{timestamp}\n{DINGTALK_SECRET}".encode("utf-8")
    sign = base64.b64encode(hmac.new(secret_enc, string_to_sign, digestmod=hashlib.sha256).digest()).decode()
    
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"{DINGTALK_KEYWORD} {datetime.now().strftime('%Y-%m-%d')}",
            "text": content[:3000]
        }
    }
    
    try:
        response = requests.post(
            f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}",
            json=data,
            headers=headers,
            timeout=10
        )
        return f"推送成功（状态码：{response.status_code}）"
    except Exception as e:
        return f"推送失败: {str(e)}"

# ==================== 主流程 ====================
if __name__ == "__main__":
    print(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始执行 =====")
    
    news_content, error = get_bbc_news()
    if error:
        print(f"新闻获取失败: {error}")
        send_to_dingtalk(f"⚠️ {error}")
        exit(1)
    
    save_result = save_news_to_github(news_content)
    if save_result == "failed":
        print("存档文件生成失败")
        exit(1)
    elif save_result == "unchanged":
        print("新闻内容未更新，无需推送")
        exit(0)
    
    send_result = send_to_dingtalk(news_content)
    print(f"推送结果: {send_result}")
    print(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 执行结束 =====")
