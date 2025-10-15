// Coupon copy functionality for Django Admin
function copyCouponCode(couponCode) {
    console.log('Copying coupon code:', couponCode);
    
    // Try modern clipboard API first
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(couponCode).then(function() {
            showCopySuccess();
        }).catch(function(err) {
            console.error('Clipboard API failed:', err);
            fallbackCopy(couponCode);
        });
    } else {
        // Fallback for older browsers or non-HTTPS
        fallbackCopy(couponCode);
    }
}

function fallbackCopy(couponCode) {
    const textArea = document.createElement('textarea');
    textArea.value = couponCode;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showCopySuccess();
        } else {
            alert('Please copy the coupon code manually: ' + couponCode);
        }
    } catch (err) {
        alert('Please copy the coupon code manually: ' + couponCode);
    }
    document.body.removeChild(textArea);
}

function showCopySuccess() {
    // Show notification
    showNotification('✅ Coupon code copied to clipboard!', 'success');
    
    // Visual feedback for all copy buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        if (button.textContent === 'Copy Code') {
            const originalText = button.textContent;
            const originalBg = button.style.backgroundColor;
            
            button.textContent = '✓ Copied!';
            button.style.backgroundColor = '#28a745';
            button.style.color = 'white';
            button.disabled = true;
            
            setTimeout(function() {
                button.textContent = originalText;
                button.style.backgroundColor = originalBg;
                button.style.color = '';
                button.disabled = false;
            }, 2000);
        }
    });
}

function showNotification(message, type) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.coupon-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = 'coupon-notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#28a745' : '#dc3545'};
        color: white;
        padding: 12px 20px;
        border-radius: 5px;
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    document.body.appendChild(notification);
    
    setTimeout(function() {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 3000);
}

// Initialize when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('META_SHARK Coupon Copy script loaded');
});