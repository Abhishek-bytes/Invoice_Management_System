// Invoice Management System JavaScript

// Global variables
let itemCount = 1;
let currentInvoiceData = {};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Set up event listeners
    setupEventListeners();
    
    // Calculate initial totals
    calculateTotals();
    
    // Load any saved form data
    if (typeof loadFormData === 'function') {
        loadFormData();
    }
}

function setupEventListeners() {
    // Tax rate change listener
    const taxRateInput = document.getElementById('tax_rate');
    if (taxRateInput) {
        taxRateInput.addEventListener('input', calculateTotals);
    }

    // Form auto-save functionality
    const form = document.getElementById('invoiceForm');
    if (form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', debounce(saveFormData, 1000));
        });
    }
}

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add new item row to the invoice
function addItem() {
    const tableBody = document.getElementById('itemsTableBody');
    const productOptions = document.querySelector('.item-product').innerHTML;
    const newRow = document.createElement('tr');
    newRow.className = 'item-row';
    newRow.innerHTML = `
        <td>
            <select name="item_product_id[]" class="form-control item-product" onchange="selectProduct(this)">
                ${productOptions}
            </select>
            <input type="text" name="item_description[]" class="form-control item-description mt-2" placeholder="Or enter custom description" required>
        </td>
        <td><input type="text" name="item_hsn[]" class="form-control item-hsn" placeholder="1234"></td>
        <td><input type="number" name="item_quantity[]" class="form-control item-quantity" step="0.01" min="0" onchange="calculateRowTotal(this)" required></td>
        <td><input type="text" name="item_unit[]" class="form-control item-unit" value="pcs"></td>
        <td><input type="number" name="item_rate[]" class="form-control item-rate" step="0.01" min="0" onchange="calculateRowTotal(this)" required></td>
        <td class="item-total">₹0.00</td>
        <td><button type="button" class="btn btn-danger btn-sm" onclick="removeItem(this)"><i class="fas fa-trash"></i></button></td>
    `;
    tableBody.appendChild(newRow);
    itemCount++;
    
    // Add event listeners to new inputs
    const newInputs = newRow.querySelectorAll('input');
    newInputs.forEach(input => {
        input.addEventListener('input', debounce(saveFormData, 1000));
    });
}

// Remove item row from the invoice
function removeItem(button) {
    const row = button.closest('tr');
    row.remove();
    calculateTotals();
    saveFormData();
}

// Calculate total for a specific row
function calculateRowTotal(input) {
    const row = input.closest('tr');
    const quantity = parseFloat(row.querySelector('.item-quantity').value) || 0;
    const rate = parseFloat(row.querySelector('.item-rate').value) || 0;
    const total = quantity * rate;
    
    row.querySelector('.item-total').textContent = formatCurrencyINR(total);
    calculateTotals();
}

// Calculate invoice totals with GST
function calculateTotals() {
    const rows = document.querySelectorAll('.item-row');
    let subtotal = 0;
    
    rows.forEach(row => {
        const quantity = parseFloat(row.querySelector('.item-quantity').value) || 0;
        const rate = parseFloat(row.querySelector('.item-rate').value) || 0;
        subtotal += quantity * rate;
    });
    
    // Get GST rates
    const cgstRate = parseFloat(document.getElementById('cgst_rate')?.value) || 0;
    const sgstRate = parseFloat(document.getElementById('sgst_rate')?.value) || 0;
    const igstRate = parseFloat(document.getElementById('igst_rate')?.value) || 0;
    
    // Calculate GST amounts
    let cgstAmount = 0, sgstAmount = 0, igstAmount = 0;
    
    if (document.getElementById('gst_type')?.value === 'inter') {
        // Inter-state: Use IGST
        igstAmount = subtotal * (igstRate / 100);
    } else {
        // Intra-state: Use CGST + SGST
        cgstAmount = subtotal * (cgstRate / 100);
        sgstAmount = subtotal * (sgstRate / 100);
    }
    
    const totalGST = cgstAmount + sgstAmount + igstAmount;
    const total = subtotal + totalGST;
    
    // Update display
    const subtotalElement = document.getElementById('subtotal');
    const cgstElement = document.getElementById('cgst_amount');
    const sgstElement = document.getElementById('sgst_amount');
    const igstElement = document.getElementById('igst_amount');
    const totalElement = document.getElementById('total');
    
    // Update rate displays
    const cgstRateDisplay = document.getElementById('cgst_rate_display');
    const sgstRateDisplay = document.getElementById('sgst_rate_display');
    const igstRateDisplay = document.getElementById('igst_rate_display');
    
    if (subtotalElement) subtotalElement.textContent = formatCurrencyINR(subtotal);
    if (cgstElement) cgstElement.textContent = formatCurrencyINR(cgstAmount);
    if (sgstElement) sgstElement.textContent = formatCurrencyINR(sgstAmount);
    if (igstElement) igstElement.textContent = formatCurrencyINR(igstAmount);
    if (totalElement) totalElement.textContent = formatCurrencyINR(total);
    
    if (cgstRateDisplay) cgstRateDisplay.textContent = cgstRate;
    if (sgstRateDisplay) sgstRateDisplay.textContent = sgstRate;
    if (igstRateDisplay) igstRateDisplay.textContent = igstRate;
}

