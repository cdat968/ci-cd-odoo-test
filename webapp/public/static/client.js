(function () {
  var meta = window.__REPORT_META__;
  var patches = window.__REPORT_PATCHES__ || [];

  if (!meta || !meta.report_id) return;

  // Patch lookup by bug_id
  var patchMap = {};
  patches.forEach(function (p) { if (p.bug_id) patchMap[p.bug_id] = p; });

  function esc(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  // Apply server-side patches to the rendered table rows
  // Column order from renderRows(): 0=id, 1=summary, 2=steps, 3=priority, 4=feature,
  // 5=build, 6=reproducibility, 7=severity, 8=frequency, 9=keyword,
  // 10=status, 11=resolution, 12=note, 13=suggestedFix, 14=view
  function applyPatches() {
    patches.forEach(function (p) {
      if (!p.bug_id) return;
      var row = document.querySelector('tr[data-bug-id="' + p.bug_id + '"]');
      if (!row) return;
      var tds = row.querySelectorAll('td');
      if (p.resolution && tds[11]) {
        tds[11].innerHTML = '<span class="badge option">' + esc(p.resolution) + '</span>';
      }
      if (p.note && tds[12]) {
        tds[12].textContent = p.note;
      }
    });
  }

  // Track which ticket modal is open
  var currentBugId = null;
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-view-ticket]');
    if (btn) currentBugId = btn.getAttribute('data-view-ticket');
  }, true);

  // Intercept Save button — also PATCH to backend
  document.addEventListener('click', function (e) {
    if (!e.target.closest('#saveTicketUpdate')) return;
    if (!currentBugId) return;

    var noteEl = document.getElementById('ticketNoteControl');
    var picker = document.querySelector('.resolution-picker');
    var note = noteEl ? noteEl.value : null;
    var resolution = picker ? picker.dataset.selectedResolution : null;

    var url = meta.backend_url
      + '/api/reports/' + encodeURIComponent(meta.report_id)
      + '/bugs/' + encodeURIComponent(currentBugId)
      + '?t=' + encodeURIComponent(meta.share_token);

    fetch(url, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ note: note, resolution: resolution, updated_by: 'webapp-user' }),
    })
      .then(function (r) { return r.json(); })
      .then(function (updated) {
        // Keep local patch map in sync
        patchMap[currentBugId] = Object.assign(patchMap[currentBugId] || {}, updated);
      })
      .catch(function (err) {
        console.warn('[qa-client] backend save failed:', err);
      });
  });

  // renderRows() already ran synchronously — apply patches on next frame
  requestAnimationFrame(applyPatches);
})();
