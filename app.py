import streamlit as st
import requests
import os
import re
from urllib.parse import urlparse

# 基础配置
SAVE_DIR = "download"
os.makedirs(SAVE_DIR, exist_ok=True)

# 请求头（解决B站防盗链）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

# 清理非法文件名
def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# 提取B站 BV 号
def extract_bvid(url):
    patterns = [
        r'BV[0-9a-zA-Z]+',
        r'bilibili\.com/video/(BV[0-9a-zA-Z]+)',
        r'b23\.tv/([0-9a-zA-Z]+)'
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(0)
    return None

# 解析B站视频
def parse_bilibili(bvid):
    try:
        info_api = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        resp = requests.get(info_api, headers=HEADERS, timeout=15)
        data = resp.json()

        if data.get("code") != 0:
            return None, f"获取视频信息失败：{data.get('message','未知错误')}"

        cid = data["data"]["cid"]
        aid = data["data"]["aid"]
        title = data["data"]["title"]

        # 80 = 高清原画质
        play_api = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=80&type=mp4"
        play_resp = requests.get(play_api, headers=HEADERS, timeout=15)
        play_data = play_resp.json()

        if play_data.get("code") != 0:
            return None, f"获取播放地址失败：{play_data.get('message','未知错误')}"

        video_url = play_data["data"]["durl"][0]["url"]
        return video_url, f"解析成功：{title}"
    except Exception as e:
        return None, f"解析异常：{str(e)}"

# 下载视频
def download_video(video_url):
    try:
        stream = requests.get(video_url, stream=True, headers=HEADERS, timeout=60)
        stream.raise_for_status()

        file_name = safe_filename(os.path.basename(urlparse(video_url).path))
        if not file_name.endswith(".mp4"):
            file_name = f"bilibili_video_{len(os.listdir(SAVE_DIR))}.mp4"
        save_path = os.path.join(SAVE_DIR, file_name)

        with open(save_path, "wb") as f:
            for chunk in stream.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
        return True, save_path, file_name
    except Exception as e:
        return False, str(e), ""

# ========== Streamlit 页面样式 & 布局 ==========
st.set_page_config(
    page_title="B站视频下载工具",
    page_icon="📺",
    layout="centered"
)

# 自定义 CSS 美化（模拟 HTML 网页风格）
st.markdown("""
<style>
.main {
    background-color: #f7f8fa;
}
.stTextInput > div > div > input {
    font-size: 16px;
    padding: 10px;
}
h1 {
    text-align: center;
    color: #fb7299;
}
</style>
""", unsafe_allow_html=True)

# 页面主体
st.title("📺 B站原画质视频解析下载")
st.markdown("---")

url = st.text_input("请粘贴 B站链接 / b23.tv 短链接", placeholder="例如：https://www.bilibili.com/video/BVxxxx/")

col1, col2 = st.columns([1, 1])
with col1:
    parse_btn = st.button("开始解析", type="primary", use_container_width=True)

# 状态变量
if "real_url" not in st.session_state:
    st.session_state.real_url = ""

if parse_btn:
    link = url.strip()
    if not link:
        st.warning("⚠️ 请输入视频链接")
    else:
        with st.spinner("正在解析视频..."):
            bvid = extract_bvid(link)
            if not bvid:
                st.error("❌ 未识别到有效B站链接，请检查")
            else:
                real_url, msg = parse_bilibili(bvid)
                if real_url:
                    st.success(f"✅ {msg}")
                    st.session_state.real_url = real_url
                    st.text_input("视频直链（可复制）", value=real_url, disabled=True)

                    # 自动开始下载
                    with st.spinner("正在下载视频..."):
                        ok, path, fname = download_video(real_url)
                        if ok:
                            st.success(f"🎉 下载完成！文件路径：{path}")
                        else:
                            st.error(f"❌ 下载失败：{path}")
                else:
                    st.error(f"❌ {msg}")

st.markdown("---")
st.info("💡 温馨提示：仅用于个人学习与本地备份，请勿侵权传播视频内容。")