// Format number as INR currency
function formatCurrencyINR(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

// Toggle GST fields based on type
function toggleGSTFields() {
    const gstType = document.getElementById('gst_type').value;
    const cgstField = document.getElementById('cgst_field');
    const sgstField = document.getElementById('sgst_field');
    const igstField = document.getElementById('igst_field');
    const cgstRow = document.getElementById('cgst_row');
    const sgstRow = document.getElementById('sgst_row');
    const igstRow = document.getElementById('igst_row');
    
    if (gstType === 'inter') {
        // Inter-state: Show IGST, hide CGST/SGST
        cgstField.style.display = 'none';
        sgstField.style.display = 'none';
        igstField.style.display = 'block';
        cgstRow.style.display = 'none';
        sgstRow.style.display = 'none';
        igstRow.style.display = 'flex';
        
        // Set IGST to combined rate
        const cgstRate = parseFloat(document.getElementById('cgst_rate').value) || 0;
        const sgstRate = parseFloat(document.getElementById('sgst_rate').value) || 0;
        document.getElementById('igst_rate').value = cgstRate + sgstRate;
    } else {
        // Intra-state: Show CGST/SGST, hide IGST
        cgstField.style.display = 'block';
        sgstField.style.display = 'block';
        igstField.style.display = 'none';
        cgstRow.style.display = 'flex';
        sgstRow.style.display = 'flex';
        igstRow.style.display = 'none';
        
        // Reset IGST
        document.getElementById('igst_rate').value = 0;
    }
    
    calculateTotals();
}

// Select product and fill details
function selectProduct(selectElement) {
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const row = selectElement.closest('.item-row');
    
    if (selectedOption.value) {
        // Fill product details
        row.querySelector('.item-description').value = selectedOption.dataset.name;
        row.querySelector('.item-rate').value = selectedOption.dataset.rate;
        row.querySelector('.item-unit').value = selectedOption.dataset.unit;
        row.querySelector('.item-hsn').value = selectedOption.dataset.hsn || '';
        
        // Calculate total if quantity is set
        const quantityInput = row.querySelector('.item-quantity');
        if (quantityInput.value) {
            calculateRowTotal(quantityInput);
        }
    }
}

// Save form data to localStorage
function saveFormData() {
    try {
        const form = document.getElementById('invoiceForm');
        if (!form) return;
        
        const formData = new FormData(form);
        const data = {};
        
        // Save regular form fields
        for (let [key, value] of formData.entries()) {
            if (!key.includes('[]')) {
                data[key] = value;
            }
        }
        
        // Save array fields (items)
        const descriptions = formData.getAll('item_description[]');
        const quantities = formData.getAll('item_quantity[]');
        const rates = formData.getAll('item_rate[]');
        
        data.items = [];
        for (let i = 0; i < descriptions.length; i++) {
            if (descriptions[i].trim()) {
                data.items.push({
                    description: descriptions[i],
                    quantity: quantities[i],
                    rate: rates[i]
                });
            }
        }
        
        localStorage.setItem('invoiceFormData', JSON.stringify(data));
    } catch (error) {
        console.error('Error saving form data:', error);
    }
}

// Load form data from localStorage
function loadFormData() {
    try {
        const savedData = localStorage.getItem('invoiceFormData');
        if (!savedData) return;
        
        const data = JSON.parse(savedData);
        
        // Load regular form fields
        for (let [key, value] of Object.entries(data)) {
            if (key !== 'items') {
                const input = document.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = value;
                }
            }
        }
        
        // Load items
        if (data.items && data.items.length > 0) {
            // Clear existing items except the first one
            const tableBody = document.getElementById('itemsTableBody');
            const firstRow = tableBody.querySelector('.item-row');
            tableBody.innerHTML = '';
            
            // Add items
            data.items.forEach((item, index) => {
                if (index === 0 && firstRow) {
                    // Use existing first row
                    firstRow.querySelector('.item-description').value = item.description;
                    firstRow.querySelector('.item-quantity').value = item.quantity;
                    firstRow.querySelector('.item-rate').value = item.rate;
                    calculateRowTotal(firstRow.querySelector('.item-quantity'));
                    tableBody.appendChild(firstRow);
                } else {
                    // Add new row
                    addItem();
                    const newRow = tableBody.lastElementChild;
                    newRow.querySelector('.item-description').value = item.description;
                    newRow.querySelector('.item-quantity').value = item.quantity;
                    newRow.querySelector('.item-rate').value = item.rate;
                    calculateRowTotal(newRow.querySelector('.item-quantity'));
                }
            });
        }
        
        calculateTotals();
    } catch (error) {
        console.error('Error loading form data:', error);
    }
}

