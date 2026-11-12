/**
 * FinAssist - Customers Management Controller
 * Handles loading customer tables, adding, editing, deleting customers, and viewing detailed profile/loans.
 */

document.addEventListener('DOMContentLoaded', () => {
  loadCustomers();

  // Search Filter
  const filterInput = document.getElementById('customer-table-filter');
  if (filterInput) {
    filterInput.addEventListener('input', (e) => loadCustomers(e.target.value.trim()));
  }

  // Modal Handlers
  const addBtn = document.getElementById('btn-add-customer');
  const modal = document.getElementById('modal-customer');
  const closeBtn = document.getElementById('btn-close-customer-modal');
  const cancelBtn = document.getElementById('btn-cancel-customer-modal');
  const form = document.getElementById('form-customer');

  if (addBtn && modal) {
    addBtn.addEventListener('click', () => {
      openCustomerModal();
    });
  }

  if (closeBtn && modal) closeBtn.addEventListener('click', () => closeModal(modal));
  if (cancelBtn && modal) cancelBtn.addEventListener('click', () => closeModal(modal));

  const closeDetailsBtn = document.getElementById('btn-close-details-modal');
  const detailsModal = document.getElementById('modal-customer-details');
  if (closeDetailsBtn && detailsModal) closeDetailsBtn.addEventListener('click', () => closeModal(detailsModal));

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      await saveCustomer();
    });
  }

  // Check URL parameters for ?id= query
  const urlParams = new URLSearchParams(window.location.search);
  const targetId = urlParams.get('id');
  if (targetId) {
    viewCustomerDetails(targetId);
  }
});

async function loadCustomers(query = '') {
  try {
    const url = query ? `/api/customers?q=${encodeURIComponent(query)}` : '/api/customers';
    const res = await fetch(url);
    const json = await res.json();

    if (!json.success) {
      showToast(json.error || "Failed to load customers", "error");
      return;
    }

    renderCustomersTable(json.customers);
  } catch (err) {
    console.error("Error loading customers:", err);
  }
}

function renderCustomersTable(customers) {
  const tbody = document.getElementById('customers-table-body');
  if (!tbody) return;

  if (!customers || customers.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--text-muted);">No customers found. Click "Add New Customer" to create one.</td></tr>';
    return;
  }

  tbody.innerHTML = customers.map(c => `
    <tr>
      <td><strong>#${c.id}</strong></td>
      <td><strong style="color:var(--text-primary); cursor:pointer;" onclick="viewCustomerDetails(${c.id})">${escapeHtml(c.full_name)}</strong></td>
      <td>${escapeHtml(c.phone)}</td>
      <td>${escapeHtml(c.address || '—')}</td>
      <td><span class="badge badge-active">${c.total_loans} Loans</span></td>
      <td style="font-weight:700; color: ${c.current_outstanding > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)'};">${formatINR(c.current_outstanding)}</td>
      <td style="color:var(--text-muted);">${c.date_added}</td>
      <td>
        <div style="display:flex; gap:0.4rem;">
          <button class="btn btn-secondary btn-sm" onclick="viewCustomerDetails(${c.id})">View</button>
          <button class="btn btn-secondary btn-sm" onclick="editCustomer(${c.id}, '${escapeHtml(c.full_name)}', '${escapeHtml(c.phone)}', '${escapeHtml(c.address || '')}', '${escapeHtml(c.notes || '')}')">Edit</button>
          <button class="btn btn-danger btn-sm" onclick="confirmDeleteCustomer(${c.id}, '${escapeHtml(c.full_name)}')">Delete</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function openCustomerModal(id = '', name = '', phone = '', address = '', notes = '') {
  document.getElementById('customer-id').value = id;
  document.getElementById('customer-name').value = name;
  document.getElementById('customer-phone').value = phone;
  document.getElementById('customer-address').value = address;
  document.getElementById('customer-notes').value = notes;
  document.getElementById('modal-customer-title').textContent = id ? 'Edit Customer' : 'Add New Customer';

  const modal = document.getElementById('modal-customer');
  if (modal) modal.classList.add('active');
}

function editCustomer(id, name, phone, address, notes) {
  openCustomerModal(id, name, phone, address, notes);
}

function closeModal(modal) {
  if (modal) modal.classList.remove('active');
}

async function saveCustomer() {
  const id = document.getElementById('customer-id').value;
  const full_name = document.getElementById('customer-name').value.trim();
  const phone = document.getElementById('customer-phone').value.trim();
  const address = document.getElementById('customer-address').value.trim();
  const notes = document.getElementById('customer-notes').value.trim();

  if (!full_name || !phone) {
    showToast("Name and Phone are required", "error");
    return;
  }

  const payload = { full_name, phone, address, notes };
  const url = id ? `/api/customers/${id}` : '/api/customers';
  const method = id ? 'PUT' : 'POST';

  try {
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (json.success) {
      showToast(id ? "Customer updated successfully!" : "New customer added successfully!");
      closeModal(document.getElementById('modal-customer'));
      loadCustomers();
    } else {
      showToast(json.error || "Failed to save customer", "error");
    }
  } catch (err) {
    console.error("Error saving customer:", err);
    showToast("Server error saving customer", "error");
  }
}

async function confirmDeleteCustomer(id, name) {
  if (confirm(`Are you sure you want to delete customer "${name}" (ID #${id})? All associated loans and payments will be deleted.`)) {
    try {
      const res = await fetch(`/api/customers/${id}`, { method: 'DELETE' });
      const json = await res.json();
      if (json.success) {
        showToast("Customer deleted successfully.");
        loadCustomers();
      } else {
        showToast(json.error || "Delete failed", "error");
      }
    } catch (err) {
      console.error("Delete error:", err);
      showToast("Error deleting customer", "error");
    }
  }
}

