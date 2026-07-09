// Dark Mode Toggle
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.className = savedTheme;
    updateThemeIcon();
    
    // Theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.body.className;
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.body.className = newTheme;
            localStorage.setItem('theme', newTheme);
            updateThemeIcon();
        });
    }
    
    function updateThemeIcon() {
        const icon = document.querySelector('#themeToggle i');
        if (icon) {
            const isDark = document.body.className === 'dark';
            icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    // User Dropdown Menu
    const userBtn = document.getElementById('userBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userBtn && userDropdown) {
        userBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        document.addEventListener('click', function() {
            userDropdown.classList.remove('show');
        });
    }
    
    // Sidebar Toggle (Mobile)
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
});

// Dynamic Prescription Rows
function initPrescriptionForm() {
    const addRowBtn = document.getElementById('addPrescriptionRow');
    if (addRowBtn) {
        addRowBtn.addEventListener('click', addPrescriptionRow);
    }
    
    // Calculate total on page load
    calculatePrescriptionTotal();
}

function addPrescriptionRow() {
    const tbody = document.querySelector('#prescriptionTable tbody');
    const rowCount = tbody.querySelectorAll('tr').length;
    
    const newRow = document.createElement('tr');
    newRow.innerHTML = `
        <td>${rowCount + 1}</td>
        <td style="position: relative;">
            <input type="text" class="form-control drug-search" 
                   name="drug_search_${rowCount}" 
                   placeholder="جستجوی دارو..." 
                   autocomplete="off"
                   onkeyup="searchDrug(this)">
            <input type="hidden" class="drug-id" name="drug_id[]">
            <div class="drug-suggestions"></div>
        </td>
        <td class="drug-manufacturer">-</td>
        <td class="drug-form">-</td>
        <td class="drug-dosage">-</td>
        <td>
            <input type="number" class="form-control drug-quantity" 
                   name="quantity[]" min="1" value="1" 
                   onchange="calculatePrescriptionTotal()">
        </td>
        <td>
            <input type="text" class="form-control drug-instructions" 
                   name="instructions[]" 
                   placeholder="دستور مصرف">
        </td>
        <td class="drug-price">0</td>
        <td class="drug-total">0</td>
        <td>
            <button type="button" class="btn btn-danger btn-sm" onclick="removePrescriptionRow(this)">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;
    tbody.appendChild(newRow);
}

function removePrescriptionRow(btn) {
    const row = btn.closest('tr');
    row.remove();
    
    // Renumber rows
    const rows = document.querySelectorAll('#prescriptionTable tbody tr');
    rows.forEach((row, index) => {
        row.querySelector('td:first-child').textContent = index + 1;
    });
    
    calculatePrescriptionTotal();
}

// Drug Search with Autocomplete
let searchTimeout;
function searchDrug(input) {
    clearTimeout(searchTimeout);
    const query = input.value.trim();
    
    if (query.length < 2) {
        hideSuggestions(input);
        return;
    }
    
    searchTimeout = setTimeout(() => {
        fetch(`/api/drugs/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(drugs => {
                showDrugSuggestions(input, drugs);
            })
            .catch(error => {
                console.error('Error searching drugs:', error);
            });
    }, 300);
}

function showDrugSuggestions(input, drugs) {
    const suggestionsDiv = input.parentElement.querySelector('.drug-suggestions');
    
    if (drugs.length === 0) {
        hideSuggestions(input);
        return;
    }
    
    // Clear previous suggestions
    suggestionsDiv.innerHTML = '';
    
    // Create suggestions using data attributes and DOM manipulation (XSS-safe)
    drugs.forEach(drug => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.setAttribute('data-drug-id', drug.id);
        div.setAttribute('data-drug-name', drug.name);
        div.setAttribute('data-drug-manufacturer', drug.manufacturer);
        div.setAttribute('data-drug-form', drug.form);
        div.setAttribute('data-drug-dosage', drug.dosage);
        div.setAttribute('data-drug-price', drug.price);
        div.setAttribute('data-drug-stock', drug.stock || 0);
        div.setAttribute('data-drug-instructions', drug.default_instructions);
        
        // Safely set text content (prevents XSS)
        const strong = document.createElement('strong');
        strong.textContent = drug.name;
        div.appendChild(strong);
        
        // Add remaining text safely
        const text1 = document.createTextNode(' - ');
        const manuf = document.createTextNode(drug.manufacturer);
        const text2 = document.createTextNode(' - ');
        const formDosage = document.createTextNode(drug.form + ' ' + drug.dosage);
        const text3 = document.createTextNode(' - موجودی: ' + (drug.stock || 0));
        
        div.appendChild(text1);
        div.appendChild(manuf);
        div.appendChild(text2);
        div.appendChild(formDosage);
        div.appendChild(text3);
        
        div.onclick = function() { selectDrugSafe(this); };
        
        suggestionsDiv.appendChild(div);
    });
    
    suggestionsDiv.style.display = 'block';
}