// Clear saved form data
function clearFormData() {
    localStorage.removeItem('invoiceFormData');
}

// Show invoice preview
function showPreview() {
    generatePreviewContent();
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
}

// Generate preview content
function generatePreviewContent() {
    const previewContainer = document.getElementById('invoicePreview');
    if (!previewContainer) return;
    
    // Get form data
    const formData = getFormData();
    
    const previewHTML = `
        <div class="invoice-preview-header">
            <div>
                <h1 class="invoice-title">INVOICE</h1>
            </div>
            <div class="invoice-preview-details">
                <p><strong>Invoice #:</strong> ${formData.invoiceNumber || 'INV-PREVIEW'}</p>
                <p><strong>Date:</strong> ${formData.issueDate || new Date().toLocaleDateString()}</p>
                <p><strong>Due Date:</strong> ${formData.dueDate || ''}</p>
            </div>
        </div>
        
        <div class="invoice-parties">
            <div class="party-info">
                <h3>From:</h3>
                <div>
                    <strong>${formData.companyName || 'Your Company'}</strong><br>
                    ${formData.companyAddress || ''}<br>
                    ${formData.companyCity || ''} ${formData.companyState || ''} ${formData.companyZip || ''}<br>
                    ${formData.companyPhone || ''}<br>
                    ${formData.companyEmail || ''}
                </div>
            </div>
            <div class="party-info">
                <h3>To:</h3>
                <div>
                    <strong>${formData.clientName || 'Client Name'}</strong><br>
                    ${formData.clientAddress || ''}<br>
                    ${formData.clientCity || ''} ${formData.clientState || ''} ${formData.clientZip || ''}<br>
                    ${formData.clientPhone || ''}<br>
                    ${formData.clientEmail || ''}
                </div>
            </div>
        </div>
        
        <table class="items-table">
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Rate</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                ${formData.items.map(item => `
                    <tr>
                        <td>${item.description}</td>
                        <td>${item.quantity}</td>
                        <td>${formatCurrencyINR(parseFloat(item.rate))}</td>
                        <td>${formatCurrencyINR(parseFloat(item.quantity) * parseFloat(item.rate))}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        
        <div class="total-section">
            <div class="total-row">
                <span>Subtotal:</span>
                <span>${formatCurrencyINR(formData.subtotal)}</span>
            </div>
            ${formData.cgstAmount > 0 ? `<div class="total-row"><span>CGST (${formData.cgstRate}%):</span><span>${formatCurrencyINR(formData.cgstAmount)}</span></div>` : ''}
            ${formData.sgstAmount > 0 ? `<div class="total-row"><span>SGST (${formData.sgstRate}%):</span><span>${formatCurrencyINR(formData.sgstAmount)}</span></div>` : ''}
            ${formData.igstAmount > 0 ? `<div class="total-row"><span>IGST (${formData.igstRate}%):</span><span>${formatCurrencyINR(formData.igstAmount)}</span></div>` : ''}
            <div class="total-row final">
                <span>Total:</span>
                <span>${formatCurrencyINR(formData.total)}</span>
            </div>
        </div>
        
        ${formData.notes ? `
            <div class="mt-4">
                <h4>Notes:</h4>
                <p>${formData.notes}</p>
            </div>
        ` : ''}
        
        ${formData.terms ? `
            <div class="mt-4">
                <h4>Terms & Conditions:</h4>
                <p>${formData.terms}</p>
            </div>
        ` : ''}
    `;
    
    previewContainer.innerHTML = previewHTML;
}

// Get form data as object
function getFormData() {
    const form = document.getElementById('invoiceForm');
    if (!form) return {};
    
    const formData = new FormData(form);
    const data = {};
    
    // Basic fields
    for (let [key, value] of formData.entries()) {
        if (!key.includes('[]')) {
            data[key] = value;
        }
    }
    
    // Items
    const descriptions = formData.getAll('item_description[]');
    const quantities = formData.getAll('item_quantity[]');
    const rates = formData.getAll('item_rate[]');
    
    data.items = [];
    let subtotal = 0;
    
    for (let i = 0; i < descriptions.length; i++) {
        if (descriptions[i].trim()) {
            const quantity = parseFloat(quantities[i]) || 0;
            const rate = parseFloat(rates[i]) || 0;
            const itemTotal = quantity * rate;
            
            data.items.push({
                description: descriptions[i],
                quantity: quantities[i],
                rate: rates[i],
                total: itemTotal
            });
            
            subtotal += itemTotal;
        }
    }
    
    // GST Calculations
    data.subtotal = subtotal;
    data.cgstRate = parseFloat(data.cgst_rate) || 0;
    data.sgstRate = parseFloat(data.sgst_rate) || 0;
    data.igstRate = parseFloat(data.igst_rate) || 0;
    
    if (data.gst_type === 'inter') {
        data.igstAmount = subtotal * (data.igstRate / 100);
        data.cgstAmount = 0;
        data.sgstAmount = 0;
    } else {
        data.cgstAmount = subtotal * (data.cgstRate / 100);
        data.sgstAmount = subtotal * (data.sgstRate / 100);
        data.igstAmount = 0;
    }
    
    data.totalGST = data.cgstAmount + data.sgstAmount + data.igstAmount;
    data.total = subtotal + data.totalGST;
    data.invoiceNumber = 'INV-PREVIEW';
    
    return data;
}

// Generate PDF
function generatePDF() {
    const previewContainer = document.getElementById('invoicePreview');
    if (!previewContainer || !previewContainer.innerHTML.trim()) {
        generatePreviewContent();
    }
    
    const element = previewContainer;
    const opt = {
        margin: 1,
        filename: `invoice-${new Date().getTime()}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(element).save();
}

