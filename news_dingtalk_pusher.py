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
# 1. 新闻源配置
BBC_RSS_URL = "https://feeds.bbci.co.uk/news/rss.xml"  # BBC国际新闻RSS
MAX_NEWS_ITEMS = 5  # 最大新闻数量

# 2. 存档配置
ARCHIVE_DIR = "news_archive"  # 存档目录名
REPO_OWNER = os.getenv("REPO_OWNER", "musicxiaobai")  # 替换GITHUB_USER
REPO_NAME = os.getenv("REPO_NAME", "daily-english-news")  # 替换GITHUB_REPO

# 3. 钉钉配置
DINGTALK_KEYWORD = "BBC新闻"  # 钉钉消息关键词（需与机器人安全设置匹配）
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET")

# 创建存档目录
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# ==================== 核心函数 ====================
def get_bbc_news():
    """从BBC RSS获取新闻并生成Markdown内容"""
    try:
        # 获取BBC新闻
        response = requests.get(BBC_RSS_URL, timeout=15)
        response.encoding = "utf-8"
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            return None, "未获取到BBC新闻内容"
        
        # 生成GitHub存档链接
        today = datetime.now().strftime("%Y-%m-%d")
        archive_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/main/{ARCHIVE_DIR}/{today}.md"
        
        # 生成Markdown内容
        md_content = f"# {DINGTALK_KEYWORD} ({today})\n\n"
        for i, entry in enumerate(feed.entries[:MAX_NEWS_ITEMS], 1):
            md_content += f"## {i}. {entry.title}\n\n"
            md_content += f"{entry.summary}\n\n"
            md_content += f"[国内阅读存档]({archive_url}) | 原始链接：{entry.link}\n\n"
            md_content += f"发布时间：{entry.published}\n\n---\n\n"
        
        return md_content, None
        
    except Exception as e:
        return None, f"获取失败: {str(e)}"

def save_news_to_github(content):
    """保存新闻到GitHub仓库（去重逻辑）"""
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
    """发送Markdown内容到钉钉机器人"""
    if not DINGTALK_WEBHOOK or not DINGTALK_SECRET:
        return "错误：未配置DINGTALK_WEBHOOK或DINGTALK_SECRET"
    
    # 计算钉钉签名
    timestamp = str(round(time.time() * 1000))
    secret_enc = DINGTALK_SECRET.encode("utf-8")
    string_to_sign = f"{timestamp}\n{DINGTALK_SECRET}".encode("utf-8")
    sign = base64.b64encode(hmac.new(secret_enc, string_to_sign, digestmod=hashlib.sha256).digest()).decode()
    
    # 构建请求
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"{DINGTALK_KEYWORD} {datetime.now().strftime('%Y-%m-%d')}",
            "text": content[:3000]  # 钉钉消息长度限制（最大3000字符）
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
    
    # 1. 获取BBC新闻
    news_content, error = get_bbc_news()
    if error:
        print(f"新闻获取失败: {error}")
        send_to_dingtalk(f"⚠️ {DINGTALK_KEYWORD}获取失败：{error}")
        exit(1)
    
    # 2. 存档新闻到GitHub
    save_result = save_news_to_github(news_content)
    if save_result == "unchanged":
        print("新闻内容未更新，无需推送")
        exit(0)
    print("新闻已存档到GitHub仓库")
    
    # 3. 推送新闻到钉钉
    send_result = send_to_dingtalk(news_content)
    print(f"推送结果: {send_result}")
    
    print(f"===== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 执行结束 =====")
