document.addEventListener('DOMContentLoaded', () => {
    console.log('Product_add.js loaded successfully');

    // تحميل المود المحفوظ
    const savedMode = localStorage.getItem('theme') || 'light-mode';
    document.body.className = savedMode;
    const modeToggle = document.getElementById('mode-toggle');
    const modeIcon = modeToggle ? modeToggle.querySelector('.mode-icon') : null;
    if (modeIcon) {
        modeIcon.textContent = savedMode === 'light-mode' ? '🌙' : '☀️';
    } else {
        console.error('Mode icon not found');
    }

    // تبديل اللايت/دارك مود
    if (modeToggle) {
        modeToggle.addEventListener('click', () => {
            console.log('Mode toggle clicked');
            const isLightMode = document.body.classList.contains('light-mode');
            document.body.className = isLightMode ? 'dark-mode' : 'light-mode';
            modeIcon.textContent = isLightMode ? '☀️' : '🌙';
            localStorage.setItem('theme', isLightMode ? 'dark-mode' : 'light-mode');
            modeToggle.title = isLightMode ? modeToggle.getAttribute('data-title-ar') : modeToggle.getAttribute('data-title-en');
        });
    } else {
        console.error('Mode toggle button not found');
    }

    // تبديل اللغة
    const langToggle = document.getElementById('lang-toggle');
    const langIcon = langToggle ? langToggle.querySelector('.lang-icon') : null;
    let currentLang = document.documentElement.lang || 'ar';
    if (langIcon) {
        langIcon.textContent = currentLang === 'ar' ? '🇸🇦' : '🇬🇧';
    } else {
        console.error('Language icon not found');
    }

    if (langToggle) {
        langToggle.addEventListener('click', () => {
            console.log('Language toggle clicked');
            const isArabic = currentLang === 'ar';
            const newLang = isArabic ? 'en' : 'ar';
            fetch(`/set-language/${newLang}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            }).then(() => {
                document.documentElement.lang = newLang;
                document.documentElement.dir = isArabic ? 'ltr' : 'rtl';
                currentLang = newLang;
                langIcon.textContent = isArabic ? '🇬🇧' : '🇸🇦';

                // تحديث النصوص
                document.querySelectorAll('[data-en]').forEach(element => {
                    const enText = element.getAttribute('data-en');
                    const arText = element.getAttribute('data-ar') || element.textContent;
                    element.textContent = isArabic ? enText : arText;
                    element.setAttribute('data-ar', arText);
                });

                // تحديث title لأزرار الوضع واللغة
                modeToggle.title = isArabic ? modeToggle.getAttribute('data-title-en') : modeToggle.getAttribute('data-title-ar');
                langToggle.title = isArabic ? langToggle.getAttribute('data-title-en') : langToggle.getAttribute('data-title-ar');
            });
        });
    } else {
        console.error('Language toggle button not found');
    }

    // التحقق من الفورم
    const form = document.querySelector('.form-animated');
    if (form) {
        form.addEventListener('submit', (e) => {
            const name = document.getElementById('name').value;
            const basePrice = document.getElementById('base_price').value;
            const stock = document.getElementById('stock').value;
            if (!name || basePrice <= 0 || stock < 0) {
                e.preventDefault();
                const errorDiv = document.createElement('div');
                errorDiv.className = 'form-error notification error';
                errorDiv.textContent = 'يرجى ملء جميع الحقول المطلوبة بقيم صالحة';
                document.querySelector('.form-messages')?.appendChild(errorDiv) || document.querySelector('.container').appendChild(errorDiv);
                setTimeout(() => errorDiv.remove(), 3000);
            }
        });
    }
});