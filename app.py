import os
import sys

# Ensure UTF-8 encoding for stdout/stderr on Windows to prevent UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import time
import uuid
import threading
import subprocess
import traceback
from flask import Flask, request, jsonify, send_from_directory
import yt_dlp

try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_PATH = None

app = Flask(__name__, static_folder='static', static_url_path='')

# Target download directory: support both Local Windows & Cloud Containers (Railway/Docker)
WINDOWS_DEFAULT = r'C:\Users\Hello\Downloads\wordpress\vid-downloader'
if os.name == 'nt' and os.path.exists(WINDOWS_DEFAULT):
    BASE_DIR = WINDOWS_DEFAULT
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_DIR = os.path.join(BASE_DIR, 'Downloaded_Videos')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory database of downloads
# Structure: { task_id: { id, url, title, thumbnail, status, progress, speed, eta, total_size, filepath, error, format_id, time } }
downloads = {}


def get_base_ydl_opts():
    """Returns base yt-dlp options configured to bypass YouTube cloud datacenter bot detection."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'socket_timeout': 15,
        # Bypass YouTube bot detection on cloud servers (Railway/Render) by spoofing mobile/TV clients
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web_creator', 'tvembedded'],
            }
        },
    }
    if FFMPEG_PATH:
        opts['ffmpeg_location'] = FFMPEG_PATH
    return opts


@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/api/info', methods=['POST'])
def get_video_info():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'Please provide a valid video URL.'}), 400

    ydl_opts = get_base_ydl_opts()
    ydl_opts['extract_flat'] = False

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # If playlist or multiple entries, pick the first video
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
                
            title = info.get('title', 'Unknown Video Title')
            thumbnail = info.get('thumbnail')
            if not thumbnail and info.get('thumbnails'):
                thumbnail = info['thumbnails'][-1].get('url', '')
                
            duration_sec = info.get('duration')
            if duration_sec:
                duration = time.strftime('%H:%M:%S', time.gmtime(duration_sec)) if duration_sec >= 3600 else time.strftime('%M:%S', time.gmtime(duration_sec))
            else:
                duration = info.get('duration_string', 'N/A')
                
            uploader = info.get('uploader') or info.get('channel') or info.get('author', 'Unknown Creator')
            platform = info.get('extractor_key', 'Web Video')
            webpage_url = info.get('webpage_url', url)
            
            formats = [
                {'id': 'best', 'label': '🌟 Best Quality (MP4 / Windows Compatible)', 'desc': 'Highest resolution with H.264 codec for Windows Media Player'},
                {'id': '1080p', 'label': '🖥️ 1080p Full HD (MP4 / Windows Compatible)', 'desc': 'Crisp 1080p MP4 format for native Windows playback'},
                {'id': '720p', 'label': '📱 720p HD Quality (MP4)', 'desc': 'Standard HD MP4, instant playback on all media players'},
                {'id': '480p', 'label': '⚡ 480p SD Quality (MP4)', 'desc': 'Smallest MP4 file size, fastest download'},
                {'id': 'mp3', 'label': '🎵 Audio Only (MP3)', 'desc': 'Extract high quality MP3 audio'}
            ]
            
            return jsonify({
                'success': True,
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration,
                'uploader': uploader,
                'platform': platform,
                'url': webpage_url,
                'formats': formats,
                'download_dir': DOWNLOAD_DIR
            })
    except Exception as e:
        err_msg = str(e)
        if 'Unsupported URL' in err_msg:
            err_msg = "Unsupported URL or website. Please paste a valid link from YouTube, TikTok, Instagram, Twitter/X, Vimeo, Facebook, etc."
        return jsonify({'error': err_msg}), 400


def progress_hook(d):
    info_dict = d.get('info_dict', {})
    task_id = info_dict.get('__task_id') or d.get('__task_id')
    
    if not task_id or task_id not in downloads:
        return

    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        progress = 0
        if total_bytes > 0:
            progress = round((downloaded_bytes / total_bytes) * 100, 1)

        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        total_str = d.get('_total_bytes_str') or d.get('_total_bytes_estimate_str', 'N/A')
        
        # Clean ansi color codes from strings if any
        if speed and isinstance(speed, str):
            speed = speed.replace('\x1b[0;32m', '').replace('\x1b[0m', '').strip()
        if eta and isinstance(eta, str):
            eta = eta.replace('\x1b[0;33m', '').replace('\x1b[0m', '').strip()
        if total_str and isinstance(total_str, str):
            total_str = total_str.replace('\x1b[0;32m', '').replace('\x1b[0m', '').strip()

        downloads[task_id].update({
            'status': 'downloading',
            'progress': progress,
            'speed': speed,
            'eta': eta,
            'total_size': total_str
        })
    elif d['status'] == 'finished':
        filepath = d.get('filename', '')
        downloads[task_id].update({
            'status': 'processing',
            'progress': 100.0,
            'speed': 'Merging / Processing...',
            'eta': '0s',
            'filepath': filepath
        })


def download_worker(task_id, url, format_id, title):
    try:
        downloads[task_id]['status'] = 'downloading'
        
        # We inject __task_id into ydl_opts or hook so hook can find it
        out_template = os.path.join(DOWNLOAD_DIR, '%(title).100s [%(id)s].%(ext)s')
        
        ydl_opts = get_base_ydl_opts()
        ydl_opts['outtmpl'] = out_template
        ydl_opts['progress_hooks'] = [lambda d: progress_hook(dict(d, __task_id=task_id))]

        if format_id != 'mp3':
            ydl_opts['merge_output_format'] = 'mp4'
            if FFMPEG_PATH:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoRemuxer',
                    'preferedformat': 'mp4',
                }]

        if format_id == 'best':
            ydl_opts['format'] = 'bestvideo[vcodec^=avc]+bestaudio[acodec^=mp4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif format_id == '1080p':
            ydl_opts['format'] = 'bestvideo[height<=1080][vcodec^=avc]+bestaudio[acodec^=mp4a]/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best'
        elif format_id == '720p':
            ydl_opts['format'] = 'bestvideo[height<=720][vcodec^=avc]+bestaudio[acodec^=mp4a]/bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
        elif format_id == '480p':
            ydl_opts['format'] = 'bestvideo[height<=480][vcodec^=avc]+bestaudio[acodec^=mp4a]/bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'
        elif format_id == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            if FFMPEG_PATH:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
                
            filepath = info.get('requested_downloads', [{}])[0].get('filepath') or info.get('filepath') or ydl.prepare_filename(info)
            if format_id == 'mp3' and filepath and not filepath.endswith('.mp3'):
                base, _ = os.path.splitext(filepath)
                if os.path.exists(base + '.mp3'):
                    filepath = base + '.mp3'

            downloads[task_id].update({
                'status': 'finished',
                'progress': 100.0,
                'speed': 'Completed',
                'eta': '0s',
                'filepath': filepath
            })
    except Exception as e:
        traceback.print_exc()
        downloads[task_id].update({
            'status': 'error',
            'error': str(e)
        })


@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.get_json()
    url = data.get('url', '').strip()
    format_id = data.get('format', 'best')
    title = data.get('title', 'Video Download')
    thumbnail = data.get('thumbnail', '')
    platform = data.get('platform', 'Web')
    
    if not url:
        return jsonify({'error': 'URL is required.'}), 400

    task_id = str(uuid.uuid4())
    downloads[task_id] = {
        'id': task_id,
        'url': url,
        'title': title,
        'thumbnail': thumbnail,
        'platform': platform,
        'format_id': format_id,
        'status': 'starting',
        'progress': 0.0,
        'speed': 'Starting...',
        'eta': 'Calculating...',
        'total_size': 'N/A',
        'filepath': '',
        'error': '',
        'time': time.time()
    }
    
    thread = threading.Thread(target=download_worker, args=(task_id, url, format_id, title), daemon=True)
    thread.start()
    
    return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if task_id not in downloads:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(downloads[task_id])


@app.route('/api/history', methods=['GET'])
def get_history():
    # Return sorted by time descending
    sorted_history = sorted(downloads.values(), key=lambda x: x.get('time', 0), reverse=True)
    return jsonify({'downloads': sorted_history, 'download_dir': DOWNLOAD_DIR})


@app.route('/api/open-folder', methods=['POST'])
def open_folder():
    data = request.get_json()
    filepath = data.get('filepath', '')
    task_id = data.get('task_id', '')
    
    if task_id and task_id in downloads and downloads[task_id].get('filepath'):
        filepath = downloads[task_id]['filepath']
        
    target_path = os.path.normpath(filepath) if filepath and os.path.exists(filepath) else os.path.normpath(DOWNLOAD_DIR)
    
    try:
        if os.path.isfile(target_path):
            # Select the exact file in Windows Explorer
            subprocess.run(['explorer', '/select,', target_path])
        else:
            # Open the folder directly
            os.startfile(os.path.dirname(target_path) if os.path.isfile(target_path) else target_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/open-root-folder', methods=['POST'])
def open_root_folder():
    try:
        os.startfile(os.path.normpath(DOWNLOAD_DIR))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<task_id>', methods=['GET'])
def download_file(task_id):
    if task_id not in downloads or not downloads[task_id].get('filepath'):
        return jsonify({'error': 'File not found'}), 404
    filepath = downloads[task_id]['filepath']
    if not os.path.exists(filepath):
        return jsonify({'error': 'File no longer exists on server'}), 404
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("  [INFO] Universal Video Downloader Server Started!")
    print(f"  [PATH] Videos will be saved to: {DOWNLOAD_DIR}")
    print(f"  [WEB]  Server listening on port {port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
