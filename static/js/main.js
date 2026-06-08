// Travel Agency Management System - Minimal JS
// Most interactivity is handled by inline scripts and Alpine.js-compatible patterns

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 4 seconds
    var flashContainer = document.querySelector('.fixed.top-20.right-4');
    if (flashContainer && flashContainer.children.length > 0) {
        setTimeout(function() {
            flashContainer.style.transition = 'opacity 0.3s ease';
            flashContainer.style.opacity = '0';
            setTimeout(function() { flashContainer.remove(); }, 300);
        }, 4000);
    }
});
