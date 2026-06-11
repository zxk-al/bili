import streamlit as st
import requests
import re
from io import BytesIO

# 配置页面
st.set_page_config(
    page_title="B站视频解析下载",
    page_icon="📺",
    layout="centered"
)

# 全局请求头（绕过B站防盗链）
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

# 解析B站视频直链
def parse_bilibili(bvid: str):
    try:
        info_api = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        resp = requests.get(info_api, headers=HEADERS, timeout=15)
        data = resp.json()

        if data.get("code") != 0:
            return None, f"获取视频信息失败：{data.get('message','未知错误')}"

        cid = data["data"]["cid"]
        aid = data["data"]["aid"]
        title = data["data"]["title"]

        # qn=80 原画质
        play_api = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=80&type=mp4"
        play_resp = requests.get(play_api, headers=HEADERS, timeout=15)
        play_data = play_resp.json()

        if play_data.get("code") != 0:
            return None, f"获取播放地址失败：{play_data.get('message','')}"

        video_url = play_data["data"]["durl"][0]["url"]
        return video_url, title
    except Exception as e:
        return None, f"解析异常：{str(e)}"

# ----------------- 页面主体 -----------------
st.markdown("""
<style>
h1 {text-align: center; color: #fb7299;}
</style>
""", unsafe_allow_html=True)

st.title("📺 B站原画质视频解析下载")
st.divider()

# 初始化会话状态
if "video_url" not in st.session_state:
    st.session_state.video_url = ""
if "title" not in st.session_state:
    st.session_state.title = "bilibili_video"

# 输入框
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
        with st.spinner("正在解析视频..."):
            bvid = extract_bvid(link)
            if not bvid:
                st.error("❌ 未识别到有效B站链接")
            else:
                v_url, title = parse_bilibili(bvid)
                if v_url:
                    st.success(f"✅ 解析成功：{title}")
                    st.session_state.video_url = v_url
                    st.session_state.title = re.sub(r'[\\/*?:"<>|]', "", title)  # 清理非法字符
                else:
                    st.error(f"❌ {title}")

# 解析成功后，生成下载按钮（预加载到内存流）
if st.session_state.video_url:
    try:
        with st.spinner("正在准备下载，请稍候..."):
            # 拉取视频流到内存（兼容Streamlit下载按钮）
            resp = requests.get(st.session_state.video_url, stream=True, headers=HEADERS, timeout=120)
            resp.raise_for_status()

            buffer = BytesIO()
            for chunk in resp.iter_content(chunk_size=1024*1024):
                if chunk:
                    buffer.write(chunk)
            buffer.seek(0)

            # 标准下载按钮，不会报错
            st.download_button(
                label="🔽 下载视频",
                data=buffer,
                file_name=f"{st.session_state.title}.mp4",
                mime="video/mp4",
                type="primary",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"❌ 下载准备失败：{str(e)}")

st.divider()
st.info("💡 温馨提示：本工具仅用于个人学习、本地备份，请勿侵权传播视频内容。")