async function viewCustomerDetails(id) {
  try {
    const res = await fetch(`/api/customers/${id}`);
    const json = await res.json();
    if (!json.success || !json.customer) {
      showToast(json.error || "Customer profile not found", "error");
      return;
    }

    const c = json.customer;
    const body = document.getElementById('customer-details-body');
    if (!body) return;

    let loansHtml = '';
    if (!c.loans || c.loans.length === 0) {
      loansHtml = '<p style="color:var(--text-muted);">No loans recorded for this customer.</p>';
    } else {
      loansHtml = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Loan #</th>
              <th>Principal</th>
              <th>Interest Rate</th>
              <th>Total Repayment</th>
              <th>Paid</th>
              <th>Outstanding</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${c.loans.map(l => `
              <tr>
                <td><strong>#${l.id}</strong></td>
                <td>${formatINR(l.principal)}</td>
                <td>${l.interest_rate}% (${l.interest_type})</td>
                <td>${formatINR(l.total_repayment)}</td>
                <td style="color:var(--accent-emerald);">${formatINR(l.amount_paid)}</td>
                <td style="font-weight:700; color:var(--accent-rose);">${formatINR(l.outstanding_balance)}</td>
                <td><span class="badge badge-${l.status.toLowerCase()}">${l.status}</span></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }

    body.innerHTML = `
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; background: var(--bg-card); padding: 1.25rem; border-radius: var(--radius-md); border: 1px solid var(--border-color);">
        <div>
          <div style="font-size: 0.8rem; color:var(--text-muted); text-transform:uppercase;">Customer Name</div>
          <div style="font-size: 1.2rem; font-weight: 700;">${escapeHtml(c.full_name)} <span style="font-size: 0.85rem; color:var(--text-secondary);">(ID: #${c.id})</span></div>
          <div style="margin-top: 0.5rem; font-size: 0.9rem;"><strong>Phone:</strong> ${escapeHtml(c.phone)}</div>
          <div style="font-size: 0.9rem;"><strong>Address:</strong> ${escapeHtml(c.address || 'N/A')}</div>
        </div>
        <div>
          <div style="font-size: 0.8rem; color:var(--text-muted); text-transform:uppercase;">Financial Overview</div>
          <div style="margin-top: 0.4rem; font-size: 0.9rem;"><strong>Total Paid:</strong> <span style="color:var(--accent-emerald); font-weight:700;">${formatINR(c.total_paid)}</span></div>
          <div style="font-size: 0.9rem;"><strong>Total Outstanding:</strong> <span style="color:var(--accent-rose); font-weight:700;">${formatINR(c.total_outstanding)}</span></div>
          <div style="font-size: 0.9rem;"><strong>Date Added:</strong> ${c.date_added}</div>
        </div>
      </div>

      <h3 style="font-size: 1.05rem; font-weight: 700; margin-bottom: 0.75rem;">Loans Portfolio</h3>
      <div class="table-responsive">
        ${loansHtml}
      </div>
    `;

    const detailsModal = document.getElementById('modal-customer-details');
    if (detailsModal) detailsModal.classList.add('active');

  } catch (err) {
    console.error("Error viewing customer details:", err);
  }
}
