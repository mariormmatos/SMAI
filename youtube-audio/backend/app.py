import os
import re
import requests
import yt_dlp
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

YT_URL_RE = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}"
)


def sanitize_url(url: str) -> str:
    url = url.strip()
    if not YT_URL_RE.match(url):
        raise ValueError("Invalid YouTube URL")
    return url


def get_audio_info(url: str) -> dict:
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", ""),
            "stream_url": info["url"],
            "content_type": info.get("ext", "m4a"),
        }


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/info")
def info():
    url = request.args.get("url", "")
    try:
        url = sanitize_url(url)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        data = get_audio_info(url)
        # Don't expose internal stream_url — client uses /stream endpoint
        return jsonify({
            "title": data["title"],
            "thumbnail": data["thumbnail"],
            "duration": data["duration"],
            "uploader": data["uploader"],
        })
    except Exception as e:
        return jsonify({"error": f"Could not fetch video info: {str(e)}"}), 500


@app.route("/stream")
def stream():
    url = request.args.get("url", "")
    try:
        url = sanitize_url(url)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        data = get_audio_info(url)
        stream_url = data["stream_url"]
        ext = data["content_type"]
        content_type_map = {
            "m4a": "audio/mp4",
            "webm": "audio/webm",
            "mp3": "audio/mpeg",
            "ogg": "audio/ogg",
        }
        mime = content_type_map.get(ext, "audio/mp4")
    except Exception as e:
        return jsonify({"error": f"Could not resolve stream: {str(e)}"}), 500

    # Forward range requests for seeking support
    range_header = request.headers.get("Range", None)
    headers = {"User-Agent": "Mozilla/5.0"}
    if range_header:
        headers["Range"] = range_header

    upstream = requests.get(stream_url, headers=headers, stream=True, timeout=30)

    response_headers = {
        "Content-Type": mime,
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-cache",
    }
    if "Content-Length" in upstream.headers:
        response_headers["Content-Length"] = upstream.headers["Content-Length"]
    if "Content-Range" in upstream.headers:
        response_headers["Content-Range"] = upstream.headers["Content-Range"]

    status_code = upstream.status_code

    def generate():
        for chunk in upstream.iter_content(chunk_size=65536):
            if chunk:
                yield chunk

    return Response(
        stream_with_context(generate()),
        status=status_code,
        headers=response_headers,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
