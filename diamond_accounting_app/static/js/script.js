// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

    // Check for saved sidebar state
    if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        document.body.classList.add('sb-sidenav-toggled');
    }

    // Initialize Bootstrap components safely
    // Initialize tooltips
    try {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        if (tooltipTriggerList.length > 0 && typeof bootstrap !== 'undefined') {
            const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    } catch (error) {
        console.warn('Error initializing tooltips:', error);
    }

    // Initialize popovers
    try {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        if (popoverTriggerList.length > 0 && typeof bootstrap !== 'undefined') {
            const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        }
    } catch (error) {
        console.warn('Error initializing popovers:', error);
    }

    // Add fade-in animation to cards with performance optimization
    // Use requestAnimationFrame for better performance
    requestAnimationFrame(() => {
        const cards = document.querySelectorAll('.card');
        if (cards.length > 0) {
            cards.forEach((card, index) => {
                // Stagger animations for better performance
                setTimeout(() => {
                    card.classList.add('fade-in');
                }, index * 50); // 50ms delay between each card
            });
        }
    });

    // Format currency in tables
    const currencyCells = document.querySelectorAll('td[data-type="currency"]');
    if (currencyCells.length > 0) {
        currencyCells.forEach(cell => {
            const value = parseFloat(cell.textContent);
            if (!isNaN(value)) {
                cell.textContent = '$' + value.toFixed(2);
            }
        });
    }

    // Handle form submission with validation
    const forms = document.querySelectorAll('.needs-validation');
    if (forms.length > 0) {
        Array.from(forms).forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }

    // Add event listener to flash message close button
    const flashMessages = document.querySelectorAll('.alert-dismissible');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            // Add fade-in animation
            message.classList.add('fade-in');
            
            // Auto-close after 5 seconds
            setTimeout(() => {
                const closeButton = message.querySelector('.btn-close');
                if (closeButton) {
                    closeButton.click();
                }
            }, 5000);
        });
    }

    // Use event delegation for common actions
    // Add confirmation for delete actions
    document.addEventListener('click', function(e) {
        if (e.target && e.target.closest('.btn-delete')) {
            if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
                e.preventDefault();
            }
        }
        
        // Print functionality
        if (e.target && e.target.closest('.btn-print')) {
            window.print();
        }
    });

    // Responsive table handling
    const tables = document.querySelectorAll('.table');
    if (tables.length > 0) {
        tables.forEach(table => {
            if (table.offsetWidth > table.parentElement.offsetWidth) {
                table.parentElement.style.overflowX = 'auto';
            }
        });
    }
    
    // Remove hover effect on sidebar items (previously added hover effects)
    const sidebarItems = document.querySelectorAll('.list-group-item');
    if (sidebarItems.length > 0) {
        // No hover effects - removed to prevent any movement or bouncing
    }
    
    // Add animation to dropdown menus
    const dropdowns = document.querySelectorAll('.dropdown');
    if (dropdowns.length > 0) {
        dropdowns.forEach(dropdown => {
            const menu = dropdown.querySelector('.dropdown-menu');
            if (menu) {
                dropdown.addEventListener('show.bs.dropdown', function() {
                    menu.classList.add('fade-in');
                });
            }
        });
    }
    
    // Add smooth scrolling to all links with hash
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    if (anchorLinks.length > 0) {
        anchorLinks.forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                const href = this.getAttribute('href');
                if (href !== "#" && href.startsWith('#')) {
                    const targetElement = document.querySelector(href);
                    if (targetElement) {
                        e.preventDefault();
                        targetElement.scrollIntoView({
                            behavior: 'smooth'
                        });
                    }
                }
            });
        });
    }
    
    // Add animation to page transitions
    window.addEventListener('pageshow', function() {
        document.body.classList.add('fade-in');
    });
    
    // Dark Mode Toggle with improved accessibility
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        // Check for saved theme preference or respect OS preference
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        const storedTheme = localStorage.getItem('theme');
        
        // Function to update UI for dark mode
        const updateDarkModeUI = (isDarkMode) => {
            if (isDarkMode) {
                document.body.classList.add('dark-mode');
                darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                darkModeToggle.setAttribute('aria-label', 'Switch to light mode');
            } else {
                document.body.classList.remove('dark-mode');
                darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                darkModeToggle.setAttribute('aria-label', 'Switch to dark mode');
            }
        };
        
        // Set initial state
        updateDarkModeUI(storedTheme === 'dark' || (!storedTheme && prefersDarkScheme.matches));
        
        // Toggle dark mode
        darkModeToggle.addEventListener('click', () => {
            const isDarkMode = document.body.classList.toggle('dark-mode');
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
            updateDarkModeUI(isDarkMode);
        });
        
        // Listen for OS theme changes
        prefersDarkScheme.addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                updateDarkModeUI(e.matches);
            }
        });
    }
}); 