document.addEventListener('DOMContentLoaded', () => {
    console.log('Register.js loaded successfully');

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
                    'h2': 'إنشاء حساب',
                    'p': 'لديك حساب بالفعل؟ <a href="/users/login/">تسجيل الدخول</a>',
                    'button': 'تسجيل',
                    'username': 'اسم المستخدم',
                    'email': 'البريد الإلكتروني',
                    'phone_number': 'رقم الهاتف',
                    'user_type': 'نوع المستخدم',
                    'password1': 'كلمة المرور',
                    'password2': 'تأكيد كلمة المرور',
                    'marketer': 'مسوق',
                    'designer': 'مصمم',
                    'customer': 'مشتري'
                },
                'en': {
                    'h2': 'Create an Account',
                    'p': 'Already have an account? <a href="/users/login/">Login</a>',
                    'button': 'Register',
                    'username': 'Username',
                    'email': 'Email',
                    'phone_number': 'Phone Number',
                    'user_type': 'User Type',
                    'password1': 'Password',
                    'password2': 'Confirm Password',
                    'marketer': 'Marketer',
                    'designer': 'Designer',
                    'customer': 'Customer'
                }
            };

            const h2 = document.querySelector('h2');
            const p = document.querySelector('.form-link');
            const button = document.querySelector('.animated-button');
            if (h2) h2.textContent = translations[currentLang]['h2'];
            if (p) p.innerHTML = translations[currentLang]['p'];
            if (button) button.textContent = translations[currentLang]['button'];

            document.querySelectorAll('label').forEach(label => {
                const fieldName = label.getAttribute('for') ? label.getAttribute('for').split('_')[0] : '';
                const enText = label.getAttribute('data-en');
                if (enText && fieldName) {
                    label.textContent = translations[currentLang][fieldName] || enText;
                    label.setAttribute('data-ar', translations['ar'][fieldName] || label.textContent);
                }
            });

            document.querySelectorAll('.form-check-label').forEach(label => {
                const value = label.getAttribute('for') ? label.getAttribute('for').split('_')[1] : '';
                if (value) {
                    label.textContent = translations[currentLang][value] || label.textContent;
                }
            });
        });
    } else {
        console.error('Language toggle button not found');
    }
});