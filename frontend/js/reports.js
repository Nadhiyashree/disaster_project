/**
 * reports.js
 * ==========
 * Controller for reports.html page.
 */

(function () {
  'use strict';

  const DEFAULT_LIMIT = 25;

  const state = {
    offset: 0,
    limit: DEFAULT_LIMIT,
    total: 0,
    filters: {
      search: '',
      incident_type: '',
      zone: '',
      priority: '',
      confidence: '',
      freshness: '',
      status: '',
      source_type: '',
      sort_by: 'priority_score',
    },
  };

  const DOM = {};

  function cacheDom() {
    DOM.tbody = document.getElementById('reports-table-body');
    DOM.info = document.getElementById('pagination-info');
    DOM.prev = document.getElementById('btn-prev');
    DOM.next = document.getElementById('btn-next');
    DOM.clearBtn = document.getElementById('btn-clear-filters');

    DOM.search = document.getElementById('filter-search');
    DOM.incident = document.getElementById('filter-incident');
    DOM.zone = document.getElementById('filter-zone');
    DOM.priority = document.getElementById('filter-priority');
    DOM.confidence = document.getElementById('filter-confidence');
    DOM.freshness = document.getElementById('filter-freshness');
    DOM.status = document.getElementById('filter-status');
    DOM.source = document.getElementById('filter-source');
    DOM.sort = document.getElementById('filter-sort');
  }

  async function fetchAndRender() {
    if (!DOM.tbody) return;
    DOM.tbody.innerHTML = `<tr><td colspan="10"><div class="state-container"><div class="spinner"></div><span class="state-desc">Loading reports...</span></div></td></tr>`;

    try {
      const query = {
        limit: state.limit,
        offset: state.offset,
        search: state.filters.search,
        incident_type: state.filters.incident_type,
        zone: state.filters.zone,
        priority_category: state.filters.priority,
        confidence_category: state.filters.confidence,
        freshness_state: state.filters.freshness,
        status: state.filters.status,
        source_type: state.filters.source_type,
        sort_by: state.filters.sort_by,
        sort_order: 'desc',
      };

      const data = await window.API.getReports(query);
      state.total = data.total;
      renderRows(data.items);
      renderPagination();
    } catch (err) {
      console.error('[reports.js] Load error:', err);
      DOM.tbody.innerHTML = `<tr><td colspan="10" class="text-center text-muted">Error loading reports: ${APP.escapeHtml(err.message)}</td></tr>`;
    }
  }

  function renderRows(items) {
    if (!items || items.length === 0) {
      DOM.tbody.innerHTML = `<tr><td colspan="10"><div class="state-container"><div class="state-icon">🔍</div><div class="state-title">No matching reports found</div><div class="state-desc">Try clearing or adjusting your search filters.</div></div></td></tr>`;
      return;
    }

    DOM.tbody.innerHTML = items.map(r => {
      const prioBadge = `<span class="badge badge-prio-${(r.priority_category || 'low').toLowerCase()}">${r.priority_category} (${r.priority_score.toFixed(0)})</span>`;
      const confBadge = `<span class="badge badge-conf-${(r.confidence_category || 'low').toLowerCase().replace(' ', '-')}">${r.confidence_category} (${r.confidence_score.toFixed(0)})${r.confidence_capped ? ' <span class="badge-capped">Cap</span>' : ''}</span>`;
      const freshBadge = `<span class="badge badge-fresh-${(r.freshness_state || 'unknown').toLowerCase()}">${r.freshness_state}</span>`;
      const statusBadge = `<span class="badge ${APP.statusBadgeClass(r.status)}">${r.status}</span>`;

      return `
        <tr onclick="window.location.href='/report-details.html?id=${encodeURIComponent(r.report_id)}'" style="cursor:pointer;">
          <td class="report-id-cell">${APP.escapeHtml(r.report_id)}</td>
          <td><strong>${APP.escapeHtml(r.incident_type)}</strong></td>
          <td>${APP.escapeHtml(r.zone)}</td>
          <td>${APP.escapeHtml(r.source_type)}</td>
          <td>${prioBadge}</td>
          <td>${confBadge}</td>
          <td>${freshBadge}</td>
          <td>${statusBadge}</td>
          <td>${APP.escapeHtml(r.department)}</td>
          <td>
            <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation();window.location.href='/report-details.html?id=${encodeURIComponent(r.report_id)}'">
              View
            </button>
          </td>
        </tr>`;
    }).join('');
  }

  function renderPagination() {
    if (!DOM.info) return;
    const start = state.total === 0 ? 0 : state.offset + 1;
    const end = Math.min(state.offset + state.limit, state.total);
    DOM.info.textContent = `Showing ${start}–${end} of ${state.total.toLocaleString()} reports`;

    if (DOM.prev) DOM.prev.disabled = state.offset === 0;
    if (DOM.next) DOM.next.disabled = state.offset + state.limit >= state.total;
  }

  function bindEvents() {
    const bindSelect = (el, key) => {
      if (!el) return;
      el.addEventListener('change', () => {
        state.filters[key] = el.value;
        state.offset = 0;
        fetchAndRender();
      });
    };

    bindSelect(DOM.incident, 'incident_type');
    bindSelect(DOM.zone, 'zone');
    bindSelect(DOM.priority, 'priority');
    bindSelect(DOM.confidence, 'confidence');
    bindSelect(DOM.freshness, 'freshness');
    bindSelect(DOM.status, 'status');
    bindSelect(DOM.source, 'source_type');
    bindSelect(DOM.sort, 'sort_by');

    if (DOM.search) {
      let timeout = null;
      DOM.search.addEventListener('input', () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          state.filters.search = DOM.search.value.trim();
          state.offset = 0;
          fetchAndRender();
        }, 300);
      });
    }

    if (DOM.clearBtn) {
      DOM.clearBtn.addEventListener('click', () => {
        state.filters = {
          search: '', incident_type: '', zone: '', priority: '',
          confidence: '', freshness: '', status: '', source_type: '',
          sort_by: 'priority_score',
        };
        [DOM.search, DOM.incident, DOM.zone, DOM.priority, DOM.confidence, DOM.freshness, DOM.status, DOM.source].forEach(el => {
          if (el) el.value = '';
        });
        if (DOM.sort) DOM.sort.value = 'priority_score';
        state.offset = 0;
        fetchAndRender();
      });
    }

    if (DOM.prev) {
      DOM.prev.addEventListener('click', () => {
        if (state.offset > 0) {
          state.offset = Math.max(0, state.offset - state.limit);
          fetchAndRender();
        }
      });
    }

    if (DOM.next) {
      DOM.next.addEventListener('click', () => {
        if (state.offset + state.limit < state.total) {
          state.offset += state.limit;
          fetchAndRender();
        }
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    cacheDom();
    bindEvents();
    fetchAndRender();
  });
})();
