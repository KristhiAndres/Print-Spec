document.addEventListener('DOMContentLoaded', () => {
    
    // Sidebar toggle
    const menuToggle = document.getElementById('menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('wrapper').classList.toggle('toggled');
        });
    }

    // Settings Page Logic
    const dbForm = document.getElementById('dbConfigForm');
    if (dbForm) {
        // Cargar configuración actual
        fetch('/api/v1/settings/db')
            .then(response => response.json())
            .then(data => {
                document.getElementById('db_host').value = data.db_host || '';
                document.getElementById('db_port').value = data.db_port || '3306';
                document.getElementById('db_user').value = data.db_user || '';
                document.getElementById('db_password').value = data.db_password || '';
                document.getElementById('db_name').value = data.db_name || '';
            });

        // Guardar configuración
        dbForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = document.getElementById('saveBtn');
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
            btn.disabled = true;

            const config = {
                db_host: document.getElementById('db_host').value,
                db_port: parseInt(document.getElementById('db_port').value),
                db_user: document.getElementById('db_user').value,
                db_password: document.getElementById('db_password').value,
                db_name: document.getElementById('db_name').value
            };

            fetch('/api/v1/settings/db', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                const alertHtml = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="bi bi-check-circle-fill me-2"></i>${data.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>`;
                document.getElementById('alertPlaceholder').innerHTML = alertHtml;
            })
            .catch(error => {
                const alertHtml = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>Error al guardar la configuración.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>`;
                document.getElementById('alertPlaceholder').innerHTML = alertHtml;
            })
            .finally(() => {
                btn.innerHTML = '<i class="bi bi-save me-2"></i>Guardar y Reiniciar';
                btn.disabled = false;
            });
        });
    }

    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {
        fetch('/api/v1/stats/trend')
            .then(res => res.json())
            .then(data => {
                new Chart(trendCtx, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Páginas Impresas',
                            data: data.data,
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            borderWidth: 2,
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            });
    }

    const printerCtx = document.getElementById('printerChart');
    if (printerCtx) {
        fetch('/api/v1/stats/printers')
            .then(res => res.json())
            .then(data => {
                new Chart(printerCtx, {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.data,
                            backgroundColor: ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '70%',
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });
            });
    }
});
