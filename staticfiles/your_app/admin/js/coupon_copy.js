document.addEventListener('DOMContentLoaded', function() {
    // Add copy functionality to coupon code buttons
    const copyButtons = document.querySelectorAll('button[onclick*="navigator.clipboard.writeText"]');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = button.textContent;
            const originalBackground = button.style.backgroundColor;
            const originalColor = button.style.color;
            
            // Extract coupon code from onclick attribute
            const onclickContent = button.getAttribute('onclick');
            const match = onclickContent.match(/navigator\.clipboard\.writeText\('([^']+)'\)/);
            
            if (match && match[1]) {
                const couponCode = match[1];
                
                // Copy to clipboard
                navigator.clipboard.writeText(couponCode).then(function() {
                    button.textContent = 'Copied!';
                    button.style.backgroundColor = '#28a745';
                    button.style.color = 'white';
                    
                    setTimeout(function() {
                        button.textContent = originalText;
                        button.style.backgroundColor = originalBackground;
                        button.style.color = originalColor;
                    }, 2000);
                }).catch(function(err) {
                    console.error('Failed to copy: ', err);
                    alert('Failed to copy coupon code: ' + err);
                });
            }
        });
    });
});
