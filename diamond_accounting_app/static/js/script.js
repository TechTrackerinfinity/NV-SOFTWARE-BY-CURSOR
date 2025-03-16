// Wait for the DOM to be fully loaded
// Debug configuration
const DEBUG = {
    enabled: true,  // Set to false in production
    logLevel: 'debug',  // 'debug', 'info', 'warn', 'error'
    
    // Custom logging functions
    debug: function(message, data) {
        if (this.enabled && ['debug'].includes(this.logLevel)) {
            console.debug(`[DEBUG] ${message}`, data || '');
        }
    },
    
    info: function(message, data) {
        if (this.enabled && ['debug', 'info'].includes(this.logLevel)) {
            console.info(`[INFO] ${message}`, data || '');
        }
    },
    
    warn: function(message, data) {
        if (this.enabled && ['debug', 'info', 'warn'].includes(this.logLevel)) {
            console.warn(`[WARN] ${message}`, data || '');
        }
    },
    
    error: function(message, data) {
        if (this.enabled && ['debug', 'info', 'warn', 'error'].includes(this.logLevel)) {
            console.error(`[ERROR] ${message}`, data || '');
        }
    },
    
    // Performance monitoring
    startTimer: function(label) {
        if (this.enabled) {
            console.time(label);
        }
    },
    
    endTimer: function(label) {
        if (this.enabled) {
            console.timeEnd(label);
        }
    },
    
    // DOM element inspection
    inspectElement: function(selector, message) {
        if (this.enabled) {
            const element = document.querySelector(selector);
            console.log(`[INSPECT] ${message || selector}:`, element);
            return element;
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    DEBUG.info('DOM fully loaded');
    DEBUG.startTimer('Page Initialization');
    
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

    // Enhanced form validation with detailed error messages
    const forms = document.querySelectorAll('.needs-validation');
    if (forms.length > 0) {
        Array.from(forms).forEach(form => {
            // Add input event listeners for real-time validation feedback
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    // Clear previous error messages
                    const feedbackElement = this.nextElementSibling;
                    if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
                        if (this.checkValidity()) {
                            feedbackElement.textContent = '';
                        }
                    }
                    
                    // Add custom validation for specific input types
                    if (this.type === 'number' && this.hasAttribute('min')) {
                        const min = parseFloat(this.getAttribute('min'));
                        const value = parseFloat(this.value);
                        if (!isNaN(value) && value < min) {
                            this.setCustomValidity(`Value must be at least ${min}`);
                        } else {
                            this.setCustomValidity('');
                        }
                    }
                });
            });
            
            // Form submission validation
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    // Show detailed error messages for each invalid field
                    const invalidInputs = form.querySelectorAll(':invalid');
                    invalidInputs.forEach(input => {
                        const feedbackElement = input.nextElementSibling;
                        if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
                            if (input.validity.valueMissing) {
                                feedbackElement.textContent = 'This field is required';
                            } else if (input.validity.typeMismatch) {
                                feedbackElement.textContent = 'Please enter a valid format';
                            } else if (input.validity.rangeUnderflow) {
                                feedbackElement.textContent = `Value must be at least ${input.min}`;
                            } else if (input.validity.rangeOverflow) {
                                feedbackElement.textContent = `Value must be at most ${input.max}`;
                            }
                        }
                        
                        // Scroll to the first invalid element
                        invalidInputs[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
                    });
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

    // AJAX form submission with error handling
    const ajaxForms = document.querySelectorAll('form[data-ajax="true"]');
    if (ajaxForms.length > 0) {
        DEBUG.info(`Found ${ajaxForms.length} AJAX forms`);
        
        ajaxForms.forEach((form, index) => {
            DEBUG.debug(`Initializing AJAX form #${index + 1}`, form);
            
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                DEBUG.info(`AJAX form submitted: ${form.id || 'unnamed form'}`);
                DEBUG.startTimer(`AJAX request: ${form.id || 'unnamed form'}`);
                
                // Show loading indicator
                const submitButton = form.querySelector('button[type="submit"]');
                const originalButtonText = submitButton.innerHTML;
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                // Clear previous error messages
                const errorContainer = form.querySelector('.ajax-error');
                if (errorContainer) {
                    errorContainer.textContent = '';
                    errorContainer.style.display = 'none';
                }
                
                // Collect form data
                const formData = new FormData(form);
                
                // Log form data for debugging
                if (DEBUG.enabled) {
                    DEBUG.debug('Form data:', {});
                    for (let [key, value] of formData.entries()) {
                        DEBUG.debug(`  ${key}: ${value}`);
                    }
                }
                
                // Send AJAX request
                fetch(form.action, {
                    method: form.method,
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    DEBUG.debug(`Response status: ${response.status}`);
                    
                    if (!response.ok) {
                        throw new Error(`Server responded with status: ${response.status}`);
                    }
                    
                    // Check if response is JSON
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return response.json();
                    } else {
                        throw new Error('Expected JSON response but got: ' + contentType);
                    }
                })
                .then(data => {
                    DEBUG.debug('Response data:', data);
                    
                    // Handle successful response
                    if (data.success) {
                        DEBUG.info('Request successful');
                        
                        // Show success message
                        if (data.message) {
                            // Create a flash message
                            const flashContainer = document.getElementById('flash-messages');
                            if (flashContainer) {
                                const alertDiv = document.createElement('div');
                                alertDiv.className = 'alert alert-success alert-dismissible fade show';
                                alertDiv.role = 'alert';
                                alertDiv.innerHTML = `
                                    ${data.message}
                                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                `;
                                flashContainer.appendChild(alertDiv);
                                
                                // Auto-close after 5 seconds
                                setTimeout(() => {
                                    const closeButton = alertDiv.querySelector('.btn-close');
                                    if (closeButton) {
                                        closeButton.click();
                                    }
                                }, 5000);
                            }
                        }
                        
                        // Redirect if specified
                        if (data.redirect) {
                            DEBUG.info(`Redirecting to: ${data.redirect}`);
                            window.location.href = data.redirect;
                        } else if (form.dataset.resetOnSuccess === 'true') {
                            // Reset form if specified
                            DEBUG.info('Resetting form');
                            form.reset();
                        }
                    } else {
                        DEBUG.warn('Request returned success: false', data);
                        
                        // Handle validation errors
                        if (data.errors) {
                            DEBUG.warn('Validation errors:', data.errors);
                            
                            // Display field-specific errors
                            Object.keys(data.errors).forEach(field => {
                                const input = form.querySelector(`[name="${field}"]`);
                                if (input) {
                                    input.classList.add('is-invalid');
                                    const feedbackElement = input.nextElementSibling;
                                    if (feedbackElement && feedbackElement.classList.contains('invalid-feedback')) {
                                        feedbackElement.textContent = data.errors[field];
                                    }
                                } else {
                                    DEBUG.error(`Field not found: ${field}`);
                                }
                            });
                        }
                        
                        // Display general error message
                        if (data.message && errorContainer) {
                            errorContainer.textContent = data.message;
                            errorContainer.style.display = 'block';
                        }
                    }
                })
                .catch(error => {
                    DEBUG.error('Error submitting form:', error);
                    
                    // Display error message
                    if (errorContainer) {
                        errorContainer.textContent = 'An error occurred while processing your request. Please try again.';
                        errorContainer.style.display = 'block';
                    }
                })
                .finally(() => {
                    // Restore submit button
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalButtonText;
                    
                    DEBUG.endTimer(`AJAX request: ${form.id || 'unnamed form'}`);
                });
            });
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