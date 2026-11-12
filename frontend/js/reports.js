/**
 * FinAssist - Reports & Analytics Controller
 * Renders Chart.js charts for Monthly Collections and Loan Status distribution, and displays summary KPIs.
 */

document.addEventListener('DOMContentLoaded', () => {
  loadReports();
});

let monthlyChartInstance = null;
let statusChartInstance = null;

async function loadReports() {
  try {
    const res = await fetch('/api/reports');
    const json = await res.json();

    if (!json.success) {
      showToast(json.error || "Failed to load report analytics", "error");
      return;
    }

    const r = json.reports;
    document.getElementById('report-total-collections').textContent = formatINR(r.total_collections);

    // Parse status summary
    let active = 0, overdue = 0, completed = 0;
    (r.status_summary || []).forEach(item => {
      if (item.status === 'Active') active = item.count;
      else if (item.status === 'Overdue') overdue = item.count;
      else if (item.status === 'Completed') completed = item.count;
    });

    document.getElementById('report-active-count').textContent = active;
    document.getElementById('report-overdue-count').textContent = overdue;
    document.getElementById('report-completed-count').textContent = completed;

    renderMonthlyCollectionsChart(r.monthly_collections || []);
    renderStatusDoughnutChart(active, overdue, completed);

  } catch (err) {
    console.error("Reports error:", err);
  }
}

function renderMonthlyCollectionsChart(monthlyData) {
  const ctx = document.getElementById('chart-monthly-collections');
  if (!ctx) return;

  const labels = monthlyData.map(d => d.month).reverse();
  const data = monthlyData.map(d => d.monthly_total).reverse();

  if (monthlyChartInstance) monthlyChartInstance.destroy();

  monthlyChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length > 0 ? labels : ['No Collections Yet'],
      datasets: [{
        label: 'Monthly Collections (₹)',
        data: data.length > 0 ? data : [0],
        backgroundColor: 'rgba(16, 185, 129, 0.6)',
        borderColor: '#10b981',
        borderWidth: 1.5,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#9ca3af' } }
      },
      scales: {
        x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

function renderStatusDoughnutChart(active, overdue, completed) {
  const ctx = document.getElementById('chart-loan-status');
  if (!ctx) return;

  if (statusChartInstance) statusChartInstance.destroy();

  statusChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Active Loans', 'Overdue Loans', 'Completed Loans'],
      datasets: [{
        data: [active, overdue, completed],
        backgroundColor: ['#10b981', '#ef4444', '#6366f1'],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#9ca3af', padding: 15 } }
      }
    }
  });
}
