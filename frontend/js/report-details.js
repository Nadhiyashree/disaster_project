/**
 * report-details.js
 * =================
 * Dedicated controller for report-details.html page.
 */

(function () {
  'use strict';

  let currentReportId = null;

  document.addEventListener('DOMContentLoaded', async function () {
    const params = new URLSearchParams(window.location.search);
    currentReportId = params.get('id');

    if (!currentReportId) {
      document.getElementById('summary-grid').innerHTML =
        '<div class="alert-box alert-conflict">No Report ID specified. Please select a report from the Command Center or Reports page.</div>';
      return;
    }

    await loadReportDetails(currentReportId);
  });

  async function loadReportDetails(reportId) {
    try {
      const data = await window.API.getReport(reportId);
      renderDetailsPage(data);
    } catch (err) {
      console.error('[report-details.js] Failed to load details:', err);
      document.getElementById('summary-grid').innerHTML =
        `<div class="alert-box alert-conflict">Report '${APP.escapeHtml(reportId)}' not found or server error.</div>`;
    }
  }

  function renderDetailsPage(data) {
    const r = data.report;
    const c = data.confidence;
    const p = data.priority;
    const f = data.freshness;

    document.getElementById('report-id-badge').textContent = r.report_id;

    // Summary Grid
    document.getElementById('summary-grid').innerHTML = `
      <div class="detail-field">
        <span class="detail-label">Report ID</span>
        <span class="detail-value text-mono text-accent">${APP.escapeHtml(r.report_id)}</span>
      </div>
      <div class="detail-field">
        <span class="detail-label">Incident Type</span>
        <span class="detail-value"><strong>${APP.escapeHtml(r.incident_type)}</strong></span>
      </div>
      <div class="detail-field">
        <span class="detail-label">Zone</span>
        <span class="detail-value">${APP.escapeHtml(r.zone)}</span>
      </div>
      <div class="detail-field">
        <span class="detail-label">Department</span>
        <span class="detail-value">${APP.escapeHtml(r.department)}</span>
      </div>
      <div class="detail-field">
        <span class="detail-label">Source Type</span>
        <span class="detail-value">${APP.escapeHtml(r.source_type)}</span>
      </div>
      <div class="detail-field">
        <span class="detail-label">Verification Status</span>
        <span class="detail-value"><span class="badge ${APP.statusBadgeClass(r.status)}">${APP.escapeHtml(r.status)}</span></span>
      </div>
      <div class="detail-field">
        <span class="detail-label">Permit Impact</span>
        <span class="detail-value">${APP.escapeHtml(r.permit_impact)}</span>
      </div>
      <div class="detail-field">
        <span class="detail-label">Timestamp</span>
        <span class="detail-value">${APP.formatTimestamp(r.timestamp)}</span>
      </div>
      <div class="detail-field">
        <span class="detail-label">Last Updated</span>
        <span class="detail-value">${APP.formatTimestamp(r.last_updated)}</span>
      </div>
      <div class="detail-field full-width">
        <span class="detail-label">Incident Description</span>
        <div class="detail-desc">${APP.escapeHtml(r.description)}</div>
      </div>`;

    // Alerts
    const alertsContainer = document.getElementById('alert-container');
    alertsContainer.innerHTML = '';
    if (c.capped) {
      alertsContainer.innerHTML += `
        <div class="alert-box alert-cap">
          <div class="alert-title">🔒 CONFIDENCE CAPPED</div>
          <div>${APP.escapeHtml(c.cap_reason)}</div>
        </div>`;
    }
    if (r.conflict_detected) {
      alertsContainer.innerHTML += `
        <div class="alert-box alert-conflict">
          <div class="alert-title">⚔️ CONFLICT DETECTED</div>
          <div>${APP.escapeHtml(r.conflict_explanation)} Related Reports: ${r.related_report_ids.join(', ')}</div>
        </div>`;
    }
    if (r.duplicate_detected) {
      alertsContainer.innerHTML += `
        <div class="alert-box alert-correlation">
          <div class="alert-title">🔗 CORRELATED REPORT GROUP (${r.correlation_group_id})</div>
          <div>${APP.escapeHtml(r.similarity_reason)}</div>
        </div>`;
    }

    // Confidence Card
    document.getElementById('conf-score-val').textContent = `${c.score.toFixed(1)} / 100`;
    const confBadgeEl = document.getElementById('conf-category-badge');
    confBadgeEl.textContent = c.category;
    confBadgeEl.className = `badge badge-conf-${c.category.toLowerCase().replace(' ', '-')}`;
    const confFill = document.getElementById('conf-progress-fill');
    confFill.style.width = `${Math.min(100, c.score)}%`;
    confFill.className = `progress-bar-fill ${c.score >= 70 ? 'bg-success' : (c.score >= 40 ? 'bg-medium' : 'bg-low')}`;

    if (c.capped) {
      document.getElementById('conf-capped-notice').style.display = 'block';
    } else {
      document.getElementById('conf-capped-notice').style.display = 'none';
    }

    // Priority Card
    document.getElementById('prio-score-val').textContent = `${p.score.toFixed(1)} / 100`;
    const prioBadgeEl = document.getElementById('prio-category-badge');
    prioBadgeEl.textContent = p.category;
    prioBadgeEl.className = `badge badge-prio-${p.category.toLowerCase()}`;
    const prioFill = document.getElementById('prio-progress-fill');
    prioFill.style.width = `${Math.min(100, p.score)}%`;
    prioFill.className = `progress-bar-fill ${p.score >= 80 ? 'bg-critical' : (p.score >= 60 ? 'bg-high' : 'bg-medium')}`;
    document.getElementById('fresh-state-val').textContent = f.state;

    // Confidence Breakdown Table
    document.getElementById('conf-summary-text').textContent = c.explanation.summary;
    const confComps = c.explanation.components || {};
    let confRows = '';
    for (const [key, item] of Object.entries(confComps)) {
      confRows += `
        <tr>
          <td style="font-weight:600;color:var(--text-primary);">${formatKeyName(key)}</td>
          <td>${(item.weight * 100).toFixed(0)}%</td>
          <td>${item.precision || item.source_type || item.media_type || item.status || (item.value * 100).toFixed(0) + '%'}</td>
          <td style="font-weight:700;color:var(--accent-primary);">${item.contribution.toFixed(2)} pts</td>
        </tr>`;
    }
    document.getElementById('conf-breakdown-rows').innerHTML = confRows;

    // Priority Breakdown Table
    document.getElementById('prio-explanation-text').textContent = p.explanation.text || 'N/A';
    const prioExp = p.explanation || {};
    let prioRows = `
      <tr>
        <td style="font-weight:600;">Incident Severity</td>
        <td>35%</td>
        <td>${prioExp.incident_severity?.label || 'N/A'} (${((prioExp.incident_severity?.value || 0)*100).toFixed(0)}%)</td>
        <td style="font-weight:700;color:var(--accent-primary);">${prioExp.incident_severity?.contribution || 0} pts</td>
      </tr>
      <tr>
        <td style="font-weight:600;">Confidence Contribution</td>
        <td>30%</td>
        <td>${prioExp.confidence_contribution?.label || 'N/A'}</td>
        <td style="font-weight:700;color:var(--accent-primary);">${prioExp.confidence_contribution?.contribution || 0} pts</td>
      </tr>
      <tr>
        <td style="font-weight:600;">Freshness Urgency</td>
        <td>20%</td>
        <td>${prioExp.freshness_urgency?.label || 'N/A'}</td>
        <td style="font-weight:700;color:var(--accent-primary);">${prioExp.freshness_urgency?.contribution || 0} pts</td>
      </tr>
      <tr>
        <td style="font-weight:600;">Operational Urgency</td>
        <td>15%</td>
        <td>${prioExp.operational_urgency?.label || 'N/A'}</td>
        <td style="font-weight:700;color:var(--accent-primary);">${prioExp.operational_urgency?.contribution || 0} pts</td>
      </tr>`;
    document.getElementById('prio-breakdown-rows').innerHTML = prioRows;

    // Freshness Panel
    const freshStateText = document.getElementById('fresh-state-text');
    freshStateText.textContent = f.state;
    freshStateText.className = `badge badge-fresh-${f.state.toLowerCase()}`;
    document.getElementById('fresh-ts-text').textContent = APP.formatTimestamp(r.timestamp);
    document.getElementById('fresh-min-text').textContent = f.minutes_since_report != null ? `${f.minutes_since_report} minutes ago` : 'Unknown';
    document.getElementById('fresh-lu-text').textContent = APP.formatTimestamp(r.last_updated);

    if (f.state === 'Stale') {
      const warnBox = document.getElementById('fresh-warning-box');
      warnBox.style.display = 'block';
      warnBox.textContent = 'STALE REPORT: This report is older than 6 hours and should be interpreted with caution.';
    }

    // Media Evidence Panel
    document.getElementById('media-type-text').textContent = r.media_type;

    // Conflicts Section
    const conflictArea = document.getElementById('conflict-content-area');
    if (r.conflict_detected) {
      let relList = (data.conflicts || []).map(c => `<li><strong>${c.report_id}</strong> (${c.incident_type}): ${APP.escapeHtml(c.description)} [Status: ${c.status}]</li>`).join('');
      conflictArea.innerHTML = `
        <div class="alert-box alert-conflict">
          <div class="alert-title">⚔️ CONFLICT DETECTED</div>
          <p>${APP.escapeHtml(r.conflict_explanation)}</p>
          <div style="margin-top:8px;"><strong>Related Conflicting Reports:</strong><ul>${relList || r.related_report_ids.join(', ')}</ul></div>
        </div>`;
    } else {
      conflictArea.innerHTML = '<div class="text-muted text-sm">✅ No known conflicting observations detected for this incident location.</div>';
    }

    // Correlation Section
    const correlationArea = document.getElementById('correlation-content-area');
    if (r.duplicate_detected) {
      let corrList = (data.correlated_reports || []).map(cr => `<li><strong>${cr.report_id}</strong> (${cr.zone}): ${APP.escapeHtml(cr.description)}</li>`).join('');
      correlationArea.innerHTML = `
        <div class="alert-box alert-correlation">
          <div class="alert-title">🔗 CORRELATED REPORT GROUP (${r.correlation_group_id})</div>
          <p>${APP.escapeHtml(r.similarity_reason)}</p>
          ${r.corroboration_adjustment_note ? `<p style="margin-top:4px;font-style:italic;">Note: ${APP.escapeHtml(r.corroboration_adjustment_note)}</p>` : ''}
          <div style="margin-top:8px;"><strong>Correlated Observations:</strong><ul>${corrList || r.related_report_ids.join(', ')}</ul></div>
        </div>`;
    } else {
      correlationArea.innerHTML = '<div class="text-muted text-sm">ℹ️ Report is an independent observation with no duplicate clustering.</div>';
    }

    // Location Panel
    document.getElementById('loc-lat').textContent = r.latitude.toFixed(5);
    document.getElementById('loc-lon').textContent = r.longitude.toFixed(5);
    document.getElementById('loc-zone').textContent = r.zone;
    document.getElementById('loc-prec').textContent = r.location_precision;
  }

  window.confirmVerification = function (targetStatus) {
    if (!currentReportId) return;

    APP.showConfirmationModal({
      title: 'Confirm Verification Status Change',
      message: `You are changing the operational status of report '${currentReportId}' to '${targetStatus}'. This action updates responder confidence across the system.`,
      confirmText: `Set ${targetStatus}`,
      onConfirm: async () => {
        const msgEl = document.getElementById('verification-status-msg');
        msgEl.innerHTML = `<span class="text-muted">Updating verification status...</span>`;
        try {
          await window.API.verifyReport(currentReportId, targetStatus);
          APP.showToast(`Report '${currentReportId}' status updated to '${targetStatus}'.`, 'success');
          msgEl.innerHTML = `<span style="color:var(--accent-success);font-weight:600;">✅ Verification status successfully updated to '${targetStatus}'. Reloading intelligence scores...</span>`;
          await loadReportDetails(currentReportId);
        } catch (err) {
          console.error('[report-details.js] Verification error:', err);
          APP.showToast(`Unable to update verification status: ${err.message}`, 'error');
          msgEl.innerHTML = `<span style="color:var(--accent-danger);font-weight:600;">❌ Verification failed: ${APP.escapeHtml(err.message)}</span>`;
        }
      },
    });
  };

  function formatKeyName(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

})();
