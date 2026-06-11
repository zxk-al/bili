import streamlit as st
import requests
import re

# 页面基础配置
st.set_page_config(
    page_title="B站视频解析下载",
    page_icon="📺",
    layout="centered"
)

# 请求头（绕过B站防盗链）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

# 提取BV号
def extract_bvid(url: str):
    patterns = [
        r'BV[0-9a-zA-Z]+',
        r'bilibili\.com/video/(BV[0-9a-zA-Z]+)',
        r'b23\.tv/([0-9a-zA-Z]+)'
    ]
    for pat in patterns:
        match = re.search(pat, url)
        if match:
            return match.group(0)
    return None

# 解析视频直链（仅获取地址，不下载）
def parse_bilibili(bvid: str):
    try:
        info_api = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        resp = requests.get(info_api, headers=HEADERS, timeout=10)
        data = resp.json()

        if data.get("code") != 0:
            return None, f"获取信息失败：{data.get('message','未知错误')}"

        cid = data["data"]["cid"]
        aid = data["data"]["aid"]
        title = data["data"]["title"]
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)

        play_api = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=80&type=mp4"
        play_resp = requests.get(play_api, headers=HEADERS, timeout=10)
        play_data = play_resp.json()

        if play_data.get("code") != 0:
            return None, f"获取播放地址失败：{play_data.get('message','')}"

        video_url = play_data["data"]["durl"][0]["url"]
        return video_url, safe_title
    except Exception as e:
        return None, f"解析异常：{str(e)}"

# 纯白背景 + 黑色字体 样式
st.markdown("""
<style>
body, .stApp, .css-18e3th9, .css-1lcbmhc, .css-1d391kg {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}
.stTextInput > div > div > input {
    color: #000000 !important;
    background-color: #FFFFFF !important;
}
.stTextInput > div > div > input::placeholder {
    color: #444444 !important;
}
.stButton > button {
    background-color: #FFFFFF !important;
    border-color: #E0E0E0 !important;
    color: #000000 !important;
}
h1, h2, h3, h4, h5, h6 {
    color: #000000 !important;
}
.stInfo, .stWarning, .stSuccess, .stError {
    color: #000000 !important;
}
.stCode > div {
    background-color: #f8f8f8 !important;
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# 页面主体
st.title("📺 B站原画质视频解析下载")
st.divider()

# 会话状态
if "video_url" not in st.session_state:
    st.session_state.video_url = ""
if "video_name" not in st.session_state:
    st.session_state.video_name = ""

# 链接输入
input_url = st.text_input(
    "粘贴B站链接 / b23.tv 短链接",
    placeholder="https://www.bilibili.com/video/BVxxxx/"
)

# 解析按钮
if st.button("开始解析", type="primary", use_container_width=True):
    link = input_url.strip()
    if not link:
        st.warning("⚠️ 请输入视频链接")
    else:
        with st.spinner("正在解析..."):
            bvid = extract_bvid(link)
            if not bvid:
                st.error("❌ 未识别到有效B站链接")
            else:
                v_url, v_name = parse_bilibili(bvid)
                if v_url:
                    st.success(f"✅ 解析成功：{v_name}")
                    st.session_state.video_url = v_url
                    st.session_state.video_name = v_name
                else:
                    st.error(f"❌ {v_name}")

# 展示直链 + 下载指引
if st.session_state.video_url:
    st.text("视频直链（复制后浏览器打开下载）：")
    st.code(st.session_state.video_url)
    st.info("💡 使用方法：复制上方链接 → 浏览器新标签页打开 → 右键「另存为」即可高速下载")

st.divider()
st.info("温馨提示：本工具仅用于个人学习、本地备份，请勿侵权传播视频内容。")
