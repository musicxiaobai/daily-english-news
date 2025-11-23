import os
import time
import hmac
import hashlib
import base64
import requests
import feedparser
from datetime import datetime

# 配置国内新闻源（已验证可用）
RSS_URL = "https://www.i21st.cn/rss/","https://archive.shine.cn/siteinfo/rss.aspx" ,"http://www.chinadaily.com.cn/rss/world_rss.xml" # China Daily国际新闻
MAX_NEWS_ITEMS = 5  # 最多推送新闻数量
DINGTALK_KEYWORD = "新闻"  # 确保包含钉钉机器人关键词

def get_news():
    """获取并解析RSS新闻"""
    try:
        # 添加浏览器请求头，避免被拦截
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        }
        
        # 发送请求并处理编码
        response = requests.get(RSS_URL, headers=headers, timeout=15)
        response.encoding = "utf-8"  # 强制UTF-8编码，避免中文乱码
        
        # 解析RSS
        feed = feedparser.parse(response.text)
        if not feed.entries:
            return f"⚠️ 未获取到新闻内容，请检查RSS链接: {RSS_URL}"
        
        # 提取新闻
        news_list = []
        for i, entry in enumerate(feed.entries[:MAX_NEWS_ITEMS], 1):
            title = entry.get("title", "无标题")
            link = entry.get("link", "#")
            # 处理不同新闻源的发布时间格式差异
            pub_date = entry.get("published", entry.get("pubDate", "未知时间"))
            
            # 确保包含关键词
            if DINGTALK_KEYWORD not in title:
                title = f"{DINGTALK_KEYWORD}：{title}"
                
            news_list.append(f"{i}. [{title}]({link})\n🕒 {pub_date}")
        
        return "\n\n".join(news_list)
        
    except Exception as e:
        return f"❌ 新闻获取失败: {str(e)}"

def send_to_dingtalk(content):
    """发送消息到钉钉"""
    webhook = os.getenv("DINGTALK_WEBHOOK")
    secret = os.getenv("DINGTALK_SECRET")
    
    if not webhook or not secret:
        return "⚠️ 请设置DINGTALK_WEBHOOK和DINGTALK_SECRET环境变量"
    
    # 计算钉钉签名
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    hmac_code = hmac.new(secret_enc, string_to_sign, digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(hmac_code).decode("utf-8")
    
    # 构建请求
    url = f"{webhook}&timestamp={timestamp}&sign={sign}"
    headers = {"Content-Type": "application/json;charset=utf-8"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"{datetime.now().strftime('%Y-%m-%d')} {DINGTALK_KEYWORD}推送",
            "text": content
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("errcode") == 0:
            return "✅ 消息推送成功"
        else:
            return f"❌ 推送失败: {result.get('errmsg')}"
    except Exception as e:
        return f"❌ 请求异常: {str(e)}"

if __name__ == "__main__":
    # 执行流程
    news_content = get_news()
    print(f"新闻内容:\n{news_content}")
    
    # 添加推送结果到内容
    full_content = f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{news_content}\n\n---\n系统状态: {send_to_dingtalk(news_content)}"
    print(full_content)