function selectDrugSafe(element) {
    // Extract drug data from data attributes (safe from XSS)
    const drugData = {
        id: element.getAttribute('data-drug-id'),
        name: element.getAttribute('data-drug-name'),
        manufacturer: element.getAttribute('data-drug-manufacturer'),
        form: element.getAttribute('data-drug-form'),
        dosage: element.getAttribute('data-drug-dosage'),
        price: element.getAttribute('data-drug-price'),
        default_instructions: element.getAttribute('data-drug-instructions')
    };
    
    const row = element.closest('tr');
    const drugNameInput = row.querySelector('.drug-search');
    const drugIdInput = row.querySelector('.drug-id');
    const instructionsInput = row.querySelector('.drug-instructions');
    const priceCell = row.querySelector('.drug-price');
    const manufacturerCell = row.querySelector('.drug-manufacturer');
    const formCell = row.querySelector('.drug-form');
    const dosageCell = row.querySelector('.drug-dosage');
    
    // Set values safely using textContent/value properties
    drugNameInput.value = drugData.name;
    drugIdInput.value = drugData.id;
    instructionsInput.value = drugData.default_instructions;
    priceCell.textContent = drugData.price;
    if (manufacturerCell) manufacturerCell.textContent = drugData.manufacturer;
    if (formCell) formCell.textContent = drugData.form;
    if (dosageCell) dosageCell.textContent = drugData.dosage;
    
    hideSuggestions(drugNameInput);
    calculatePrescriptionTotal();
}

function hideSuggestions(input) {
    const suggestionsDiv = input.parentElement.querySelector('.drug-suggestions');
    if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
        suggestionsDiv.innerHTML = '';
    }
}

function calculatePrescriptionTotal() {
    const rows = document.querySelectorAll('#prescriptionTable tbody tr');
    let total = 0;
    
    rows.forEach(row => {
        const quantity = parseInt(row.querySelector('.drug-quantity')?.value) || 0;
        const price = parseFloat(row.querySelector('.drug-price')?.textContent) || 0;
        const rowTotal = quantity * price;
        
        const totalCell = row.querySelector('.drug-total');
        if (totalCell) {
            totalCell.textContent = rowTotal.toFixed(2);
        }
        
        total += rowTotal;
    });
    
    const totalElement = document.getElementById('prescriptionTotalAmount');
    if (totalElement) {
        totalElement.textContent = total.toFixed(2);
    }
    
    const hiddenTotal = document.querySelector('input[name="total_amount"]');
    if (hiddenTotal) {
        hiddenTotal.value = total.toFixed(2);
    }
}

function validatePrescriptionItems(form) {
    if (!form || !document.getElementById('prescriptionTable')) return true;
    const rows = form.querySelectorAll('#prescriptionTable tbody tr');
    let hasDrug = false;

    rows.forEach(row => {
        const drugId = row.querySelector('.drug-id')?.value;
        const quantity = parseInt(row.querySelector('.drug-quantity')?.value, 10) || 0;
        if (drugId && quantity > 0) {
            hasDrug = true;
        }
    });

    if (!hasDrug) {
        alert('حداقل یک داروی معتبر انتخاب کنید.');
        return false;
    }
    return true;
}

// Close suggestions when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.classList.contains('drug-search')) {
        document.querySelectorAll('.drug-suggestions').forEach(div => {
            div.style.display = 'none';
        });
    }
});

// Initialize prescription form if exists
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('prescriptionTable')) {
        initPrescriptionForm();
        const prescriptionForm = document.getElementById('prescriptionForm');
        if (prescriptionForm) {
            prescriptionForm.addEventListener('submit', function(event) {
                if (!validatePrescriptionItems(prescriptionForm)) {
                    event.preventDefault();
                }
            });
        }
    }
});

// Print Prescription
function printPrescription(prescriptionId) {
    window.open(`/print/prescription/${prescriptionId}`, '_blank');
}

// Confirmation dialogs
function confirmAction(message) {
    return confirm(message);
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = 'var(--danger)';
            isValid = false;
        } else {
            field.style.borderColor = 'var(--input-border)';
        }
    });
    
    if (!isValid) {
        alert('لطفا تمام فیلدهای الزامی را پر کنید');
    }
    
    return isValid;
}