// Form validation
function validateForm() {
    const form = document.getElementById('invoiceForm');
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // Check if at least one item is added
    const itemRows = document.querySelectorAll('.item-row');
    let hasItems = false;
    
    itemRows.forEach(row => {
        const description = row.querySelector('.item-description').value.trim();
        if (description) {
            hasItems = true;
        }
    });
    
    if (!hasItems) {
        alert('Please add at least one item to the invoice.');
        isValid = false;
    }
    
    return isValid;
}

// Enhanced form submission
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('invoiceForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }
            
            // Clear saved data on successful submission
            setTimeout(() => {
                clearFormData();
            }, 1000);
        });
    }
});

// Auto-calculate due date (30 days from issue date)
document.addEventListener('DOMContentLoaded', function() {
    const issueDateInput = document.getElementById('issue_date');
    const dueDateInput = document.getElementById('due_date');
    
    if (issueDateInput && dueDateInput) {
        issueDateInput.addEventListener('change', function() {
            const issueDate = new Date(this.value);
            const dueDate = new Date(issueDate.getTime() + (30 * 24 * 60 * 60 * 1000));
            dueDateInput.value = dueDate.toISOString().split('T')[0];
        });
    }
});

// Utility functions for number formatting
function parseNumber(value) {
    return parseFloat(value) || 0;
}

function formatNumber(number, decimals = 2) {
    return number.toFixed(decimals);
}

// Client autocomplete functionality (if needed)
function setupClientAutocomplete() {
    const clientNameInput = document.getElementById('client_name');
    if (!clientNameInput) return;
    
    // This could be enhanced with a proper autocomplete library
    // For now, it's a placeholder for future enhancement
}

// Export functions for global access
window.addItem = addItem;
window.removeItem = removeItem;
window.calculateRowTotal = calculateRowTotal;
window.calculateTotals = calculateTotals;
window.showPreview = showPreview;
window.generatePDF = generatePDF;
window.toggleGSTFields = toggleGSTFields;
window.selectProduct = selectProduct;
window.saveFormData = saveFormData;
window.loadFormData = loadFormData;
window.clearFormData = clearFormData;
