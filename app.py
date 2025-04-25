from flask import Flask, request, jsonify, send_from_directory, render_template
import yt_dlp
import os
import uuid
import time

app = Flask(__name__, static_url_path='', static_folder='.', template_folder='.')


# Output dizini oluşturma
OUTPUT_DIR = os.path.join(os.getcwd(), "output")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

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
        
        # Dosya adını ve yolunu döndür
        download_path = f"/download/{output_filename}"
        host_url = request.host_url.rstrip('/')
        full_download_url = f"{host_url}{download_path}"
        
        return jsonify({
            "success": True,
            "filename": output_filename,
            "download_path": download_path,
            "full_url": full_download_url
        })
        
    except Exception as e:
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
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        # Post-processor mp3'e dönüştüreceği için
        return f"{base_filename}.mp3"

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)