// ======================================================
// SMART CROP CALENDAR – MAIN JAVASCRIPT
// ======================================================

// ── SIDEBAR TOGGLE ──────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const toggleBtn = document.getElementById('sidebarToggle');
  const sidebar   = document.getElementById('sidebar');
  const overlay   = document.getElementById('sidebarOverlay');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      overlay && overlay.classList.toggle('show');
    });
  }
  if (overlay) {
    overlay.addEventListener('click', function () {
      sidebar && sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }

  // Auto-dismiss alerts
  document.querySelectorAll('.alert').forEach(function (el) {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });
});

// ── CROP VARIETY LOADER ──────────────────────────────
function loadVarieties(cropName) {
  if (!cropName) return;
  fetch('/api/crop_varieties/' + encodeURIComponent(cropName))
    .then(r => r.json())
    .then(data => {
      const sel = document.getElementById('crop_id');
      const info = document.getElementById('crop-info');
      if (!sel) return;
      sel.innerHTML = '<option value="">-- Select Variety --</option>';
      data.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = v.variety + ' (' + v.season + ')';
        opt.dataset.season    = v.season;
        opt.dataset.duration  = v.duration_days;
        opt.dataset.soil      = v.soil_type;
        opt.dataset.water     = v.water_requirement;
        sel.appendChild(opt);
      });
      if (info) info.style.display = 'none';
    });
}

function updateCropInfo() {
  const sel  = document.getElementById('crop_id');
  const info = document.getElementById('crop-info');
  if (!sel || !info) return;
  const opt = sel.options[sel.selectedIndex];
  if (!opt || !opt.value) { info.style.display = 'none'; return; }
  document.getElementById('info-season')   && (document.getElementById('info-season').textContent   = opt.dataset.season   || '—');
  document.getElementById('info-duration') && (document.getElementById('info-duration').textContent = opt.dataset.duration ? opt.dataset.duration + ' days' : '—');
  document.getElementById('info-soil')     && (document.getElementById('info-soil').textContent     = opt.dataset.soil     || '—');
  document.getElementById('info-water')    && (document.getElementById('info-water').textContent    = opt.dataset.water    || '—');
  updateHarvestDate();
  info.style.display = 'block';
}

function updateHarvestDate() {
  const sowingInput  = document.getElementById('sowing_date');
  const cropSel      = document.getElementById('crop_id');
  const harvestSpan  = document.getElementById('expected-harvest');
  if (!sowingInput || !cropSel || !harvestSpan) return;
  const sowDate  = new Date(sowingInput.value);
  const opt      = cropSel.options[cropSel.selectedIndex];
  if (!sowDate || isNaN(sowDate) || !opt || !opt.dataset.duration) {
    harvestSpan.textContent = '—';
    return;
  }
  const harvestDate = new Date(sowDate);
  harvestDate.setDate(harvestDate.getDate() + parseInt(opt.dataset.duration));
  harvestSpan.textContent = harvestDate.toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });
}

// ── FULLCALENDAR INIT ────────────────────────────────
function initCalendar() {
  const calEl = document.getElementById('calendar');
  if (!calEl) return;

  const calendar = new FullCalendar.Calendar(calEl, {
    initialView: window.innerWidth < 600 ? 'listMonth' : 'dayGridMonth',
    headerToolbar: {
      left:   'prev,next today',
      center: 'title',
      right:  'dayGridMonth,listMonth'
    },
    height: 'auto',
    events: '/api/calendar_events',
    eventClick: function (info) {
      const p = info.event.extendedProps;
      showActivityModal(
        info.event.id,
        p.crop_name,
        p.activity_name,
        p.scheduled_date,
        p.description,
        p.status,
        p.completed_date,
        p.variety
      );
    },
    eventDidMount: function (info) {
      // Tooltip
      info.el.title = info.event.title + ' – ' + info.event.extendedProps.status;
    },
    dayCellDidMount: function (info) {
      const today = new Date();
      today.setHours(0,0,0,0);
      if (info.date.toDateString() === today.toDateString()) {
        info.el.style.backgroundColor = 'rgba(139,195,74,0.1)';
      }
    }
  });
  calendar.render();
}

