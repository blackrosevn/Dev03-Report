// Vinatex Report Portal - Charts

// Create a pie chart
function createPieChart(canvasId, labels, data, backgroundColors, borderColors) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Default colors if not provided
    const defaultBackgroundColors = [
        'rgba(40, 167, 69, 0.8)',
        'rgba(255, 193, 7, 0.8)',
        'rgba(220, 53, 69, 0.8)',
        'rgba(13, 110, 253, 0.8)',
        'rgba(108, 117, 125, 0.8)'
    ];
    
    const defaultBorderColors = [
        'rgba(40, 167, 69, 1)',
        'rgba(255, 193, 7, 1)',
        'rgba(220, 53, 69, 1)',
        'rgba(13, 110, 253, 1)',
        'rgba(108, 117, 125, 1)'
    ];
    
    // Use provided colors or defaults
    const bgColors = backgroundColors || defaultBackgroundColors;
    const bdColors = borderColors || defaultBorderColors;
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderColor: bdColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                }
            }
        }
    });
}

// Create a bar chart
function createBarChart(canvasId, labels, datasets, horizontal = false) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: horizontal ? 'horizontalBar' : 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        borderDash: [2, 4]
                    }
                }
            }
        }
    });
}

// Create a line chart
function createLineChart(canvasId, labels, datasets) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        borderDash: [2, 4]
                    }
                }
            }
        }
    });
}

// Create a doughnut chart
function createDoughnutChart(canvasId, labels, data, backgroundColors, borderColors) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Default colors if not provided
    const defaultBackgroundColors = [
        'rgba(40, 167, 69, 0.8)',
        'rgba(255, 193, 7, 0.8)',
        'rgba(220, 53, 69, 0.8)',
        'rgba(13, 110, 253, 0.8)',
        'rgba(108, 117, 125, 0.8)'
    ];
    
    const defaultBorderColors = [
        'rgba(40, 167, 69, 1)',
        'rgba(255, 193, 7, 1)',
        'rgba(220, 53, 69, 1)',
        'rgba(13, 110, 253, 1)',
        'rgba(108, 117, 125, 1)'
    ];
    
    // Use provided colors or defaults
    const bgColors = backgroundColors || defaultBackgroundColors;
    const bdColors = borderColors || defaultBorderColors;
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderColor: bdColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'right',
                }
            }
        }
    });
}

// Export chart as image
function exportChartAsImage(chartId, filename) {
    const canvas = document.getElementById(chartId);
    const image = canvas.toDataURL('image/png');
    
    // Create download link
    const link = document.createElement('a');
    link.href = image;
    link.download = filename || 'chart.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Add data to an existing chart
function addChartData(chart, label, data) {
    chart.data.labels.push(label);
    chart.data.datasets.forEach((dataset) => {
        dataset.data.push(data);
    });
    chart.update();
}

// Remove data from an existing chart
function removeChartData(chart) {
    chart.data.labels.pop();
    chart.data.datasets.forEach((dataset) => {
        dataset.data.pop();
    });
    chart.update();
}

// Update chart data
function updateChartData(chart, labels, data) {
    chart.data.labels = labels;
    chart.data.datasets.forEach((dataset, i) => {
        dataset.data = data[i] || data;
    });
    chart.update();
}
