import feedparser
import requests
import time
import hmac
import hashlib
import base64
import os

def get_bbc_news(rss_url):
    """从BBC RSS Feed获取新闻"""
    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo != 0:
            print(f"RSS解析错误: {feed.bozo_exception}")
            return []
            
        news_items = []
        for entry in feed.entries[:5]:  # 获取最新5条新闻
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.get("published", "未知时间")
            })
        return news_items
    except Exception as e:
        print(f"获取新闻失败: {str(e)}")
        return []

def send_to_dingtalk(webhook, secret, news_items):
    """发送新闻到钉钉群"""
    if not news_items:
        print("没有可发送的新闻内容")
        return False
        
    # 构建消息内容
    message = "📰 今日BBC英语新闻:\n\n"
    for i, item in enumerate(news_items, 1):
        message += f"{i}. [{item['title']}]({item['link']})\n\n"
    
    # 计算签名
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f"{timestamp}\n{secret}".encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    
    # 发送请求
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "text",
        "text": {"content": message}
    }
    
    try:
        response = requests.post(
            f"{webhook}&timestamp={timestamp}&sign={sign}",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        if result.get("errcode") == 0:
            print("消息发送成功")
            return True
        else:
            print(f"消息发送失败: {result.get('errmsg')}")
            return False
    except Exception as e:
        print(f"发送请求失败: {str(e)}")
        return False

def main():
    # 从环境变量获取配置
    rss_url = "https://www.bbc.com/news/rss.xml"  # BBC新闻RSS Feed
    webhook = os.getenv("DINGTALK_WEBHOOK")
    secret = os.getenv("DINGTALK_SECRET")
    
    if not all([webhook, secret]):
        print("请设置DINGTALK_WEBHOOK和DINGTALK_SECRET环境变量")
        return
    
    # 获取新闻
    news_items = get_bbc_news(rss_url)
    if not news_items:
        return
        
    # 发送到钉钉
    send_to_dingtalk(webhook, secret, news_items)

if __name__ == "__main__":
    main()