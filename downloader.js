document.addEventListener('DOMContentLoaded', function() {
    const urlInput = document.getElementById('url-input');
    const formatSelect = document.getElementById('format-select');
    const downloadBtn = document.getElementById('download-btn');
    const loader = document.getElementById('loader');
    const statusDiv = document.getElementById('status');
    const resultSection = document.getElementById('result-section');
    const downloadLink = document.getElementById('download-link');
    const recentList = document.getElementById('recent-list');
    
    // Yerel depolamadan son indirmeleri yükle
    loadRecentDownloads();
    
    downloadBtn.addEventListener('click', function() {
        // URL doğrulama
        const url = urlInput.value.trim();
        if (!url) {
            showStatus('Lütfen geçerli bir URL girin', 'error');
            return;
        }
        
        // Yükleme durumunu göster
        downloadBtn.disabled = true;
        loader.style.display = 'block';
        resultSection.style.display = 'none';
        showStatus('İndirme isteğiniz işleniyor...', 'processing');
        
        // Backend'e istek gönder
        const format = formatSelect.value;
        
        fetch('/api/download', {
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
                // İndirme başarılı
                resultSection.style.display = 'block';
                downloadLink.href = data.download_path;
                downloadLink.setAttribute('download', data.filename);
                
                showStatus('İndirme başarıyla tamamlandı!', 'success');
                
                // Son indirmelere ekle
                addRecentDownload(data.full_url || data.download_path, data.filename);
            } else {
                showStatus('Hata: ' + (data.error || 'İndirme işlemi başarısız oldu.'), 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showStatus('Bir hata oluştu: ' + error.message, 'error');
        })
        .finally(() => {
            // Yükleme durumunu kaldır
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
        // Mevcut indirmeleri al veya boş dizi başlat
        let recentDownloads = [];
        try {
            recentDownloads = JSON.parse(localStorage.getItem('recentDownloads') || '[]');
        } catch (error) {
            console.error('JSON parse error:', error);
            recentDownloads = [];
            // Xətalı məlumatları silmək
            localStorage.removeItem('recentDownloads');
        }
        
        // Yeni indirmeyi başa ekle
        recentDownloads.unshift({
            url: url,
            filename: filename,
            date: new Date().toISOString()
        });
        
        // Sadece son 5 indirmeyi tut
        if (recentDownloads.length > 5) {
            recentDownloads.pop();
        }
        
        // LocalStorage'a kaydet
        localStorage.setItem('recentDownloads', JSON.stringify(recentDownloads));
        
        // Arayüzü güncelle
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
            recentList.innerHTML = '<p>Henüz indirme yok</p>';
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
                        <strong>${item.filename || 'Unknown file'}</strong>
                        <div>${formattedDate}</div>
                    </div>
                    <a href="${item.url || '#'}" download="${item.filename || ''}" class="btn">İndir</a>
                `;
                
                recentList.appendChild(downloadItem);
            } catch (error) {
                console.error('Error rendering recent download item:', error);
            }
        });
    }
});