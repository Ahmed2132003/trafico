document.addEventListener('DOMContentLoaded', () => {
    console.log('Verify_email.js loaded successfully');

    // تحميل المود المحفوظ
    const savedMode = localStorage.getItem('theme') || 'light-mode';
    document.body.className = savedMode;
    const modeToggle = document.getElementById('mode-toggle');
    const modeIcon = modeToggle ? modeToggle.querySelector('.mode-icon') : null;
    if (modeIcon) {
        modeIcon.textContent = savedMode === 'light-mode' ? '☀️' : '🌙';
    } else {
        console.error('Mode icon not found');
    }

    // تبديل اللايت/دارك مود
    if (modeToggle) {
        modeToggle.addEventListener('click', () => {
            console.log('Mode toggle clicked');
            const isLightMode = document.body.classList.contains('light-mode');
            document.body.className = isLightMode ? 'dark-mode' : 'light-mode';
            modeIcon.textContent = isLightMode ? '🌙' : '☀️';
            localStorage.setItem('theme', isLightMode ? 'dark-mode' : 'light-mode');
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
            document.documentElement.lang = isArabic ? 'en' : 'ar';
            document.documentElement.dir = isArabic ? 'ltr' : 'rtl';
            currentLang = isArabic ? 'en' : 'ar';
            langIcon.textContent = isArabic ? '🇬🇧' : '🇸🇦';

            // تغيير النصوص
            const translations = {
                'ar': {
                    'h2': 'تحقق من بريدك الإلكتروني',
                    'p': 'أدخل كود التحقق الذي تم إرساله إلى بريدك الإلكتروني. الكود صالح لمدة دقيقتين.',
                    'button': 'تحقق',
                    'verification_code': 'كود التحقق'
                },
                'en': {
                    'h2': 'Verify Your Email',
                    'p': 'Enter the verification code sent to your email. The code is valid for two minutes.',
                    'button': 'Verify',
                    'verification_code': 'Verification Code'
                }
            };

            const h2 = document.querySelector('h2');
            const p = document.querySelector('p');
            const button = document.querySelector('.animated-button');
            if (h2) h2.textContent = translations[currentLang]['h2'];
            if (p) p.textContent = translations[currentLang]['p'];
            if (button) button.textContent = translations[currentLang]['button'];

            document.querySelectorAll('label').forEach(label => {
                const fieldName = label.getAttribute('for') || '';
                const enText = label.getAttribute('data-en');
                if (enText && fieldName) {
                    label.textContent = translations[currentLang][fieldName] || enText;
                    label.setAttribute('data-ar', translations['ar'][fieldName] || label.textContent);
                }
            });
        });
    } else {
        console.error('Language toggle button not found');
    }
});