from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
import re


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/108.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

# 提取视频 ID
def extract_id(url: str):
    # 提取 BVID
    m = re.search(r"BV[0-9A-Za-z]+", url)
    if m:
        return {"type": "bvid", "id": m.group(0)}
    # 提取 AV 号
    m2 = re.search(r"av(\d+)", url)
    if m2:
        return {"type": "aid", "id": m2.group(1)}
    # 短链处理
    if "b23.tv" in url:
        try:
            # 使用定义的请求头处理短链接跳转
            r = requests.get(url, allow_redirects=True, timeout=8, headers=headers)
            return extract_id(r.url)
        except Exception:
            return None
    return None


@app.get("/api/info")
def info(url: str = Query(..., description="B站视频链接")):
    parsed = extract_id(url)
    if not parsed:
        raise HTTPException(status_code=400, detail=f"无法提取视频 ID: {url}")

    api = "https://api.bilibili.com/x/web-interface/view"
    params = {parsed["type"]: parsed["id"]}
    # 使用请求头获取视频信息
    r = requests.get(api, params=params, timeout=8, headers=headers)

    try:
        j = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail="B站 API 响应异常")

    if j.get("code") != 0:
        raise HTTPException(status_code=502, detail=f"view 接口错误: {j.get('message')}")

    data = j["data"]
    title = data.get("title")
    bvid = data.get("bvid")
    pages = data.get("pages", [])
    if not pages:
        raise HTTPException(status_code=502, detail="未找到视频页")

    # 返回所有分 P 信息
    parts = [{"cid": p["cid"], "part": p["part"]} for p in pages]

    return {"title": title, "bvid": bvid, "parts": parts}


@app.get("/api/playurl")
def playurl(bvid: str, cid: int, qn: int = 80):
    """获取视频播放直链，qn: 清晰度(16=360p,32=480p,64=720p,80=1080p,116=1080p+)"""
    play_api = "https://api.bilibili.com/x/player/playurl"
    params = {"bvid": bvid, "cid": cid, "qn": qn, "otype": "json"}
    # 使用请求头获取播放链接
    r = requests.get(play_api, params=params, timeout=8, headers=headers)
    pj = r.json()
    if pj.get("code") != 0:
        raise HTTPException(status_code=502, detail=f"playurl 接口错误: {pj.get('message')}")

    play_data = pj.get("data", {})
    urls = []
    if play_data.get("durl"):
        urls = [d.get("url") for d in play_data["durl"] if d.get("url")]
    elif play_data.get("dash"):
        videos = play_data["dash"].get("video", [])
        if videos:
            urls.append(videos[0].get("baseUrl"))
    return {"urls": urls}


@app.get("/api/download")
def download(bvid: str, cid: int, qn: int = 80):
    try:
        play = playurl(bvid, cid, qn)
        if not play["urls"]:
            raise HTTPException(status_code=502, detail="未找到下载链接（可能需要登录 Cookie）")

        play_url = play["urls"][0]

        # 重新定义本地请求头（避免和全局 headers 冲突）
        dl_headers = {
            "User-Agent": headers["User-Agent"],
            "Referer": headers["Referer"],
        }

        r = requests.get(play_url, stream=True, timeout=30, headers=dl_headers)

        def iter_stream():
            try:
                for chunk in r.iter_content(1024 * 64):
                    if chunk:
                        yield chunk
            finally:
                r.close()

        return StreamingResponse(
            iter_stream(),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename=\"{bvid}_{cid}.mp4\"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

