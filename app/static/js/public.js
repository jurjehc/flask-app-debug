// Utility Functions
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

// Race Results Filtering and Sorting
class ResultsManager {
    constructor(tableId) {
        this.table = document.getElementById(tableId);
        this.setupFilters();
    }

    setupFilters() {
        const filters = document.querySelectorAll('[data-filter]');
        filters.forEach(filter => {
            filter.addEventListener('change', () => this.filterResults());
        });

        const search = document.getElementById('searchInput');
        if (search) {
            search.addEventListener('input', () => this.filterResults());
        }
    }

    filterResults() {
        const search = document.getElementById('searchInput')?.value.toLowerCase() || '';
        const gender = document.getElementById('genderFilter')?.value || '';
        const ageGroup = document.getElementById('ageGroupFilter')?.value || '';
        const status = document.getElementById('statusFilter')?.value || '';

        const rows = this.table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const matchesSearch = !search || 
                row.textContent.toLowerCase().includes(search);
            const matchesGender = !gender || 
                row.getAttribute('data-gender') === gender;
            const matchesAgeGroup = !ageGroup || 
                row.getAttribute('data-age-group') === ageGroup;
            const matchesStatus = !status || 
                row.getAttribute('data-status') === status;

            row.style.display = 
                matchesSearch && matchesGender && matchesAgeGroup && matchesStatus
                    ? ''
                    : 'none';
        });
    }

    sortTable(columnIndex) {
        const tbody = this.table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isNumeric = [0, 1, 6].includes(columnIndex);

        rows.sort((a, b) => {
            let aValue = a.cells[columnIndex].textContent;
            let bValue = b.cells[columnIndex].textContent;

            if (isNumeric) {
                aValue = aValue === '-' ? Infinity : parseFloat(aValue);
                bValue = bValue === '-' ? Infinity : parseFloat(bValue);
                return aValue - bValue;
            }

            return aValue.localeCompare(bValue);
        });

        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));
    }
}

// Registration Form Handling
class RegistrationForm {
    constructor(formId) {
        this.form = document.getElementById(formId);
        if (this.form) {
            this.setupValidation();
            this.setupEventHandlers();
        }
    }

    setupValidation() {
        this.form.addEventListener('submit', (e) => {
            if (!this.form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.form.classList.add('was-validated');
        });
    }

    setupEventHandlers() {
        // Event selection
        const eventSelects = this.form.querySelectorAll('[name="event"]');
        eventSelects.forEach(select => {
            select.addEventListener('change', () => this.updatePrice());
        });

        // Terms checkbox
        const termsCheckbox = this.form.querySelector('#terms');
        if (termsCheckbox) {
            termsCheckbox.addEventListener('change', () => {
                const submitButton = this.form.querySelector('button[type="submit"]');
                submitButton.disabled = !termsCheckbox.checked;
            });
        }
    }

    updatePrice() {
        const selectedEvent = this.form.querySelector('[name="event"]:checked');
        if (!selectedEvent) return;

        const priceElement = document.getElementById('eventPrice');
        if (priceElement) {
            const price = selectedEvent.getAttribute('data-price');
            priceElement.textContent = price ? `${price}€` : 'Free';
        }
    }
}

// Search Functionality
class SearchManager {
    constructor() {
        this.setupSearchForm();
    }

    setupSearchForm() {
        const form = document.querySelector('.search-form');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = form.querySelector('input[name="q"]').value;
            this.performSearch(query);
        });
    }

    async performSearch(query) {
        showLoading();
        
        try {
            const response = await fetch(`/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            this.displayResults(data);
        } catch (error) {
            showAlert('Error performing search', 'danger');
            console.error('Search error:', error);
        } finally {
            hideLoading();
        }
    }

    displayResults(results) {
        const container = document.getElementById('searchResults');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <p class="text-muted">No results found</p>
                </div>
            `;
            return;
        }

        container.innerHTML = results.map(result => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${result.name}</h5>
                    <p class="card-text">${result.description}</p>
                    <a href="/race/${result.id}" class="btn btn-primary">View Details</a>
                </div>
            </div>
        `).join('');
    }
}

// Initialize components on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize results manager if on results page
    const resultsTable = document.querySelector('.results-table');
    if (resultsTable) {
        new ResultsManager(resultsTable.id);
    }

    // Initialize registration form if on registration page
    const registrationForm = document.getElementById('registrationForm');
    if (registrationForm) {
        new RegistrationForm('registrationForm');
    }

    // Initialize search functionality
    new SearchManager();
});