// ── ACTIVITY MODAL ────────────────────────────────────
function showActivityModal(id, crop, activity, date, desc, status, completedDate, variety) {
  const modal = document.getElementById('activityModal');
  if (!modal) return;

  document.getElementById('modal-crop').textContent      = crop + (variety ? ' (' + variety + ')' : '');
  document.getElementById('modal-activity').textContent  = activity;
  document.getElementById('modal-date').textContent      = formatDate(date);
  document.getElementById('modal-desc').textContent      = desc || '—';
  document.getElementById('modal-status').innerHTML      = renderBadge(status);
  document.getElementById('modal-completed').textContent = completedDate ? formatDate(completedDate) : '—';

  // Complete / Delay buttons
  const completeBtn = document.getElementById('btn-complete-act');
  const delayBtn    = document.getElementById('btn-delay-act');
  if (completeBtn) {
    if (status === 'completed') {
      completeBtn.style.display = 'none';
    } else {
      completeBtn.style.display = 'inline-block';
      completeBtn.onclick = function () { markActivity(id, 'completed'); };
    }
  }
  if (delayBtn) {
    if (status === 'delayed' || status === 'completed') {
      delayBtn.style.display = 'none';
    } else {
      delayBtn.style.display = 'inline-block';
      delayBtn.onclick = function () { markActivity(id, 'delayed'); };
    }
  }

  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();
}

function markActivity(id, status) {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/mark_activity/' + id;
  const inp = document.createElement('input');
  inp.type = 'hidden'; inp.name = 'status'; inp.value = status;
  form.appendChild(inp);
  document.body.appendChild(form);
  form.submit();
}

function renderBadge(status) {
  const labels = {
    completed: 'Completed', upcoming: 'Upcoming',
    due_today: 'Due Today', overdue: 'Overdue', delayed: 'Delayed'
  };
  return `<span class="badge-status badge-${status}">${labels[status] || status}</span>`;
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });
}

// ── DASHBOARD CHARTS ──────────────────────────────────
function initDashboardCharts(chartData) {
  // Activity Status Doughnut
  const ctx1 = document.getElementById('activityChart');
  if (ctx1 && chartData) {
    new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: ['Completed', 'Upcoming', 'Due Today', 'Overdue', 'Delayed'],
        datasets: [{
          data: [
            chartData.completed,
            chartData.upcoming,
            chartData.due_today,
            chartData.overdue,
            chartData.delayed,
          ],
          backgroundColor: ['#2e7d32','#0288d1','#f9a825','#e53935','#7b1fa2'],
          borderWidth: 2, borderColor: '#fff',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 12 } },
          tooltip: { callbacks: { label: (c) => ` ${c.label}: ${c.parsed}` } }
        },
        cutout: '65%'
      }
    });
  }

  // Crop Progress Bar Chart
  const ctx2 = document.getElementById('progressChart');
  if (ctx2 && chartData && chartData.crop_labels) {
    new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: chartData.crop_labels,
        datasets: [{
          label: 'Progress (%)',
          data: chartData.crop_progress,
          backgroundColor: chartData.crop_labels.map((_, i) => [
            'rgba(46,125,50,0.8)','rgba(76,175,80,0.8)','rgba(139,195,74,0.8)',
            'rgba(249,168,37,0.8)','rgba(2,136,209,0.8)'
          ][i % 5]),
          borderRadius: 8, borderSkipped: false
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ` ${c.parsed.x}%` } } },
        scales: {
          x: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' }, grid: { color: 'rgba(0,0,0,0.05)' } },
          y: { grid: { display: false }, ticks: { font: { size: 11 } } }
        }
      }
    });
  }
}

// ── REPORT CHARTS ─────────────────────────────────────
function initReportCharts(reportData) {
  const ctx3 = document.getElementById('reportPieChart');
  if (ctx3 && reportData) {
    new Chart(ctx3, {
      type: 'pie',
      data: {
        labels: ['Completed', 'Pending', 'Delayed', 'Overdue'],
        datasets: [{
          data: [reportData.completed, reportData.pending, reportData.delayed, reportData.overdue],
          backgroundColor: ['#2e7d32','#0288d1','#7b1fa2','#e53935'],
          borderWidth: 2, borderColor: '#fff'
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { font: { size: 11 }, padding: 10 } } }
      }
    });
  }

  const ctx4 = document.getElementById('cropProgressChart');
  if (ctx4 && reportData && reportData.crop_labels) {
    new Chart(ctx4, {
      type: 'bar',
      data: {
        labels: reportData.crop_labels,
        datasets: [{
          label: 'Completion %',
          data: reportData.crop_progress,
          backgroundColor: 'rgba(46,125,50,0.8)',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } },
          x: { grid: { display: false } }
        }
      }
    });
  }
}

// ── ANIMATE NUMBERS ───────────────────────────────────
function animateNumber(el, target, duration) {
  let start = 0;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = Math.round(start);
    if (start >= target) clearInterval(timer);
  }, 16);
}

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.stat-number[data-target]').forEach(el => {
    animateNumber(el, parseInt(el.dataset.target) || 0, 800);
  });

  // Progress bars animation
  document.querySelectorAll('.progress-fill[data-width]').forEach(el => {
    setTimeout(() => { el.style.width = el.dataset.width + '%'; }, 100);
  });
});
