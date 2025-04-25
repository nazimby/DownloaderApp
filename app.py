from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import yt_dlp
import os
import uuid
import time
import subprocess

app = Flask(__name__, static_url_path='', static_folder='.', template_folder='.')
CORS(app)  # Bütün API endpointləri üçün CORS aktivləşdirildi

# Render.com mühitində olub-olmadığımızı yoxlayırıq
IS_RENDER = 'RENDER' in os.environ

# Heroku'da FFmpeg'in qurulması
if 'DYNO' in os.environ or IS_RENDER:
    try:
        # FFmpeg buildpack əgər quraşdırılıbsa
        ffmpeg_path = subprocess.check_output(["which", "ffmpeg"]).decode().strip()
        if ffmpeg_path:
            print(f"FFmpeg found at: {ffmpeg_path}")
    except Exception as e:
        print(f"FFmpeg not found: {e}")
        print("Please add the FFmpeg buildpack on Render or Heroku")

# Output dizini oluşturma - Render üçün persistant disk istifadə edirik
if IS_RENDER:
    OUTPUT_DIR = os.environ.get('RENDER_VOLUME_PATH', '/opt/render/project/media')
else:
    OUTPUT_DIR = os.path.join(os.getcwd(), "output")

if not os.path.exists(OUTPUT_DIR):
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"Qovluq yaradıldı: {OUTPUT_DIR}")
    except Exception as e:
        print(f"Qovluq yarada bilmədik: {e}")
        # Alternativ yol sınayaq
        if IS_RENDER:
            try:
                tmp_dir = "/tmp/downloader_media"
                os.makedirs(tmp_dir, exist_ok=True)
                OUTPUT_DIR = tmp_dir
                print(f"Alternativ qovluq yaradıldı: {OUTPUT_DIR}")
            except Exception as e2:
                print(f"Alternativ qovluq yarada bilmədik: {e2}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def download_media():
    data = request.json
    url = data.get('url')
    format_type = data.get('format', 'mp3')
    
    if not url:
        return jsonify({"error": "URL gereklidir"}), 400
    
    try:
        # Benzersiz bir dosya adı oluştur
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time())
        base_filename = f"{timestamp}_{unique_id}"
        
        if format_type == 'mp3':
            output_filename = download_audio(url, base_filename)
        else:  # mp4
            output_filename = download_video(url, base_filename)
        
        # Log fayl yolunu və mövcudluğunu
        file_path = os.path.join(OUTPUT_DIR, output_filename)
        file_exists = os.path.exists(file_path)
        print(f"Çıxış faylı: {file_path}, Mövcuddur: {file_exists}")
        
        # Fayl yolunu və URL-i qaytarırıq
        download_path = f"/download/{output_filename}"
        host_url = request.host_url.rstrip('/')
        full_download_url = f"{host_url}{download_path}"
        
        return jsonify({
            "success": True,
            "filename": output_filename,
            "file_path": file_path,
            "file_exists": file_exists,
            "download_path": download_path,
            "full_url": full_download_url
        })
        
    except Exception as e:
        print(f"Xəta: {str(e)}")
        return jsonify({"error": str(e)}), 500

def download_video(url, base_filename):
    output_template = os.path.join(OUTPUT_DIR, f"{base_filename}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferredformat': 'mp4',
        }],
        'verbose': True,  # Ətraflı məlumat
        'no_check_certificate': True,  # SSL sertifikatı yoxlamasını keçin
        'nocheckcertificate': True,
        'ignoreerrors': True,  # Bəzi xətaları yox sayın
        'quiet': False,  # Verbose məlumatı görmək üçün
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],  # Android klient kimi davranmaq
                'player_skip': ['webpage', 'js'],  # Web səhifəni və JavaScript-i ötürmək
            }
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
        
    # MP4 uzantısı ile dosya adını döndür
    return os.path.basename(filename).replace(".webm", ".mp4").replace(".mkv", ".mp4")

def download_audio(url, base_filename):
    output_template = os.path.join(OUTPUT_DIR, f"{base_filename}.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',  # En yüksek kalite
        }],
        'verbose': True,  # Ətraflı məlumat
        'no_check_certificate': True,  # SSL sertifikatı yoxlamasını keçin
        'nocheckcertificate': True,
        'ignoreerrors': True,  # Bəzi xətaları yox sayın
        'quiet': False,  # Verbose məlumatı görmək üçün
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],  # Android klient kimi davranmaq
                'player_skip': ['webpage', 'js'],  # Web səhifəni və JavaScript-i ötürmək
            }
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        # Post-processor mp3'e dönüştüreceği için
        return f"{base_filename}.mp3"

@app.route('/download/<path:filename>')
def download_file(filename):
    # Log - hansı fayl yolunda axtarış aparırıq
    print(f"Fayl endirmə tələbi: {filename}")
    print(f"Axtarılacaq qovluq: {OUTPUT_DIR}")
    
    # Yoxlayaq ki, fayl həqiqətən mövcuddur
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        print(f"Fayl tapıldı: {file_path}")
    else:
        print(f"Fayl tapılmadı: {file_path}")
        # Qovluqdakı bütün faylları siyahı şəklində çap edək
        all_files = os.listdir(OUTPUT_DIR)
        print(f"Qovluqdakı mövcud fayllar: {all_files}")
    
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)