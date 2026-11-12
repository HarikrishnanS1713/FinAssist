/**
 * FinAssist - Main Frontend Application Script
 * Shared helper functions, navigation controller, global search, and notification toasts.
 */

// Helper to format currency in INR (₹)
function formatINR(amount) {
  const num = parseFloat(amount) || 0;
  return '₹' + num.toLocaleString('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2
  });
}

// Global search handler
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('global-search-input');
  const searchDropdown = document.getElementById('global-search-results');

  if (searchInput && searchDropdown) {
    let timeout = null;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(timeout);
      const q = e.target.value.trim();
      if (!q) {
        searchDropdown.classList.remove('active');
        searchDropdown.innerHTML = '';
        return;
      }
      timeout = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
          const json = await res.json();
          if (json.success) {
            renderSearchResults(json.results, searchDropdown);
          }
        } catch (err) {
          console.error("Search error:", err);
        }
      }, 250);
    });

    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
        searchDropdown.classList.remove('active');
      }
    });
  }
});

function renderSearchResults(results, dropdown) {
  dropdown.innerHTML = '';
  const customers = results.customers || [];
  const loans = results.loans || [];

  if (customers.length === 0 && loans.length === 0) {
    dropdown.innerHTML = '<div class="search-item" style="color: var(--text-muted);">No matching customers or loans found</div>';
    dropdown.classList.add('active');
    return;
  }

  let html = '';
  if (customers.length > 0) {
    html += '<div style="padding: 0.5rem 1rem; font-size: 0.75rem; font-weight: 700; color: var(--accent-emerald); text-transform: uppercase;">Customers</div>';
    customers.forEach(c => {
      html += `
        <div class="search-item" onclick="window.location.href='/customers.html?id=${c.id}'">
          <div style="font-weight: 600;">${escapeHtml(c.full_name)} <span style="font-weight: 400; font-size: 0.8rem; color: var(--text-secondary);">(ID: #${c.id})</span></div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">Phone: ${escapeHtml(c.phone)}</div>
        </div>
      `;
    });
  }

  if (loans.length > 0) {
    html += '<div style="padding: 0.5rem 1rem; font-size: 0.75rem; font-weight: 700; color: var(--accent-indigo); text-transform: uppercase;">Loans</div>';
    loans.forEach(l => {
      html += `
        <div class="search-item" onclick="window.location.href='/loans.html?id=${l.id}'">
          <div style="font-weight: 600;">Loan #${l.id} - ${escapeHtml(l.customer_name)}</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">Principal: ${formatINR(l.principal)} | Outstanding: ${formatINR(l.outstanding_balance)}</div>
        </div>
      `;
    });
  }

  dropdown.innerHTML = html;
  dropdown.classList.add('active');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function showToast(message, type = 'success') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px;';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bg = type === 'error' ? 'var(--accent-rose)' : 'var(--accent-emerald)';
  toast.style.cssText = `background: ${bg}; color: #fff; padding: 0.8rem 1.25rem; border-radius: 8px; font-weight: 600; font-size: 0.9rem; box-shadow: 0 4px 15px rgba(0,0,0,0.3); transition: all 0.3s ease; opacity: 0; transform: translateX(50px);`;
  toast.textContent = message;

  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateX(0)';
  }, 10);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(50px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
