document.addEventListener('DOMContentLoaded', () => {
    console.log('Cart.js loaded successfully');

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
            showNotification(isLightMode ? 'تم تغيير الوضع إلى المظلم' : 'تم تغيير الوضع إلى الفاتح');
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
            }).then(response => {
                if (!response.ok) throw new Error('Language switch failed');
                document.documentElement.lang = newLang;
                document.documentElement.dir = isArabic ? 'ltr' : 'rtl';
                currentLang = newLang;
                langIcon.textContent = isArabic ? '🇬🇧' : '🇸🇦';
                document.querySelectorAll('[data-en]').forEach(element => {
                    const enText = element.getAttribute('data-en');
                    const arText = element.getAttribute('data-ar') || element.textContent;
                    element.textContent = isArabic ? enText : arText;
                    element.setAttribute('data-ar', arText);
                    if (element.tagName === 'IMG') element.alt = isArabic ? enText : arText;
                });
                modeToggle.title = isArabic ? modeToggle.getAttribute('data-title-en') : modeToggle.getAttribute('data-title-ar');
                langToggle.title = isArabic ? langToggle.getAttribute('data-title-en') : langToggle.getAttribute('data-title-ar');
                showNotification(isArabic ? 'Language changed to English' : 'تم تغيير اللغة إلى العربية');
            }).catch(error => {
                console.error('Error switching language:', error);
                showNotification(isArabic ? 'Error changing language' : 'خطأ أثناء تغيير اللغة', 'error');
            });
        });
    } else {
        console.error('Language toggle button not found');
    }

    // تحديث تكلفة الشحن وإجمالي السعر عند تغيير المحافظة
    const governorateSelect = document.getElementById('governorate');
    const shippingCostInput = document.getElementById('shipping_cost');
    const totalPriceSpan = document.getElementById('total-price');
    const subtotal = parseFloat(window.totalCartPrice);

    if (governorateSelect && shippingCostInput && totalPriceSpan) {
        governorateSelect.addEventListener('change', () => {
            const selectedOption = governorateSelect.options[governorateSelect.selectedIndex];
            const shippingCost = parseFloat(selectedOption.getAttribute('data-shipping-cost'));
            shippingCostInput.value = shippingCost.toFixed(2);
            document.getElementById('shipping-cost').textContent = shippingCost.toFixed(2);
            totalPriceSpan.textContent = (subtotal + shippingCost).toFixed(2);
        });
    }

    // دالة الإشعارات
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
});