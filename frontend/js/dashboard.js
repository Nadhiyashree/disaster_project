/**
 * dashboard.js
 * ============
 * Main dashboard controller for Phase 2.
 *
 * Manages Priority Queue, Master Reports Table, Map markers,
 * KPI statistics, filters, role views, and detail navigation.
 */

(function () {
  'use strict';

  const DEFAULT_PAGE_SIZE = 25;

  const state = {
    currentOffset: 0,
    currentLimit: DEFAULT_PAGE_SIZE,
    totalReports: 0,
    filters: {
      search: '',
      incident_type: '',
      zone: '',
      priority: '',
      confidence: '',
      freshness: '',
      status: '',
      conflict: '',
      correlation: '',
    },
    currentRole: 'Responder',
  };

  const DOM = {};

  function cacheDom() {
    DOM.kpiTotal          = document.getElementById('kpi-total');
    DOM.kpiVerified       = document.getElementById('kpi-verified');
    DOM.kpiCritical       = document.getElementById('kpi-critical');
    DOM.kpiHighPriority   = document.getElementById('kpi-high-priority');
    DOM.kpiStale          = document.getElementById('kpi-stale');
    DOM.kpiAvgConfidence  = document.getElementById('kpi-avg-confidence');

    DOM.prioQueueTableBody = document.getElementById('priority-queue-table-body');
    DOM.tableBody         = document.getElementById('report-table-body');
    DOM.paginationInfo    = document.getElementById('pagination-info');
    DOM.paginationPages   = document.getElementById('pagination-pages');
    DOM.prevBtn           = document.getElementById('btn-prev');
    DOM.nextBtn           = document.getElementById('btn-next');
    DOM.refreshBtn        = document.getElementById('btn-refresh');

    DOM.roleSelect        = document.getElementById('role-select');
    DOM.clearFiltersBtn   = document.getElementById('btn-clear-filters');

    DOM.searchInput       = document.getElementById('filter-search');
    DOM.incidentFilter    = document.getElementById('filter-incident');
    DOM.zoneFilter        = document.getElementById('filter-zone');
    DOM.priorityFilter    = document.getElementById('filter-priority');
    DOM.confidenceFilter  = document.getElementById('filter-confidence');
    DOM.freshnessFilter   = document.getElementById('filter-freshness');
    DOM.statusFilter      = document.getElementById('filter-status');
    DOM.conflictFilter    = document.getElementById('filter-conflict');
    DOM.correlationFilter = document.getElementById('filter-correlation');

    DOM.activityList      = document.getElementById('activity-list');
    DOM.lastUpdatedTime   = document.getElementById('last-updated-time');
  }

  // ── KPI Cards ──────────────────────────────────────────────────────────────

  function updateKpis(stats) {
    const set = (el, val) => {
      if (!el) return;
      el.textContent = typeof val === 'number' ? val.toLocaleString() : val;
      el.classList.remove('loading-val');
    };
    set(DOM.kpiTotal,         stats.total_reports);
    set(DOM.kpiVerified,      stats.verified_reports);
    set(DOM.kpiCritical,      stats.critical_reports);
    set(DOM.kpiHighPriority,  stats.high_priority_reports);
    set(DOM.kpiStale,         stats.stale_reports);
    set(DOM.kpiAvgConfidence, stats.average_confidence ? `${stats.average_confidence.toFixed(1)}/100` : '—');
  }

  async function loadStats() {
    try {
      const stats = await window.API.getDashboardStats();
      updateKpis(stats);
      renderActivityFeed(stats.recent_activity || []);
      if (DOM.lastUpdatedTime) {
        DOM.lastUpdatedTime.textContent = new Date().toLocaleTimeString();
      }
    } catch (err) {
      console.error('[dashboard] Failed to load stats:', err);
    }
  }

  // ── Activity Feed ──────────────────────────────────────────────────────────

  function renderActivityFeed(items) {
    if (!DOM.activityList) return;
    if (!items.length) {
      DOM.activityList.innerHTML =
        '<div class="state-container" style="padding:16px"><span class="state-desc">No recent activity.</span></div>';
      return;
    }
    DOM.activityList.innerHTML = items.map(item => `
      <div class="activity-item" onclick="window.viewReportDetails('${item.report_id}')" style="cursor:pointer;" title="${escapeHtml(item.incident_type)} — ${escapeHtml(item.zone)}">
        <span class="activity-id">${escapeHtml(item.report_id)}</span>
        <span class="activity-incident">${escapeHtml(item.incident_type)}</span>
        <span class="activity-zone">${escapeHtml(item.zone)}</span>
        <span class="badge badge-prio-${(item.priority_category||'low').toLowerCase()} text-xs" style="flex-shrink:0;">${escapeHtml(item.priority_category || 'Low')}</span>
      </div>`).join('');
  }

  // ── Priority Queue Rendering ───────────────────────────────────────────────

  async function loadPriorityQueue() {
    if (!DOM.prioQueueTableBody) return;
    try {
      const res = await window.API.getPriorityReports({ limit: 10 });
      renderPriorityQueueRows(res.items);
    } catch (err) {
      console.error('[dashboard] Failed to load priority queue:', err);
      DOM.prioQueueTableBody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">Unable to load priority queue.</td></tr>`;
    }
  }

  function renderPriorityQueueRows(items) {
    if (!items || items.length === 0) {
      DOM.prioQueueTableBody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">No priority items found.</td></tr>`;
      return;
    }

    DOM.prioQueueTableBody.innerHTML = items.map(r => {
      const prioBadge = `<span class="badge badge-prio-${(r.priority_category || 'low').toLowerCase()}">${r.priority_category} (${r.priority_score.toFixed(1)})</span>`;
      const confBadge = `<span class="badge badge-conf-${(r.confidence_category || 'low').toLowerCase().replace(' ', '-')}">${r.confidence_category} (${r.confidence_score.toFixed(1)})${r.confidence_capped ? ' <span class="badge-capped">Capped</span>' : ''}</span>`;
      const freshBadge = `<span class="badge badge-fresh-${(r.freshness_state || 'unknown').toLowerCase()}">${r.freshness_state}</span>`;
      const statusBadge = `<span class="badge ${statusBadgeClass(r.status)}">${r.status}</span>`;

      return `
        <tr onclick="window.viewReportDetails('${r.report_id}')" style="cursor:pointer;" class="${r.priority_category === 'Critical' ? 'table-danger' : ''}">
          <td class="report-id-cell">🚨 ${escapeHtml(r.report_id)}</td>
          <td><strong>${escapeHtml(r.incident_type)}</strong></td>
          <td>${escapeHtml(r.zone)}</td>
          <td>${prioBadge}</td>
          <td>${confBadge}</td>
          <td>${freshBadge}</td>
          <td>${r.independent_corroboration_count} indep (${r.corroborating_report_count} raw)</td>
          <td>${statusBadge}</td>
          <td>
            <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();window.viewReportDetails('${r.report_id}')">
              View
            </button>
          </td>
        </tr>`;
    }).join('');
  }

  // ── Master Reports Table Rendering ─────────────────────────────────────────

  async function loadReports() {
    if (!DOM.tableBody) return;
    showTableLoading();

    const queryParams = {
      limit: state.currentLimit,
      offset: state.currentOffset,
      search: state.filters.search,
      incident_type: state.filters.incident_type,
      zone: state.filters.zone,
      priority_category: state.filters.priority,
      confidence_category: state.filters.confidence,
      freshness_state: state.filters.freshness,
      status: state.filters.status,
      conflict: state.filters.conflict === 'true' ? true : null,
      correlation: state.filters.correlation === 'true' ? true : null,
    };

    try {
      const res = await window.API.getReports(queryParams);
      state.totalReports = res.total;
      renderTable(res.items);
      renderPagination();
      
      // Update map markers with current filtered results
      if (window.MapModule && window.MapModule.initialized) {
        window.MapModule.renderMarkers(res.items);
      }
    } catch (err) {
      console.error('[dashboard] Failed to load reports:', err);
      showTableError(err.message);
    }
  }

  function showTableLoading() {
    DOM.tableBody.innerHTML = `<tr><td colspan="8"><div class="state-container"><div class="spinner"></div><span class="state-desc">Loading disaster reports...</span></div></td></tr>`;
  }

  function showTableError(msg) {
    DOM.tableBody.innerHTML = `<tr><td colspan="8"><div class="state-container"><div class="state-icon">⚠️</div><div class="state-title">Error loading reports</div><div class="state-desc">${escapeHtml(msg)}</div></div></td></tr>`;
  }

  function renderTable(items) {
    if (!items || items.length === 0) {
      DOM.tableBody.innerHTML = `<tr><td colspan="8"><div class="state-container"><div class="state-icon">🔍</div><div class="state-title">No matching reports found</div><div class="state-desc">Try clearing or adjusting your filters.</div></div></td></tr>`;
      return;
    }

    DOM.tableBody.innerHTML = items.map(r => {
      const prioBadge = `<span class="badge badge-prio-${(r.priority_category || 'low').toLowerCase()}">${r.priority_category} (${r.priority_score.toFixed(0)})</span>`;
      const confBadge = `<span class="badge badge-conf-${(r.confidence_category || 'low').toLowerCase().replace(' ', '-')}">${r.confidence_category} (${r.confidence_score.toFixed(0)})${r.confidence_capped ? ' <span class="badge-capped">Cap</span>' : ''}</span>`;
      const freshBadge = `<span class="badge badge-fresh-${(r.freshness_state || 'unknown').toLowerCase()}">${r.freshness_state}</span>`;
      const statusBadge = `<span class="badge ${statusBadgeClass(r.status)}">${r.status}</span>`;

      let flagIcons = '';
      if (r.conflict_detected) flagIcons += ' ⚔️';
      if (r.duplicate_detected) flagIcons += ' 🔗';

      return `
        <tr onclick="window.viewReportDetails('${r.report_id}')" style="cursor:pointer;">
          <td class="report-id-cell">${escapeHtml(r.report_id)}${flagIcons}</td>
          <td>${escapeHtml(r.incident_type)}</td>
          <td>${escapeHtml(r.zone)}</td>
          <td>${prioBadge}</td>
          <td>${confBadge}</td>
          <td>${freshBadge}</td>
          <td>${statusBadge}</td>
          <td>
            <button class="btn btn-sm btn-ghost" onclick="event.stopPropagation();window.viewReportDetails('${r.report_id}')">
              Details
            </button>
          </td>
        </tr>`;
    }).join('');
  }

  // ── Pagination ─────────────────────────────────────────────────────────────

  function renderPagination() {
    if (!DOM.paginationInfo) return;
    const start = state.totalReports === 0 ? 0 : state.currentOffset + 1;
    const end   = Math.min(state.currentOffset + state.currentLimit, state.totalReports);
    DOM.paginationInfo.textContent = `Showing ${start}–${end} of ${state.totalReports.toLocaleString()} reports`;

    if (DOM.prevBtn) DOM.prevBtn.disabled = state.currentOffset === 0;
    if (DOM.nextBtn) DOM.nextBtn.disabled = state.currentOffset + state.currentLimit >= state.totalReports;
  }

  // ── Role View Adaptation ───────────────────────────────────────────────────

  function applyRoleView(role) {
    state.currentRole = role;
    const prioSection = document.getElementById('priority-queue-section');

    if (role === 'Responder') {
      if (prioSection) prioSection.style.display = 'block';
      state.filters.priority = 'Critical';
      if (DOM.priorityFilter) DOM.priorityFilter.value = 'Critical';
    } else if (role === 'City Official') {
      if (prioSection) prioSection.style.display = 'none';
      state.filters.confidence = 'High';
      if (DOM.confidenceFilter) DOM.confidenceFilter.value = 'High';
      state.filters.priority = '';
      if (DOM.priorityFilter) DOM.priorityFilter.value = '';
    } else if (role === 'Coordinator') {
      if (prioSection) prioSection.style.display = 'block';
      state.filters.conflict = 'true';
      if (DOM.conflictFilter) DOM.conflictFilter.value = 'true';
      state.filters.priority = '';
      if (DOM.priorityFilter) DOM.priorityFilter.value = '';
    }
    state.currentOffset = 0;
    loadReports();
  }

  // ── Event Handlers ─────────────────────────────────────────────────────────

  function bindEvents() {
    if (DOM.refreshBtn) {
      DOM.refreshBtn.addEventListener('click', () => {
        loadStats();
        loadPriorityQueue();
        loadReports();
      });
    }

    if (DOM.roleSelect) {
      DOM.roleSelect.addEventListener('change', (e) => applyRoleView(e.target.value));
    }

    if (DOM.clearFiltersBtn) {
      DOM.clearFiltersBtn.addEventListener('click', () => {
        state.filters = {
          search: '', incident_type: '', zone: '', priority: '',
          confidence: '', freshness: '', status: '', conflict: '', correlation: '',
        };
        [
          DOM.searchInput, DOM.incidentFilter, DOM.zoneFilter, DOM.priorityFilter,
          DOM.confidenceFilter, DOM.freshnessFilter, DOM.statusFilter,
          DOM.conflictFilter, DOM.correlationFilter,
        ].forEach(el => { if (el) el.value = ''; });
        state.currentOffset = 0;
        loadReports();
      });
    }

    const bindFilter = (inputEl, filterKey) => {
      if (!inputEl) return;
      inputEl.addEventListener('change', () => {
        state.filters[filterKey] = inputEl.value;
        state.currentOffset = 0;
        loadReports();
      });
    };

    bindFilter(DOM.incidentFilter, 'incident_type');
    bindFilter(DOM.zoneFilter, 'zone');
    bindFilter(DOM.priorityFilter, 'priority');
    bindFilter(DOM.confidenceFilter, 'confidence');
    bindFilter(DOM.freshnessFilter, 'freshness');
    bindFilter(DOM.statusFilter, 'status');
    bindFilter(DOM.conflictFilter, 'conflict');
    bindFilter(DOM.correlationFilter, 'correlation');

    if (DOM.searchInput) {
      let timeout = null;
      DOM.searchInput.addEventListener('input', () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          state.filters.search = DOM.searchInput.value.trim();
          state.currentOffset = 0;
          loadReports();
        }, 300);
      });
    }

    if (DOM.prevBtn) {
      DOM.prevBtn.addEventListener('click', () => {
        if (state.currentOffset > 0) {
          state.currentOffset = Math.max(0, state.currentOffset - state.currentLimit);
          loadReports();
        }
      });
    }

    if (DOM.nextBtn) {
      DOM.nextBtn.addEventListener('click', () => {
        if (state.currentOffset + state.currentLimit < state.totalReports) {
          state.currentOffset += state.currentLimit;
          loadReports();
        }
      });
    }
  }

  function statusBadgeClass(status) {
    const map = {
      'Verified': 'badge-verified',
      'Pending': 'badge-pending',
      'Rejected': 'badge-rejected',
      'Needs Review': 'badge-needs-review',
    };
    return map[status] || 'badge-default';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // ── Initialize ─────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    cacheDom();
    bindEvents();
    loadStats();
    loadPriorityQueue();
    loadReports();
  });

})();
