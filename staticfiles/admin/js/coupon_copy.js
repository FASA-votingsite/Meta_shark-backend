// static/admin/js/coupon_copy.js
(function() {
    'use strict';
    
    function initCouponCopy() {
        console.log('🎯 Initializing coupon copy functionality...');
        
        // Function to copy coupon code
        function copyCouponCode(couponCode) {
            console.log('📋 Copying coupon code:', couponCode);
            
            // Create a temporary textarea element
            const textArea = document.createElement('textarea');
            textArea.value = couponCode;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                // Try using the modern clipboard API first
                if (navigator.clipboard && window.isSecureContext) {
                    navigator.clipboard.writeText(couponCode).then(function() {
                        showCopySuccess(couponCode);
                    }).catch(function(err) {
                        console.error('Clipboard API failed:', err);
                        fallbackCopy(couponCode);
                    });
                } else {
                    // Fallback for older browsers
                    fallbackCopy(couponCode);
                }
            } catch (err) {
                console.error('Copy failed:', err);
                fallbackCopy(couponCode);
            } finally {
                // Clean up
                document.body.removeChild(textArea);
            }
        }
        
        function fallbackCopy(couponCode) {
            const textArea = document.createElement('textarea');
            textArea.value = couponCode;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    showCopySuccess(couponCode);
                } else {
                    showCopyError(couponCode, 'Copy failed');
                }
            } catch (err) {
                showCopyError(couponCode, 'Copy not supported');
            } finally {
                document.body.removeChild(textArea);
            }
        }
        
        function showCopySuccess(couponCode) {
            const statusElement = document.getElementById('copy-status-' + couponCode);
            if (statusElement) {
                statusElement.textContent = '✅ Copied!';
                statusElement.style.color = 'green';
                
                // Reset after 2 seconds
                setTimeout(function() {
                    statusElement.textContent = '';
                }, 2000);
            }
            
            // Also update the button if it exists
            const button = document.querySelector('.copy-coupon-btn[data-coupon="' + couponCode + '"]');
            if (button) {
                const originalHTML = button.innerHTML;
                button.innerHTML = '✅ Copied!';
                button.style.background = '#28a745';
                
                setTimeout(function() {
                    button.innerHTML = originalHTML;
                    button.style.background = '#417690';
                }, 2000);
            }
        }
        
        function showCopyError(couponCode, message) {
            const statusElement = document.getElementById('copy-status-' + couponCode);
            if (statusElement) {
                statusElement.textContent = '❌ ' + message;
                statusElement.style.color = 'red';
                
                setTimeout(function() {
                    statusElement.textContent = '';
                }, 3000);
            }
        }
        
        // Add event listeners to all copy buttons
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('copy-coupon-btn')) {
                e.preventDefault();
                const couponCode = e.target.getAttribute('data-coupon');
                copyCouponCode(couponCode);
            }
        });
        
        // Also handle the old onclick method for backward compatibility
        window.copyCouponCode = copyCouponCode;
        
        console.log('✅ Coupon copy functionality initialized');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCouponCopy);
    } else {
        initCouponCopy();
    }
})();