document.addEventListener('DOMContentLoaded', () => {
    console.log('Product_list.js loaded');
    const translations = {
        ar: {
            title: 'المنتجات - ترافيكو',
            logoAlt: 'شعار ترافيكو',
            productsLink: 'المنتجات',
            about_us: 'عنا',
            contact_us: 'تواصل معنا',
            loginLink: 'تسجيل الدخول',
            logoutLink: 'تسجيل الخروج',
            footerText: 'جميع الحقوق محفوظة © ترافيكو مقدم من شركة كريتيفتي كود للبرمجة 2025',
            modeToggleTitleLight: 'تبديل إلى الوضع المظلم',
            modeToggleTitleDark: 'تبديل إلى الوضع الفاتح',
            langToggleTitle: 'تبديل إلى الإنجليزية',
            langToggleIcon: '🇸🇦',
            heroTitle: 'تسوق منتجات ترافيكو المميزة',
            heroDescription: 'اكتشف تشكيلة فريدة من المنتجات المصممة بعناية، وانضم إلى مجتمع المسوقين والمصممين لتحقيق أرباحك!',
            productsTitle: 'المنتجات',
            addProduct: 'إضافة منتج',
            price: 'السعر',
            currency: 'جنيه',
            stock: 'المخزون',
            viewDetails: 'عرض التفاصيل',
            addToFavorites: 'إضافة إلى المفضلة',
            removeFromFavorites: 'إزالة من المفضلة',
            addToCart: 'إضافة إلى العربة',
            edit: 'تعديل',
            delete: 'حذف',
            noProducts: 'لا توجد منتجات متاحة',
            modeNotificationLight: 'تم تغيير الوضع إلى الفاتح',
            modeNotificationDark: 'تم تغيير الوضع إلى المظلم',
            langNotificationAr: 'تم تغيير اللغة إلى العربية',
            langNotificationEn: 'تم تغيير اللغة إلى الإنجليزية',
            langError: 'حدث خطأ أثناء تغيير اللغة'
        },
        en: {
            title: 'Products - Trafico',
            logoAlt: 'Trafico Logo',
            productsLink: 'Products',
            about_us: 'About Us',
            contact_us: 'Contact Us',
            loginLink: 'Login',
            logoutLink: 'Logout',
            footerText: 'All Rights Reserved © Trafico 2025 by Creativity Code Co.',
            modeToggleTitleLight: 'Switch to Dark Mode',
            modeToggleTitleDark: 'Switch to Light Mode',
            langToggleTitle: 'Switch to Arabic',
            langToggleIcon: '🇬🇧',
            heroTitle: 'Shop Trafico\'s Premium Products',
            heroDescription: 'Discover a unique collection of carefully designed products and join the community of marketers and designers to earn profits!',
            productsTitle: 'Products',
            addProduct: 'Add Product',
            price: 'Price',
            currency: 'EGP',
            stock: 'Stock',
            viewDetails: 'View Details',
            addToFavorites: 'Add to Favorites',
            removeFromFavorites: 'Remove from Favorites',
            addToCart: 'Add to Cart',
            edit: 'Edit',
            delete: 'Delete',
            noProducts: 'No products available',
            modeNotificationLight: 'Switched to Light Mode',
            modeNotificationDark: 'Switched to Dark Mode',
            langNotificationAr: 'Language changed to Arabic',
            langNotificationEn: 'Language changed to English',
            langError: 'Error occurred while changing language'
        }
    };

    // Load saved theme and language
    let savedMode = localStorage.getItem('theme') || 'light-mode';
    let currentLang = localStorage.getItem('language') || document.documentElement.lang || 'ar';
    document.body.className = savedMode;
    document.body.classList.toggle('rtl', currentLang === 'ar');
    document.documentElement.setAttribute('lang', currentLang);
    document.documentElement.setAttribute('dir', currentLang === 'ar' ? 'rtl' : 'ltr');

    // Log initial state
    console.log('Initial theme:', savedMode);
    console.log('Initial language:', currentLang);

    // Force update translations on page load
    updateTranslations(currentLang);

    // Initialize buttons
    const modeToggle = document.getElementById('mode-toggle');
    const modeIcon = modeToggle?.querySelector('.mode-icon');
    const langToggle = document.getElementById('lang-toggle');
    const langIcon = langToggle?.querySelector('.lang-icon');

    if (!modeToggle || !langToggle) {
        console.error('Mode or language toggle button not found in DOM');
    }

    // Initialize mode toggle button
    if (modeIcon && modeToggle) {
        modeIcon.textContent = savedMode === 'light-mode' ? '🌙' : '☀️';
        modeToggle.title = translations[currentLang][savedMode === 'light-mode' ? 'modeToggleTitleLight' : 'modeToggleTitleDark'];
    } else {
        console.error('Mode toggle or icon not found');
    }

    // Initialize language toggle button
    if (langIcon && langToggle) {
        langIcon.textContent = currentLang === 'ar' ? '🇸🇦' : '🇬🇧';
        langToggle.title = translations[currentLang].langToggleTitle;
    } else {
        console.error('Language toggle or icon not found');
    }

    // Function to show notifications
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: ${type === 'success' ? '#4CAF50' : '#F44336'};
            color: white;
            border-radius: 5px;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        document.body.appendChild(notification);
        setTimeout(() => notification.style.opacity = '1', 10);
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Function to update all translations dynamically
    function updateTranslations(lang) {
        try {
            // Update page title
            document.title = translations[lang].title;

            // Update header elements
            const logo = document.querySelector('.logo-container .logo');
            if (logo) logo.alt = translations[lang].logoAlt;

            const navLinks = document.querySelectorAll('.nav-links .nav-link');
            navLinks.forEach(link => {
                if (link.href.includes('products')) {
                    link.textContent = translations[lang].productsLink;
                } else if (link.href.includes('about_us')) {
                    link.textContent = translations[lang].about_us;
                } else if (link.href.includes('contact_us')) {
                    link.textContent = translations[lang].contact_us;
                } else if (link.href.includes('login')) {
                    link.textContent = translations[lang].loginLink;
                } else if (link.href.includes('logout')) {
                    link.textContent = translations[lang].logoutLink;
                }
            });

            // Update hero section
            const heroTitle = document.querySelector('.hero-content h1');
            if (heroTitle) heroTitle.textContent = translations[lang].heroTitle;
            
            const heroDescription = document.querySelector('.hero-content p');
            if (heroDescription) heroDescription.textContent = translations[lang].heroDescription;

            // Update products section
            const productsTitle = document.querySelector('.container h2');
            if (productsTitle) productsTitle.textContent = translations[lang].productsTitle;
            
            const addProductBtn = document.querySelector('.btn-primary[href*="product_add"]');
            if (addProductBtn) addProductBtn.textContent = translations[lang].addProduct;

            // Update product cards
            document.querySelectorAll('.product-card').forEach(card => {
                const priceEl = card.querySelector('.price-text');
                if (priceEl) {
                    const priceValue = priceEl.textContent.match(/[\d.]+/)?.[0] || '';
                    priceEl.textContent = `${translations[lang].price}: ${priceValue} ${translations[lang].currency}`;
                }
                
                const stockEl = card.querySelector('.stock-text');
                if (stockEl) {
                    const stockValue = stockEl.textContent.split(': ')[1];
                    stockEl.textContent = `${translations[lang].stock}: ${stockValue}`;
                }
                
                const viewDetailsBtn = card.querySelector('.btn-primary[href*="product_detail"]');
                if (viewDetailsBtn) viewDetailsBtn.textContent = translations[lang].viewDetails;
                
                const favoriteBtn = card.querySelector('.favorite-btn');
                if (favoriteBtn) {
                    favoriteBtn.textContent = favoriteBtn.textContent.includes(translations[lang].addToFavorites) ||
                                            favoriteBtn.textContent.includes(translations[lang].removeFromFavorites)
                        ? favoriteBtn.textContent.includes('إزالة') || favoriteBtn.textContent.includes('Remove')
                            ? translations[lang].removeFromFavorites
                            : translations[lang].addToFavorites
                        : translations[lang].addToFavorites;
                }
                
                const addToCartBtn = card.querySelector('.btn-primary[href*="add_to_cart"]');
                if (addToCartBtn) addToCartBtn.textContent = translations[lang].addToCart;
                
                const editBtn = card.querySelector('.btn-primary[href*="product_edit"]');
                if (editBtn) editBtn.textContent = translations[lang].edit;
                
                const deleteBtn = card.querySelector('.btn-primary[href*="product_delete"]');
                if (deleteBtn) deleteBtn.textContent = translations[lang].delete;
            });

            // Update no products message
            const noProducts = document.querySelector('.no-products');
            if (noProducts) noProducts.textContent = translations[lang].noProducts;

            // Update footer
            const footerText = document.querySelector('.footer p');
            if (footerText) footerText.textContent = translations[lang].footerText;

            // Update toggle buttons
            if (langIcon && langToggle) {
                langIcon.textContent = translations[lang].langToggleIcon;
                langToggle.title = translations[lang].langToggleTitle;
            }
            if (modeToggle && modeIcon) {
                modeToggle.title = document.body.classList.contains('light-mode')
                    ? translations[lang].modeToggleTitleLight
                    : translations[lang].modeToggleTitleDark;
            }
        } catch (error) {
            console.error('Error in updateTranslations:', error);
        }
    }

    // Toggle light/dark mode
    if (modeToggle) {
        modeToggle.addEventListener('click', () => {
            const isLightMode = document.body.classList.contains('light-mode');
            const newMode = isLightMode ? 'dark-mode' : 'light-mode';
            
            console.log('Toggling mode to:', newMode);
            document.body.className = newMode;
            if (modeIcon) {
                modeIcon.textContent = isLightMode ? '☀️' : '🌙';
            }
            modeToggle.title = isLightMode 
                ? translations[currentLang].modeToggleTitleDark 
                : translations[currentLang].modeToggleTitleLight;
            
            localStorage.setItem('theme', newMode);
            showNotification(translations[currentLang][isLightMode ? 'modeNotificationDark' : 'modeNotificationLight']);
        });
    }

    // Toggle language
    if (langToggle) {
        langToggle.addEventListener('click', () => {
            const isArabic = currentLang === 'ar';
            const newLang = isArabic ? 'en' : 'ar';
            
            console.log('Toggling language to:', newLang);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (csrfToken) {
                fetch(`/set-language/${newLang}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ language: newLang })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.status === 'success') {
                        currentLang = newLang;
                        localStorage.setItem('language', newLang);
                        document.body.classList.toggle('rtl', newLang === 'ar');
                        document.documentElement.setAttribute('lang', newLang);
                        document.documentElement.setAttribute('dir', newLang === 'ar' ? 'rtl' : 'ltr');
                        updateTranslations(newLang);
                        if (langIcon) langIcon.textContent = newLang === 'ar' ? '🇸🇦' : '🇬🇧';
                        if (langToggle) langToggle.title = translations[newLang].langToggleTitle;
                        showNotification(translations[newLang][newLang === 'ar' ? 'langNotificationAr' : 'langNotificationEn']);
                    } else {
                        console.error('Language switch failed:', data.message);
                        showNotification(translations[currentLang].langError, 'error');
                    }
                })
                .catch(error => {
                    console.error('Error switching language:', error);
                    showNotification(translations[currentLang].langError, 'error');
                    // Fallback: Update UI locally
                    currentLang = newLang;
                    localStorage.setItem('language', newLang);
                    document.body.classList.toggle('rtl', newLang === 'ar');
                    document.documentElement.setAttribute('lang', newLang);
                    document.documentElement.setAttribute('dir', newLang === 'ar' ? 'rtl' : 'ltr');
                    updateTranslations(newLang);
                    if (langIcon) langIcon.textContent = newLang === 'ar' ? '🇸🇦' : '🇬🇧';
                    if (langToggle) langToggle.title = translations[newLang].langToggleTitle;
                });
            } else {
                console.error('CSRF token not found');
                showNotification(translations[currentLang].langError, 'error');
                // Fallback: Update UI locally
                currentLang = newLang;
                localStorage.setItem('language', newLang);
                document.body.classList.toggle('rtl', newLang === 'ar');
                document.documentElement.setAttribute('lang', newLang);
                document.documentElement.setAttribute('dir', newLang === 'ar' ? 'rtl' : 'ltr');
                updateTranslations(newLang);
                if (langIcon) langIcon.textContent = newLang === 'ar' ? '🇸🇦' : '🇬🇧';
                if (langToggle) langToggle.title = translations[newLang].langToggleTitle;
            }
        });
    }

    // Animate product cards on scroll
    const cards = document.querySelectorAll('.product-card');
    if (cards.length > 0) {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animation = 'zoomIn 0.5s ease-out forwards';
                }
            });
        }, { threshold: 0.2 });
        cards.forEach(card => observer.observe(card));
    } else {
        console.warn('No product cards found for animation');
    }
});