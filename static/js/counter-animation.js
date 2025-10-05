// Counter animation
document.addEventListener('DOMContentLoaded', function() {
    const counters = document.querySelectorAll('.elementor-counter-number');

    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-to-value'));
        const duration = parseInt(counter.getAttribute('data-duration') || 2000);
        let startTime = null;

        function animateCounter(timestamp) {
            if (!startTime) startTime = timestamp;
            const progress = Math.min((timestamp - startTime) / duration, 1);

            counter.textContent = Math.floor(progress * target).toLocaleString('en-US');

            if (progress < 1) {
                requestAnimationFrame(animateCounter);
            }
        }

        // Start animation when element is in viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    requestAnimationFrame(animateCounter);
                    observer.unobserve(entry.target);
                }
            });
        });

        observer.observe(counter);
    });
});