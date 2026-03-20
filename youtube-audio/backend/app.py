import os
import re
import tempfile
import time
import requests
import yt_dlp
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

YT_URL_RE = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]{11}"
)

# Cache yt-dlp results for 5 minutes to avoid double extraction on /info + /stream
_info_cache: dict = {}
CACHE_TTL = 300  # seconds


def sanitize_url(url: str) -> str:
    url = url.strip()
    if not YT_URL_RE.match(url):
        raise ValueError("Invalid YouTube URL")
    return url


def _cookies_file():
    """Build a Netscape cookies.txt from env vars and return its path, or None.

    Accepts either:
    - YOUTUBE_COOKIE_HEADER: raw Cookie: header value copied from DevTools
      e.g.  SID=xxx; HSID=yyy; SSID=zzz; ...
    - YOUTUBE_COOKIES: already-formatted Netscape cookies.txt content (legacy)
    """
    header = os.environ.get("YOUTUBE_COOKIE_HEADER", "").strip()
    if header:
        lines = ["# Netscape HTTP Cookie File"]
        for pair in header.split(";"):
            pair = pair.strip()
            if "=" not in pair:
                continue
            name, _, value = pair.partition("=")
            name = name.strip()
            value = value.strip()
            # Write each cookie for both domains so yt-dlp finds SAPISID
            # under .google.com (needed for SAPISIDHASH) and session cookies
            # under .youtube.com
            for domain in (".google.com", ".youtube.com"):
                lines.append(
                    f"{domain}\tTRUE\t/\tTRUE\t9999999999\t{name}\t{value}"
                )
        content = "\n".join(lines) + "\n"
    else:
        content = os.environ.get("YOUTUBE_COOKIES", "").strip()

    if not content:
        return None

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    tmp.write(content)
    tmp.close()
    return tmp.name


def get_audio_info(url: str) -> dict:
    now = time.time()
    if url in _info_cache:
        entry, ts = _info_cache[url]
        if now - ts < CACHE_TTL:
            return entry

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        # Use iOS client — avoids bot-detection on server IPs without cookies
        "extractor_args": {"youtube": {"player_client": ["ios", "web"]}},
    }
    cookies_path = _cookies_file()
    if cookies_path:
        ydl_opts["cookiefile"] = cookies_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        result = {
            "title": info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", ""),
            "stream_url": info["url"],
            "content_type": info.get("ext", "m4a"),
        }
    _info_cache[url] = (result, now)
    return result


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

    # connect_timeout=10s, read_timeout=None (stream can stay open indefinitely)
    upstream = requests.get(stream_url, headers=headers, stream=True, timeout=(10, None))

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
    port_env = os.environ.get("PORT")
    print(f"PORT env var = {port_env!r}", flush=True)
    port = int(port_env) if port_env else 8080
    print(f"Starting on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port, debug=False)
