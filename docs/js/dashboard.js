// Dashboard JavaScript
let statistics = null;

// Load statistics data
async function loadStatistics() {
    try {
        const response = await fetch('data/statistics.json');
        const data = await response.json();
        statistics = data.statistics;
        displayStatistics();
        createCharts();
    } catch (error) {
        console.error('Error loading statistics:', error);
        document.getElementById('stats-overview').innerHTML = 
            '<p style="color: red;">Error loading statistics. Please ensure data/statistics.json exists.</p>';
    }
}

// Display statistics
function displayStatistics() {
    if (!statistics) return;

    document.getElementById('total-content').textContent = 
        statistics.total_content.toLocaleString();
    
    document.getElementById('geo-restricted').textContent = 
        statistics.geo_restricted_count.toLocaleString();
    
    document.getElementById('accessible').textContent = 
        statistics.accessible_count.toLocaleString();
    
    document.getElementById('restriction-percentage').textContent = 
        statistics.geo_restricted_percentage.toFixed(1) + '%';
    
    // Format last updated date
    if (statistics.last_check) {
        const date = new Date(statistics.last_check);
        document.getElementById('last-updated').textContent = 
            date.toLocaleString();
    }
}

// Create charts
function createCharts() {
    if (!statistics) return;

    // Status Chart (Pie)
    const statusCtx = document.getElementById('status-chart');
    if (statusCtx) {
        new Chart(statusCtx, {
            type: 'pie',
            data: {
                labels: ['Accessible', 'Geo-Restricted', 'Unknown'],
                datasets: [{
                    data: [
                        statistics.accessible_count,
                        statistics.geo_restricted_count,
                        statistics.unknown_count
                    ],
                    backgroundColor: [
                        '#00D7B6',  // Primary teal for accessible
                        '#FF6B6B',  // Softer coral-red for restricted
                        '#95a5a6'   // Grey for unknown
                    ],
                    borderWidth: 2,
                    borderColor: '#fff',
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Type Chart (Bar)
    const typeCtx = document.getElementById('type-chart');
    if (typeCtx && statistics.by_type) {
        const types = Object.keys(statistics.by_type);
        const counts = Object.values(statistics.by_type);
        
        new Chart(typeCtx, {
            type: 'bar',
            data: {
                labels: types.map(t => t.charAt(0).toUpperCase() + t.slice(1)),
                datasets: [{
                    label: 'Content Count',
                    data: counts,
                    backgroundColor: '#00D7B6',
                    borderColor: '#00b89a',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', loadStatistics);
