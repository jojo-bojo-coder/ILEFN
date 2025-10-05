// Enhanced Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functionality
    initMobileMenu();
    initSmoothScrolling();
    initAnimations();
    initParallaxEffects();
    initCounterAnimations();

    // Header scroll effect
    initHeaderScrollEffect();
});

// Mobile menu functionality
function initMobileMenu() {
    const menuToggle = document.querySelector('.elementor-menu-toggle');
    const navMenu = document.querySelector('.elementor-nav-menu--main');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('elementor-nav-menu--dropdown');
            menuToggle.classList.toggle('elementor-active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
                navMenu.classList.remove('elementor-nav-menu--dropdown');
                menuToggle.classList.remove('elementor-active');
            }
        });
    }
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            // Don't prevent default if it's a button in a form or has a different purpose
            if (this.closest('form') || this.type === 'submit' || this.hasAttribute('onclick')) {
                return; // Let the form submit normally
            }

            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                const headerHeight = document.querySelector('header').offsetHeight || 0;
                const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Enhanced animation initialization
function initAnimations() {
    const animatedElements = document.querySelectorAll('.elementor-invisible');

    const observerOptions = {
        root: null,
        rootMargin: '-50px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                const delay = element.getAttribute('data-animation-delay') || 0;

                setTimeout(() => {
                    element.classList.add('elementor-in-viewport');
                    element.classList.remove('elementor-invisible');
                }, delay);

                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// Header scroll effect
function initHeaderScrollEffect() {
    const header = document.querySelector('header');
    let lastScrollTop = 0;

    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        // Hide header when scrolling down, show when scrolling up
        if (scrollTop > lastScrollTop && scrollTop > 200) {
            header.style.transform = 'translateY(-100%)';
        } else {
            header.style.transform = 'translateY(0)';
        }

        lastScrollTop = scrollTop;
    });
}

// Parallax effects for hero section
function initParallaxEffects() {
    const heroSection = document.querySelector('.elementor-element-5def900');

    if (heroSection) {
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const parallax = scrolled * 0.5;

            heroSection.style.backgroundPosition = `center ${parallax}px`;
        });
    }
}

// Enhanced counter animations with intersection observer
function initCounterAnimations() {
    const counters = document.querySelectorAll('.elementor-counter-number');

    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-to-value')) || 0;
        const duration = parseInt(counter.getAttribute('data-duration')) || 2000;
        let hasAnimated = false;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !hasAnimated) {
                    hasAnimated = true;
                    animateCounter(counter, target, duration);
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.5
        });

        observer.observe(counter);
    });
}

// Counter animation function
function animateCounter(counter, target, duration) {
    let startTime = null;
    const startValue = 0;

    function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);

        // Easing function for smooth animation
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = Math.floor(easeOutQuart * target);

        counter.textContent = currentValue.toLocaleString('en-US');

        if (progress < 1) {
            requestAnimationFrame(animate);
        } else {
            counter.textContent = target.toLocaleString('en-US');
        }
    }

    requestAnimationFrame(animate);
}

// Button hover effects
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.edublink-button-item');

    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.02)';
        });

        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});

// Add loading animation
window.addEventListener('load', function() {
    document.body.classList.add('loaded');

    // Initialize any Elementor-specific functionality if available
    if (typeof jQuery !== 'undefined' && jQuery.fn.elementor) {
        console.log('Elementor loaded and initialized');
    }

    // Trigger initial animations for elements in viewport
    const initialElements = document.querySelectorAll('.elementor-invisible');
    initialElements.forEach(element => {
        const rect = element.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            const delay = element.getAttribute('data-animation-delay') || 0;
            setTimeout(() => {
                element.classList.add('elementor-in-viewport');
                element.classList.remove('elementor-invisible');
            }, delay);
        }
    });
});

// Keyboard navigation support
document.addEventListener('keydown', function(e) {
    // Handle escape key for mobile menu
    if (e.key === 'Escape') {
        const navMenu = document.querySelector('.elementor-nav-menu--main');
        const menuToggle = document.querySelector('.elementor-menu-toggle');

        if (navMenu && navMenu.classList.contains('elementor-nav-menu--dropdown')) {
            navMenu.classList.remove('elementor-nav-menu--dropdown');
            if (menuToggle) {
                menuToggle.classList.remove('elementor-active');
            }
        }
    }
});

// Resize handler for responsive adjustments
window.addEventListener('resize', function() {
    // Recalculate any size-dependent elements
    const counters = document.querySelectorAll('.elementor-counter');
    counters.forEach(counter => {
        // Adjust counter card heights if needed
        if (window.innerWidth < 768) {
            counter.style.marginBottom = '20px';
        } else {
            counter.style.marginBottom = '';
        }
    });
});

// Add CSS classes for enhanced styling
document.addEventListener('DOMContentLoaded', function() {
    // Add scrolled class to header initially if page is already scrolled
    if (window.pageYOffset > 100) {
        document.querySelector('header').classList.add('scrolled');
    }

    // Add loaded class to body for CSS animations
    setTimeout(() => {
        document.body.classList.add('page-loaded');
    }, 100);
});

// Function to set active menu item based on current page
function setActiveMenuItem() {
    const currentPage = window.location.pathname;
    const menuItems = document.querySelectorAll('.elementor-nav-menu li a');

    menuItems.forEach(item => {
        const href = item.getAttribute('href');

        // Remove active class from all items first
        item.classList.remove('elementor-item-active');
        item.parentElement.classList.remove('current-menu-item');

        // Check if this link matches the current page
        if (href === currentPage ||
            (currentPage === '/' && href === '/') ||
            (currentPage.includes(href) && href !== '/')) {
            item.classList.add('elementor-item-active');
            item.parentElement.classList.add('current-menu-item');
        }
    });
}

// Call this function when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setActiveMenuItem();

    // Also handle hash links (anchor links)
    const hash = window.location.hash;
    if (hash) {
        const targetItem = document.querySelector(`.elementor-nav-menu li a[href="${hash}"]`);
        if (targetItem) {
            // Remove active class from all items
            document.querySelectorAll('.elementor-nav-menu li a').forEach(item => {
                item.classList.remove('elementor-item-active');
                item.parentElement.classList.remove('current-menu-item');
            });

            // Add active class to the target item
            targetItem.classList.add('elementor-item-active');
            targetItem.parentElement.classList.add('current-menu-item');
        }
    }
});