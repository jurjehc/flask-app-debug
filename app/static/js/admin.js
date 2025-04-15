// Global utility functions
function showLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'spinner-overlay';
    overlay.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.querySelector('.spinner-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function showAlert(message, type = 'success') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-float alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
}

// API Helpers
async function apiRequest(url, options = {}) {
    try {
        showLoading();
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'API request failed');
        }
        
        return data;
    } catch (error) {
        showAlert(error.message, 'danger');
        throw error;
    } finally {
        hideLoading();
    }
}

// Race Management
class RaceManager {
    static async startRace(raceId) {
        if (!confirm('Are you sure you want to start the race?')) return;
        
        try {
            await apiRequest(`/admin/race/${raceId}/start`, { method: 'POST' });
            showAlert('Race started successfully');
            window.location.reload();
        } catch (error) {
            console.error('Error starting race:', error);
        }
    }

    static async finishRace(raceId) {
        if (!confirm('Are you sure you want to finish the race?')) return;
        
        try {
            await apiRequest(`/admin/race/${raceId}/finish`, { method: 'POST' });
            showAlert('Race finished successfully');
            window.location.reload();
        } catch (error) {
            console.error('Error finishing race:', error);
        }
    }

    static async deleteRace(raceId) {
        if (!confirm('Are you sure you want to delete this race? This action cannot be undone.')) return;
        
        try {
            await apiRequest(`/admin/race/${raceId}`, { method: 'DELETE' });
            showAlert('Race deleted successfully');
            window.location.reload();
        } catch (error) {
            console.error('Error deleting race:', error);
        }
    }
}

// Timing Management
class TimingManager {
    constructor(raceId) {
        this.raceId = raceId;
        this.setupEventListeners();
    }

    setupEventListeners() {
        const bibInput = document.getElementById('bibNumber');
        if (bibInput) {
            bibInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.recordFinish();
                }
            });
        }
    }

    async recordFinish() {
        const bibNumber = document.getElementById('bibNumber').value;
        if (!bibNumber) return;

        try {
            await apiRequest('/admin/timing/record', {
                method: 'POST',
                body: JSON.stringify({
                    race_id: this.raceId,
                    bib_number: bibNumber,
                    type: 'finish'
                })
            });
            
            document.getElementById('bibNumber').value = '';
            showAlert('Finish time recorded');
            this.refreshResults();
        } catch (error) {
            console.error('Error recording finish:', error);
        }
    }

    async refreshResults() {
        try {
            const data = await apiRequest(`/admin/race/${this.raceId}/results`);
            this.updateResultsTable(data);
        } catch (error) {
            console.error('Error refreshing results:', error);
        }
    }

    updateResultsTable(results) {
        results.forEach(result => {
            const row = document.getElementById(`result-${result.id}`);
            if (row) {
                row.querySelector('.finish-time').textContent = result.finish_time || '-';
                row.querySelector('.duration').textContent = result.duration || '--:--:--';
                
                const statusBadge = row.querySelector('.badge');
                statusBadge.className = `badge bg-${this.getStatusClass(result.status)}`;
                statusBadge.textContent = result.status;
            }
        });
    }

    getStatusClass(status) {
        const classes = {
            'registered': 'secondary',
            'started': 'primary',
            'finished': 'success',
            'DNF': 'danger',
            'DNS': 'warning'
        };
        return classes[status] || 'secondary';
    }
}

// Email Management
class EmailManager {
    static async sendEmail(raceId, formData) {
        try {
            await apiRequest(`/admin/race/${raceId}/email`, {
                method: 'POST',
                body: JSON.stringify(Object.fromEntries(formData))
            });
            showAlert('Emails sent successfully');
            return true;
        } catch (error) {
            console.error('Error sending emails:', error);
            return false;
        }
    }

    static loadTemplate(templateName) {
        const templates = {
            'race_info': {
                subject: 'Important Race Information',
                message: `Dear {runner_name},\n\nHere are the important details for your upcoming race:\n\nRace: {race_name}\nDate: {race_date}\nStart Time: {start_time}\nBib Number: {bib_number}\n\nBest regards,\nRace Organization Team`
            },
            'results': {
                subject: 'Your Race Results',
                message: `Dear {runner_name},\n\nCongratulations on completing {race_name}!\n\nYour Results:\nFinish Time: {finish_time}\nOverall Position: {position}\n\nBest regards,\nRace Organization Team`
            }
        };

        const template = templates[templateName];
        if (template) {
            document.getElementById('subject').value = template.subject;
            document.getElementById('message').value = template.message;
        }
    }
}

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});