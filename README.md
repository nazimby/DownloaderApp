# Media Downloader

YouTube və digər məşhur saytlardan video və audio endirmək üçün veb tətbiq.

## Xüsusiyyətlər

- YouTube URL-dən MP3 (audio) və MP4 (video) formatlarında endirmə
- Yüksək keyfiyyətli audio ve video endirmə
- Son endirmələrin saxlanması
- Sadə və istifadəçi dostu interfeys

## Quraşdırma

1. Repo-nu klonlayın
   ```
   git clone https://github.com/istifadeci_adiniz/media-downloader.git
   cd media-downloader
   ```

2. Lazımi paketləri yükləyin
   ```
   pip install -r requirements.txt
   ```

3. Tətbiqi başladın
   ```
   python app.py
   ```

4. Brauzerinizdə http://localhost:5000 ünvanına daxil olun

## İstifadə

1. YouTube video linkini daxil edin
2. Endirmək istədiyiniz formatı seçin (MP3 və ya MP4)
3. "İndir" düyməsinə basın
4. Endirmənin tamamlanmasını gözləyin və "Dosyayı İndir" düyməsinə basın

## Texniki Məlumat

- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- Video/Audio endirmə: yt-dlp

## Lisenziya

Şəxsi istifadə üçün yaradılmışdır. 