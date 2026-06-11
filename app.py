import streamlit as st
import requests
import re

st.set_page_config(page_title="B站解析（防132错误）", layout="centered")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

def extract_bvid(url):
    m = re.search(r"BV[0-9a-zA-Z]+", url)
    return m.group(0) if m else None

def parse(bvid):
    try:
        info = requests.get(f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", headers=HEADERS).json()
        if info["code"] != 0:
            return None, info["message"]
        cid, aid, title = info["data"]["cid"], info["data"]["aid"], info["data"]["title"]
        play = requests.get(f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=80&type=mp4", headers=HEADERS).json()
        if play["code"] != 0:
            return None, play["message"]
        return play["data"]["durl"][0]["url"], title
    except Exception as e:
        return None, str(e)

st.markdown("""
<style>
body {background:#fff; color:#000;}
.stButton>button {background:#2d8cf0; color:#fff; border:none;}
</style>
""", unsafe_allow_html=True)

st.title("📺 B站解析（解决 #132 错误）")
link = st.text_input("粘贴B站链接")
if st.button("解析") and link:
    bvid = extract_bvid(link)
    if not bvid:
        st.error("未识别BV号")
    else:
        url, title = parse(bvid)
        if url:
            st.success(f"✅ {title}")
            st.code(url)
            # 关键：用 JS 带 Referer 打开
            st.markdown(f'''
<a href="{url}" target="_blank" onclick="event.preventDefault(); window.open('{url}', '_blank', 'referrerpolicy=no-referrer-when-downgrade');">
    <button style="background:#2d8cf0;color:white;padding:8px 16px;border:none;border-radius:4px;">
        🔗 一键打开（自动带Referer，防132错误）
    </button>
</a>
''', unsafe_allow_html=True)
            st.info("打开后右键→另存为即可下载")
        else:
            st.error(title)
