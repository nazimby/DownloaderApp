document.addEventListener('DOMContentLoaded', function() {
    // API URL-i - deploy zamanı dəyişdirilə bilər
    const API_BASE_URL = window.location.hostname.includes('github.io') 
        ? 'https://media-downloader-api.onrender.com' // Render.com URL-nizi buraya əlavə edin
        : ''; // Lokal mühitdə boş string ("/api/download" kimi relativ PATH işlədə bilər)
    
    const urlInput = document.getElementById('url-input');
    const formatSelect = document.getElementById('format-select');
    const downloadBtn = document.getElementById('download-btn');
    const loader = document.getElementById('loader');
    const statusDiv = document.getElementById('status');
    const resultSection = document.getElementById('result-section');
    const downloadLink = document.getElementById('download-link');
    const recentList = document.getElementById('recent-list');
    
    // Yerli saxlamada olan son endirmələri yüklə
    loadRecentDownloads();
    
    downloadBtn.addEventListener('click', function() {
        // URL doğrulama
        const url = urlInput.value.trim();
        if (!url) {
            showStatus('Zəhmət olmasa düzgün bir URL daxil edin', 'error');
            return;
        }
        
        // Yüklənmə vəziyyətini göstər
        downloadBtn.disabled = true;
        loader.style.display = 'block';
        resultSection.style.display = 'none';
        showStatus('Endirmə sorğunuz işlənir...', 'processing');
        
        // Backend-ə sorğu göndər
        const format = formatSelect.value;
        
        fetch(`${API_BASE_URL}/api/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                format: format
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Endirmə uğurlu
                resultSection.style.display = 'block';
                downloadLink.href = data.download_path;
                downloadLink.setAttribute('download', data.filename);
                
                showStatus('Endirmə uğurla tamamlandı!', 'success');
                
                // Son endirmələrə əlavə et
                addRecentDownload(data.full_url || data.download_path, data.filename);
            } else {
                showStatus('Xəta: ' + (data.error || 'Endirmə prosesi uğursuz oldu.'), 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showStatus('Bir xəta baş verdi: ' + error.message, 'error');
        })
        .finally(() => {
            // Yüklənmə vəziyyətini sil
            loader.style.display = 'none';
            downloadBtn.disabled = false;
        });
    });
    
    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        statusDiv.style.display = 'block';
    }
    
    function addRecentDownload(url, filename) {
        // Mövcud endirmələri al və ya boş massiv başlat
        let recentDownloads = [];
        try {
            recentDownloads = JSON.parse(localStorage.getItem('recentDownloads') || '[]');
        } catch (error) {
            console.error('JSON parse error:', error);
            recentDownloads = [];
            // Xətalı məlumatları silmək
            localStorage.removeItem('recentDownloads');
        }
        
        // Yeni endirməni başa əlavə et
        recentDownloads.unshift({
            url: url,
            filename: filename,
            date: new Date().toISOString()
        });
        
        // Yalnız son 5 endirməni saxla
        if (recentDownloads.length > 5) {
            recentDownloads.pop();
        }
        
        // LocalStorage-ə yadda saxla
        localStorage.setItem('recentDownloads', JSON.stringify(recentDownloads));
        
        // İnterfeysi yenilə
        loadRecentDownloads();
    }
    
    function loadRecentDownloads() {
        let recentDownloads = [];
        try {
            recentDownloads = JSON.parse(localStorage.getItem('recentDownloads') || '[]');
        } catch (error) {
            console.error('JSON parse error:', error);
            recentDownloads = [];
            // Xətalı məlumatları silmək
            localStorage.removeItem('recentDownloads');
        }
        
        if (!recentDownloads || recentDownloads.length === 0) {
            recentList.innerHTML = '<p>Hələ endirmə yoxdur</p>';
            return;
        }
        
        recentList.innerHTML = '';
        recentDownloads.forEach(function(item) {
            if (!item || !item.date) {
                return; // Yanlış məlumat quruluşuna malik elementləri atlayırıq
            }
            
            try {
                const date = new Date(item.date);
                const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                
                const downloadItem = document.createElement('div');
                downloadItem.className = 'recent-item';
                downloadItem.innerHTML = `
                    <div>
                        <strong>${item.filename || 'Naməlum fayl'}</strong>
                        <div>${formattedDate}</div>
                    </div>
                    <a href="${item.url || '#'}" download="${item.filename || ''}" class="btn">Endir</a>
                `;
                
                recentList.appendChild(downloadItem);
            } catch (error) {
                console.error('Error rendering recent download item:', error);
            }
        });
    }
});