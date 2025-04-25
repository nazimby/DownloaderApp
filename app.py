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
            print(f"FFmpeg tapıldı: {ffmpeg_path}")
    except Exception as e:
        print(f"FFmpeg tapılmadı: {e}")
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
        return jsonify({"error": "URL tələb olunur"}), 400
    
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
    print(f"Video endirməyə başlayır: {url} -> {base_filename}")
    output_template = os.path.join(OUTPUT_DIR, f"{base_filename}.%(ext)s")
    
    print(f"Çıxış şablonu: {output_template}")
    print(f"OUTPUT_DIR mövcuddur: {os.path.exists(OUTPUT_DIR)}")
    
    try:
        # Qısa yoxlama: OUTPUT_DIR-də yazıla bilərmi?
        test_file = os.path.join(OUTPUT_DIR, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test")
        os.remove(test_file)
        print(f"OUTPUT_DIR-ə yazma uğurludur.")
    except Exception as e:
        print(f"OUTPUT_DIR-ə yazma xətası: {e}")
    
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
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"yt-dlp ilə endirməyə başlayır...")
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            print(f"yt-dlp ilə endirmə tamamlandı. Fayl: {filename}")
            
            # Faylın varlığını yoxlayaq
            if os.path.exists(filename):
                print(f"Fayl yaradıldı: {filename}")
                file_size = os.path.getsize(filename)
                print(f"Fayl həcmi: {file_size} bayt")
            else:
                print(f"Fayl yaradılmadı: {filename}")
                # Bütün qovluqdakı faylları listləyək
                files = os.listdir(OUTPUT_DIR)
                print(f"OUTPUT_DIR-dəki fayllar: {files}")
                
            # MP4 uzantısı ile dosya adını döndür
            return os.path.basename(filename).replace(".webm", ".mp4").replace(".mkv", ".mp4")
    except Exception as e:
        print(f"yt-dlp xətası: {str(e)}")
        # Mümkün qədər məlumat qaytarmağa çalışaq
        return f"{base_filename}.mp4"

def download_audio(url, base_filename):
    print(f"Audio endirməyə başlayır: {url} -> {base_filename}")
    output_template = os.path.join(OUTPUT_DIR, f"{base_filename}.%(ext)s")
    
    print(f"Çıxış şablonu: {output_template}")
    print(f"OUTPUT_DIR mövcuddur: {os.path.exists(OUTPUT_DIR)}")
    
    try:
        # Qısa yoxlama: OUTPUT_DIR-də yazıla bilərmi?
        test_file = os.path.join(OUTPUT_DIR, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test")
        os.remove(test_file)
        print(f"OUTPUT_DIR-ə yazma uğurludur.")
    except Exception as e:
        print(f"OUTPUT_DIR-ə yazma xətası: {e}")
    
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
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"yt-dlp ilə endirməyə başlayır...")
            info_dict = ydl.extract_info(url, download=True)
            
            # Fayl adını yaradaq
            mp3_filename = os.path.join(OUTPUT_DIR, f"{base_filename}.mp3")
            print(f"Gözlənilən MP3 fayl: {mp3_filename}")
            
            # Faylın varlığını yoxlayaq
            if os.path.exists(mp3_filename):
                print(f"MP3 fayl yaradıldı: {mp3_filename}")
                file_size = os.path.getsize(mp3_filename)
                print(f"Fayl həcmi: {file_size} bayt")
            else:
                print(f"MP3 fayl yaradılmadı: {mp3_filename}")
                # Bütün qovluqdakı faylları listləyək
                files = os.listdir(OUTPUT_DIR)
                print(f"OUTPUT_DIR-dəki fayllar: {files}")
                
                # Bəlkə digər formatda fayl yaradılıb?
                for file in files:
                    if base_filename in file:
                        full_path = os.path.join(OUTPUT_DIR, file)
                        print(f"Bənzər fayl tapıldı: {full_path}")
                        # MP3-ə konvertasiya edə bilərik?
                        try:
                            from_path = full_path
                            to_path = mp3_filename
                            os.system(f"ffmpeg -i {from_path} -codec:a libmp3lame -qscale:a 2 {to_path}")
                            if os.path.exists(to_path):
                                print(f"Fayl MP3-ə çevrildi: {to_path}")
                            else:
                                print(f"Fayl MP3-ə çevrilə bilmədi")
                        except Exception as e:
                            print(f"MP3 çevirmə xətası: {e}")
            
            # Post-processor mp3'e dönüştüreceği için
            return f"{base_filename}.mp3"
    except Exception as e:
        print(f"yt-dlp xətası: {str(e)}")
        # Mümkün qədər məlumat qaytarmağa çalışaq
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
        file_size = os.path.getsize(file_path)
        print(f"Fayl həcmi: {file_size} bayt")
        
        # MIME növləri
        if filename.endswith('.mp3'):
            mimetype = 'audio/mpeg'
        elif filename.endswith('.mp4'):
            mimetype = 'video/mp4'
        else:
            mimetype = 'application/octet-stream'
        
        # Faylı göndərərkən düzgün MIME və başlıq əlavə etmək
        response = send_from_directory(
            OUTPUT_DIR, 
            filename, 
            as_attachment=True,
            mimetype=mimetype,
            download_name=filename  # açıq şəkildə adı göstərmək
        )
        
        # Başlıqları gücləndir (bəzi brauzerlər üçün)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = mimetype
        
        return response
    else:
        print(f"Fayl tapılmadı: {file_path}")
        # Qovluqdakı bütün faylları siyahı şəklində çap edək
        try:
            all_files = os.listdir(OUTPUT_DIR)
            print(f"Qovluqdakı mövcud fayllar: {all_files}")
            
            # Bənzər fayl axtarışı
            matching_files = [f for f in all_files if filename.split('.')[0] in f]
            if matching_files:
                print(f"Bənzər fayllar tapıldı: {matching_files}")
                alt_filename = matching_files[0]
                print(f"İlk bənzər fayldan istifadə ediləcək: {alt_filename}")
                return send_from_directory(OUTPUT_DIR, alt_filename, as_attachment=True)
        except Exception as e:
            print(f"Qovluq listləmədə xəta: {e}")
            
        return jsonify({"error": f"Fayl tapılmadı: {filename}"}), 404

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)