import streamlit as st
import requests
import re
import base64

# 页面配置
st.set_page_config(
    page_title="B站视频解析下载",
    page_icon="📺",
    layout="centered"
)

# 请求头（必须带Referer，否则403）
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

# 解析直链
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

# 纯白黑字样式
st.markdown("""
<style>
body, .stApp { background: #fff; color: #000; }
.stTextInput>div>div>input { color: #000; background: #fff; }
.stButton>button { background: #fff; border: 1px solid #ddd; color: #000; }
h1, h2, h3 { color: #000; }
</style>
""", unsafe_allow_html=True)

st.title("📺 B站原画质解析（可播可下）")
st.divider()

# 会话状态
if "video_url" not in st.session_state:
    st.session_state.video_url = ""
if "video_name" not in st.session_state:
    st.session_state.video_name = ""

input_url = st.text_input("粘贴B站链接/b23.tv", placeholder="https://www.bilibili.com/video/BVxxxx/")

if st.button("开始解析", type="primary", use_container_width=True):
    link = input_url.strip()
    if not link:
        st.warning("⚠️ 请输入链接")
    else:
        with st.spinner("解析中..."):
            bvid = extract_bvid(link)
            if not bvid:
                st.error("❌ 未识别BV号")
            else:
                v_url, v_name = parse_bilibili(bvid)
                if v_url:
                    st.success(f"✅ {v_name}")
                    st.session_state.video_url = v_url
                    st.session_state.video_name = v_name
                else:
                    st.error(f"❌ {v_name}")

# 解析成功：内嵌播放 + 一键下载
if st.session_state.video_url:
    st.text("🔗 视频直链（5–30分钟有效）：")
    st.code(st.session_state.video_url)

    # 1. 内嵌播放器（带Referer，直接播放）
    st.text("▶️ 在线播放（直接看，无需跳转）：")
    st.video(st.session_state.video_url)  # Streamlit内部请求会带合法Referer

    # 2. 一键下载按钮（Base64触发下载，不跳页）
    try:
        resp = requests.get(st.session_state.video_url, headers=HEADERS, stream=True, timeout=10)
        resp.raise_for_status()
        # 转base64供前端下载
        b64 = base64.b64encode(resp.content).decode()
        href = f'data:video/mp4;base64,{b64}'
        st.markdown(
            f'<a href="{href}" download="{st.session_state.video_name}.mp4" style="display:inline-block;padding:8px 24px;background:#2d8cf0;color:#fff;border-radius:4px;text-decoration:none;margin:10px 0;">⬇️ 一键下载视频</a>',
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"下载准备失败：{str(e)}")

    st.info("💡 提示：直链短期有效，失效请重新解析；禁止侵权传播")

st.divider()
st.info("仅用于个人学习/本地备份，请勿商用")
