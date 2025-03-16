// Charts for Diamond Accounting App
document.addEventListener('DOMContentLoaded', function() {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded. Charts will not be displayed.');
        return;
    }

    // Cache chart data to avoid redundant calculations
    const chartData = {
        monthly: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            purchases: [12000, 19000, 15000, 25000, 22000, 30000, 28000, 25000, 30000, 35000, 28000, 32000],
            sales: [15000, 22000, 18000, 28000, 25000, 35000, 32000, 30000, 35000, 40000, 35000, 38000]
        },
        quarterly: {
            labels: ['Q1', 'Q2', 'Q3', 'Q4'],
            purchases: [46000, 77000, 83000, 95000],
            sales: [55000, 88000, 97000, 113000]
        },
        yearly: {
            labels: ['2020', '2021', '2022', '2023', '2024'],
            purchases: [180000, 220000, 260000, 300000, 350000],
            sales: [210000, 250000, 290000, 340000, 400000]
        }
    };

    // Set default Chart.js options with performance optimizations
    Chart.defaults.font.family = "'Poppins', 'Segoe UI', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#6c757d';
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    Chart.defaults.plugins.tooltip.titleFont = { weight: 'bold' };
    Chart.defaults.plugins.legend.position = 'top';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 15;
    Chart.defaults.elements.line.tension = 0.4;
    Chart.defaults.elements.line.borderWidth = 3;
    Chart.defaults.elements.point.radius = 4;
    Chart.defaults.elements.point.hoverRadius = 6;
    Chart.defaults.elements.bar.borderRadius = 4;
    
    // Optimize rendering
    Chart.defaults.animation = {
        duration: 800,
        easing: 'linear'
    };
    
    // Currency formatter for consistent display
    const currencyFormatter = new Intl.NumberFormat('en-US', { 
        style: 'currency', 
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });

    // Business Performance Chart
    const initPerformanceChart = () => {
        const performanceChartEl = document.getElementById('performanceChart');
        if (!performanceChartEl) return null;
        
        try {
            const ctx = performanceChartEl.getContext('2d');
            if (!ctx) {
                console.warn('Could not get 2D context for performance chart');
                return null;
            }
            
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.monthly.labels,
                    datasets: [
                        {
                            label: 'Purchases',
                            data: chartData.monthly.purchases,
                            borderColor: '#4361ee',
                            backgroundColor: 'rgba(67, 97, 238, 0.1)',
                            fill: true
                        },
                        {
                            label: 'Sales',
                            data: chartData.monthly.sales,
                            borderColor: '#2ec4b6',
                            backgroundColor: 'rgba(46, 196, 182, 0.1)',
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: false,
                            text: 'Business Performance'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += currencyFormatter.format(context.parsed.y);
                                    }
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            
            return chart;
        } catch (error) {
            console.error('Error initializing performance chart:', error);
            return null;
        }
    };

    // Initialize performance chart
    const performanceChart = initPerformanceChart();

    // Handle period buttons with debouncing to prevent excessive updates
    if (performanceChart) {
        let debounceTimer;
        const periodButtons = document.querySelectorAll('[data-chart-period]');
        
        periodButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Clear any pending updates
                if (debounceTimer) clearTimeout(debounceTimer);
                
                const period = this.getAttribute('data-chart-period');
                if (!chartData[period]) return;
                
                // Remove active class from all buttons
                periodButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Debounce the chart update to prevent excessive redraws
                debounceTimer = setTimeout(() => {
                    // Update chart data
                    performanceChart.data.labels = chartData[period].labels;
                    performanceChart.data.datasets[0].data = chartData[period].purchases;
                    performanceChart.data.datasets[1].data = chartData[period].sales;
                    performanceChart.update();
                }, 100);
            });
        });
    }

    // Profit Distribution Chart
    const initProfitChart = () => {
        const profitChartEl = document.getElementById('profitChart');
        if (!profitChartEl) return null;
        
        try {
            const ctx = profitChartEl.getContext('2d');
            if (!ctx) {
                console.warn('Could not get 2D context for profit chart');
                return null;
            }
            
            return new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Round Cut', 'Princess Cut', 'Emerald Cut', 'Cushion Cut', 'Other'],
                    datasets: [{
                        data: [35, 25, 20, 15, 5],
                        backgroundColor: [
                            '#4361ee',
                            '#2ec4b6',
                            '#ff9f1c',
                            '#e63946',
                            '#4cc9f0'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${label}: ${percentage}%`;
                                }
                            }
                        }
                    },
                    cutout: '70%'
                }
            });
        } catch (error) {
            console.error('Error initializing profit chart:', error);
            return null;
        }
    };

    // Initialize profit chart
    const profitChart = initProfitChart();

    // Transaction History Chart
    const initTransactionChart = () => {
        const transactionChartEl = document.getElementById('transactionChart');
        if (!transactionChartEl) return null;
        
        try {
            const ctx = transactionChartEl.getContext('2d');
            if (!ctx) {
                console.warn('Could not get 2D context for transaction chart');
                return null;
            }
            
            return new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [
                        {
                            label: 'Purchases',
                            data: [12, 19, 15, 25, 22, 30],
                            backgroundColor: 'rgba(67, 97, 238, 0.7)',
                            borderRadius: 4
                        },
                        {
                            label: 'Sales',
                            data: [10, 15, 12, 20, 18, 25],
                            backgroundColor: 'rgba(46, 196, 182, 0.7)',
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: false,
                            text: 'Transaction History'
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error initializing transaction chart:', error);
            return null;
        }
    };

    // Initialize transaction chart
    const transactionChart = initTransactionChart();
    
    // Handle window resize events to properly resize charts
    let resizeTimer;
    window.addEventListener('resize', function() {
        // Debounce resize events
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (performanceChart) performanceChart.resize();
            if (profitChart) profitChart.resize();
            if (transactionChart) transactionChart.resize();
        }, 250);
    });
}); 