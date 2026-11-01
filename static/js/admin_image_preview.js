// Live Image Preview before saving in Django Admin (Mobile & Desktop)
document.addEventListener('DOMContentLoaded', function () {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function (input) {
        if (input.name && input.name.includes('image_file')) {
            input.setAttribute('accept', 'image/*');
            
            // Container for live preview
            let previewContainer = document.getElementById('admin-live-image-preview');
            if (!previewContainer) {
                previewContainer = document.createElement('div');
                previewContainer.id = 'admin-live-image-preview';
                previewContainer.style.marginTop = '12px';
                previewContainer.style.marginBottom = '12px';
                input.parentNode.appendChild(previewContainer);
            }

            input.addEventListener('change', function (event) {
                const file = event.target.files[0];
                if (file) {
                    // Check file size (e.g. limit 10MB)
                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        previewContainer.innerHTML = `
                            <div style="display:inline-flex; flex-direction:column; align-items:flex-start; padding:12px; background:#f8fafc; border:2px dashed #10b981; border-radius:12px; max-width:320px;">
                                <div style="display:flex; justify-content:space-between; width:100%; margin-bottom:8px; font-size:12px; font-weight:bold; color:#0f172a;">
                                    <span>📸 معاينة مباشرة قبل الرفع</span>
                                    <span style="color:#059669;">${sizeMB} MB</span>
                                </div>
                                <img src="${e.target.result}" style="width:100%; max-height:220px; object-fit:contain; border-radius:8px; background:#ffffff; box-shadow:0 4px 12px rgba(0,0,0,0.08);"/>
                                <span style="margin-top:6px; font-size:11px; color:#64748b;">☁️ سيتم رفع هذه الصورة تلقائياً إلى Cloudinary وتطبيق f_auto,q_auto عند الحفظ.</span>
                            </div>
                        `;
                    };
                    reader.readAsDataURL(file);
                } else {
                    previewContainer.innerHTML = '';
                }
            });
        }
    });
});

