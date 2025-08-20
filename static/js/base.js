document.addEventListener('DOMContentLoaded', () => {
    console.log('Base.js loaded');

    // Translation object for base.html elements
    const translations = {
        ar: {
            title: 'ترافيكو',
            logoAlt: 'شعار ترافيكو',
            productsLink: 'المنتجات',
            loginLink: 'تسجيل الدخول',
            logoutLink: 'تسجيل الخروج',
            footerText: 'جميع الحقوق محفوظة © ترافيكو مقدم من شركة كريتيفتي كود للبرمجة 2025',
            modeToggleTitleLight: 'تبديل إلى الوضع المظلم',
            modeToggleTitleDark: 'تبديل إلى الوضع الفاتح',
            langToggleTitle: 'تبديل إلى الإنجليزية',
            langToggleIcon: '🇸🇦'
        },
        en: {
            title: 'Trafico',
            logoAlt: 'Trafico Logo',
            productsLink: 'Products',
            loginLink: 'Login',
            logoutLink: 'Logout',
            footerText: 'All Rights Reserved © Trafico 2025 by Creativity Code Co.',
            modeToggleTitleLight: 'Switch to Dark Mode',
            modeToggleTitleDark: 'Switch to Light Mode',
            langToggleTitle: 'Switch to Arabic',
            langToggleIcon: '🇬🇧'
        }
    };

    // Load saved theme and language
    let savedMode = localStorage.getItem('theme') || 'light-mode';
    let currentLang = localStorage.getItem('language') || document.documentElement.lang || 'ar';
    document.body.className = savedMode;
    document.body.classList.toggle('rtl', currentLang === 'ar');
    document.documentElement.setAttribute('lang', currentLang);
    document.documentElement.setAttribute('dir', currentLang === 'ar' ? 'rtl' : 'ltr');

    const modeToggle = document.getElementById('mode-toggle');
    const modeIcon = modeToggle?.querySelector('.mode-icon');
    const langToggle = document.getElementById('lang-toggle');
    const langIcon = langToggle?.querySelector('.lang-icon');

    // Initialize mode toggle button
    if (modeIcon) {
        modeIcon.textContent = savedMode === 'light-mode' ? '🌙' : '☀️';
        modeToggle.title = savedMode === 'light-mode' 
            ? translations[currentLang].modeToggleTitleLight 
            : translations[currentLang].modeToggleTitleDark;
    }

    // Initialize language toggle button
    if (langIcon) {
        langIcon.textContent = translations[currentLang].langToggleIcon;
        langToggle.title = translations[currentLang].langToggleTitle;
    }

    // Function to update translations dynamically
    function updateTranslations(lang) {
        // Update page title
        document.title = translations[lang].title;
        
        // Update header elements
        const logo = document.querySelector('.logo-container .logo');
        if (logo) logo.alt = translations[lang].logoAlt;
        
        // Update nav links more reliably
        const navLinks = document.querySelectorAll('.nav-links .nav-link');
        navLinks.forEach(link => {
            if (link.href.includes('products')) {
                link.textContent = translations[lang].productsLink;
            } else if (link.href.includes('login')) {
                link.textContent = translations[lang].loginLink;
            } else if (link.href.includes('logout')) {
                link.textContent = translations[lang].logoutLink;
            }
        });
        
        // Update footer
        const footerText = document.querySelector('.footer p');
        if (footerText) footerText.textContent = translations[lang].footerText;
        
        // Update toggle buttons
        if (langIcon) langIcon.textContent = translations[lang].langToggleIcon;
        if (langToggle) langToggle.title = translations[lang].langToggleTitle;
        if (modeToggle) {
            modeToggle.title = document.body.classList.contains('light-mode')
                ? translations[lang].modeToggleTitleLight
                : translations[lang].modeToggleTitleDark;
        }
    }

    // Initialize translations
    updateTranslations(currentLang);

    // Toggle light/dark mode
    modeToggle?.addEventListener('click', () => {
        const isLightMode = document.body.classList.contains('light-mode');
        const newMode = isLightMode ? 'dark-mode' : 'light-mode';
        
        // Update body class and icon
        document.body.className = newMode;
        document.body.classList.toggle('rtl', currentLang === 'ar');
        modeIcon.textContent = isLightMode ? '☀️' : '🌙';
        
        // Update title based on current language
        modeToggle.title = isLightMode 
            ? translations[currentLang].modeToggleTitleDark 
            : translations[lang].modeToggleTitleLight;
        
        // Save theme to localStorage
        localStorage.setItem('theme', newMode);
    });

    // Toggle language
    langToggle?.addEventListener('click', () => {
        const isArabic = currentLang === 'ar';
        const newLang = isArabic ? 'en' : 'ar';
        
        // Send language change request to server
        fetch(`/set-language/${newLang}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ language: newLang })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to switch language');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Update local language variable and UI
                currentLang = newLang;
                localStorage.setItem('language', newLang);
                
                // Update text direction
                document.body.classList.toggle('rtl', newLang === 'ar');
                document.documentElement.setAttribute('lang', newLang);
                document.documentElement.setAttribute('dir', newLang === 'ar' ? 'rtl' : 'ltr');
                
                // Update translations dynamically
                updateTranslations(newLang);
            } else {
                console.error('Language switch failed:', data.message);
            }
        })
        .catch(error => {
            console.error('Error switching language:', error);
            // Fallback: Update UI even if server request fails
            currentLang = newLang;
            localStorage.setItem('language', newLang);
            document.body.classList.toggle('rtl', newLang === 'ar');
            document.documentElement.setAttribute('lang', newLang);
            document.documentElement.setAttribute('dir', newLang === 'ar' ? 'rtl' : 'ltr');
            updateTranslations(newLang);
        });
    });
});