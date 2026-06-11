import streamlit as st
import requests
import os
import re
from urllib.parse import urlparse

# 配置
SAVE_DIR = "download"
os.makedirs(SAVE_DIR, exist_ok=True)

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

# 过滤非法文件名
def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# 提取 B 站 BV 号
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

# 解析 B 站视频直链
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

        # 获取播放地址（原画质）
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

# ================= Streamlit 页面 =================
st.set_page_config(page_title="B站视频解析下载", layout="wide")
st.title("📺 B站 原画质视频解析下载工具")
st.divider()

url_input = st.text_input("请粘贴 B 站视频链接（支持 b23.tv 短链接）")

if st.button("开始解析", type="primary"):
    link = url_input.strip()
    if not link:
        st.warning("请输入视频链接！")
    else:
        with st.spinner("正在解析视频..."):
            bvid = extract_bvid(link)
            if not bvid:
                st.error("❌ 未识别到有效 B 站链接，请检查链接是否正确")
            else:
                real_url, msg = parse_bilibili(bvid)
                if real_url:
                    st.success(f"✅ {msg}")
                    st.text_input("视频直链", value=real_url, disabled=True)

                    with st.spinner("正在下载视频，请稍候..."):
                        ok, path, fname = download_video(real_url)
                        if ok:
                            st.success(f"🎉 下载完成！文件已保存：{path}")
                        else:
                            st.error(f"❌ 下载失败：{path}")
                else:
                    st.error(f"❌ {msg}")

st.divider()
st.info("温馨提示：本工具仅用于个人学习、本地备份，请勿用于侵权传播。")