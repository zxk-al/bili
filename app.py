import streamlit as st
import requests
import re

# 全局请求头，解决B站防盗链 403
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

# 提取B站 BV 号（支持标准链接 + b23.tv 短链接）
def extract_bvid(url: str) -> str | None:
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

# 解析B站视频，获取原画质播放直链
def parse_bilibili(bvid: str) -> tuple[str | None, str]:
    try:
        # 获取视频基础信息
        info_api = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        resp = requests.get(info_api, headers=HEADERS, timeout=15)
        data = resp.json()

        if data.get("code") != 0:
            return None, f"获取视频信息失败：{data.get('message', '未知错误')}"

        cid = data["data"]["cid"]
        aid = data["data"]["aid"]
        title = data["data"]["title"]

        # qn=80 代表高清原画质
        play_api = f"https://api.bilibili.com/x/player/playurl?avid={aid}&cid={cid}&qn=80&type=mp4"
        play_resp = requests.get(play_api, headers=HEADERS, timeout=15)
        play_data = play_resp.json()

        if play_data.get("code") != 0:
            return None, f"获取播放地址失败：{play_data.get('message', '未知错误')}"

        video_url = play_data["data"]["durl"][0]["url"]
        return video_url, f"解析成功：{title}"

    except Exception as e:
        return None, f"解析异常：{str(e)}"

# ===================== Streamlit 页面布局 & 样式 =====================
st.set_page_config(
    page_title="B站视频解析下载",
    page_icon="📺",
    layout="centered"
)

# 自定义CSS美化界面
st.markdown("""
<style>
.main {
    background-color: #f7f8fa;
}
.stTextInput > div > div > input {
    font-size: 16px;
    padding: 8px 12px;
}
h1 {
    text-align: center;
    color: #fb7299;
}
.download-btn a {
    display: inline-block;
    padding: 8px 20px;
    background-color: #00b42a;
    color: white !important;
    text-decoration: none;
    border-radius: 6px;
    font-weight: bold;
}
.download-btn a:hover {
    background-color: #009c22;
}
</style>
""", unsafe_allow_html=True)

# 页面标题
st.title("📺 B站原画质视频解析下载工具")
st.divider()

# 输入框
video_link = st.text_input(
    label="请粘贴B站视频链接 / b23.tv 短链接",
    placeholder="示例：https://www.bilibili.com/video/BV1xxxx/"
)

# 解析按钮
parse_btn = st.button("开始解析", type="primary", use_container_width=True)

# 解析逻辑
if parse_btn:
    link = video_link.strip()
    if not link:
        st.warning("⚠️ 请输入有效的视频链接！")
    else:
        with st.spinner("正在解析视频地址，请稍候..."):
            bvid = extract_bvid(link)
            if not bvid:
                st.error("❌ 未识别到有效B站链接，请检查链接格式")
            else:
                video_url, msg = parse_bilibili(bvid)
                if video_url:
                    st.success(f"✅ {msg}")
                    st.text_input("视频直链（可复制）", value=video_url, disabled=True)
                    
                    # 生成浏览器原生下载链接，客户端直接下载
                    st.markdown(
                        f'<div class="download-btn"><a href="{video_url}" download="bilibili_video.mp4">🔽 点击此处浏览器下载视频</a></div>',
                        unsafe_allow_html=True
                    )
                    st.info("提示：点击上方按钮，将由你的浏览器自动弹出下载窗口")
                else:
                    st.error(f"❌ {msg}")

st.divider()
st.info("💡 温馨提示：本工具仅用于个人学习、本地备份，请勿侵权传播视频内容。")
