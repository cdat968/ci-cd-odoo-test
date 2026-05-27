'use client';

import { useState, useCallback, useRef } from 'react';
import type { BugRecord, ReportMeta } from '@/types';

interface Props {
  bugs: BugRecord[];
  metadata: ReportMeta;
  reportId: string;
  shareToken: string;
}

const RESOLUTION_OPTIONS = [
  'n/a', 'Fixed', "Won't Fix", 'Duplicate',
  'Cannot Reproduce', 'Not a Bug', 'Deferred',
];

const CSS = `
#rvr{--ink:#172033;--muted:#5f6b7a;--line:#d8e0eb;--paper:#fff;--bg:#f5f7fb;--navy:#173b63;--green:#15803d;--red:#b91c1c;--orange:#c2410c;--blue:#2454d6;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg);line-height:1.5;min-height:100vh}
#rvr *,#rvr *::before,#rvr *::after{box-sizing:border-box}
#rvr .page{max-width:1280px;margin:0 auto;padding:28px 20px 56px}
#rvr .hero{background:var(--navy);color:white;padding:30px;border-radius:8px;border:1px solid #0f2d4f}
#rvr .hero h1{margin:0 0 10px;font-size:32px;line-height:1.15}
#rvr .kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-top:16px}
#rvr .kpi{background:white;color:var(--ink);border-radius:8px;padding:14px;border:1px solid var(--line)}
#rvr .kpi strong{display:block;font-size:28px;line-height:1}
#rvr .kpi span{color:var(--muted);font-size:13px}
#rvr section{margin-top:22px;background:var(--paper);border:1px solid var(--line);border-radius:8px;overflow:hidden}
#rvr .section-head{padding:18px 20px;border-bottom:1px solid var(--line);background:#fbfcfe}
#rvr .section-head h2{margin:0;font-size:20px}
#rvr .section-body{padding:18px 20px 22px}
#rvr .table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px}
#rvr table{width:100%;border-collapse:collapse;min-width:1100px;background:white}
#rvr th,#rvr td{padding:10px 11px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left;font-size:13px}
#rvr th{background:#eef3f8;color:#344054;text-transform:uppercase;font-size:12px;letter-spacing:.03em;font-weight:600}
#rvr tbody tr:nth-child(even) td{background:#eef6ff}
#rvr tbody tr:nth-child(odd) td{background:#fff}
#rvr .badge{display:inline-flex;align-items:center;border-radius:8px;padding:3px 8px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#f8fafc;color:#334155;white-space:nowrap}
#rvr .b-bug{background:#fff1f2;color:var(--red);border-color:#fecdd3}
#rvr .b-new{background:#fff1f2;color:var(--red);border-color:#fecdd3}
#rvr .b-fixed{background:#f0fdf4;color:var(--green);border-color:#bbf7d0}
#rvr .b-priority{background:#fff7ed;color:var(--orange);border-color:#fed7aa}
#rvr .b-feature{background:#ecfeff;color:#0e7490;border-color:#67e8f9}
#rvr .summary-cell{color:green;font-weight:900;font-size:15px}
#rvr .opt{display:none}
#rvr.show-opt .opt{display:table-cell}
#rvr .filter-bar{display:flex;flex-wrap:wrap;gap:10px;align-items:end;margin-bottom:14px}
#rvr .ff{display:grid;gap:5px;min-width:160px}
#rvr .ff label{font-size:12px;font-weight:900;color:#475569}
#rvr .ff select{height:36px;border:1px solid #cbd5e1;border-radius:8px;background:white;color:#172033;padding:0 10px;font-weight:800;font-size:13px}
#rvr .btn{border:1px solid #d8dee8;background:white;border-radius:8px;padding:8px 11px;font-weight:900;cursor:pointer;font-size:13px}
#rvr .btn-primary{background:var(--blue);border-color:var(--blue);color:white}
#rvr .btn-reset{color:#172033;border-color:#cbd5e1}
#rvr .btn-toggle{margin-bottom:12px}
#rvr .note-ta{width:100%;min-height:56px;border:1px solid #cbd5e1;border-radius:6px;padding:5px 7px;font-size:12px;font-family:inherit;resize:vertical}
#rvr .res-sel{height:28px;border:1px solid #cbd5e1;border-radius:6px;background:white;font-size:12px;padding:0 4px;min-width:110px}
#rvr .modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:flex-start;justify-content:center;z-index:9999;overflow-y:auto;padding:32px 16px}
#rvr .modal{background:white;border-radius:10px;width:100%;max-width:1240px;overflow:hidden}
#rvr .modal-hdr{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:20px 24px;border-bottom:1px solid var(--line);background:#fbfcfe}
#rvr .modal-hdr h2{margin:0;font-size:20px}
#rvr .modal-sub{color:var(--muted);font-size:13px;margin-top:4px}
#rvr .modal-actions{display:flex;gap:8px;flex-wrap:wrap;flex-shrink:0}
#rvr .modal-body{padding:24px}
#rvr .tgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
#rvr .tf{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:14px}
#rvr .tf.wide{grid-column:span 2}
#rvr .tf.full{grid-column:1/-1}
#rvr .tf.summary-main{grid-column:span 2;background:#eff6ff;border-color:#bfdbfe}
#rvr .tf.f-exp{background:#f0fdf4;border-color:#bbf7d0}
#rvr .tf.f-obs{background:#fff7f7;border-color:#fecdd3}
#rvr .tlabel{display:block;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:6px}
#rvr .tval{font-size:14px}
#rvr .steps{margin:0;padding-left:0;list-style:none;display:flex;flex-direction:column;gap:6px}
#rvr .steps li{font-size:13px;display:flex;gap:8px}
#rvr .step-code{font-weight:700;color:var(--blue);white-space:nowrap}
#rvr .ev-section{margin-top:24px}
#rvr .ev-section h3{margin:0 0 14px;font-size:16px}
#rvr .ev-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
#rvr .ev-card{border:1px solid var(--line);border-radius:8px;overflow:hidden;background:white;cursor:pointer;transition:border-color .15s}
#rvr .ev-card:hover{border-color:#93c5fd}
#rvr .ev-cap{font-size:12px;font-weight:600;padding:8px 10px;background:#f8fafc;border-bottom:1px solid var(--line)}
#rvr .ev-img{padding:8px}
#rvr .ev-img img{width:100%;height:auto;max-height:200px;object-fit:contain;display:block}
#rvr .viewer-bg{position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:stretch;z-index:10000}
#rvr .viewer-panel{background:white;border-radius:10px;margin:24px;flex:1;display:flex;flex-direction:column;overflow:hidden}
#rvr .viewer-hdr{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:14px 18px;border-bottom:1px solid var(--line);background:#fbfcfe;flex-shrink:0}
#rvr .viewer-hdr h2{margin:0;font-size:15px;line-height:1.3;overflow-wrap:anywhere}
#rvr .viewer-hdr .modal-actions{flex-wrap:nowrap}
#rvr .viewer-body{flex:1;overflow:auto;display:flex;align-items:flex-start;justify-content:center;padding:20px}
#rvr .viewer-body img{display:block;max-width:100%;border:1px solid #cbd5e1;background:#fff;transform-origin:top center;transition:transform .15s}
@media(max-width:900px){
  #rvr .page{padding:14px 10px 34px}
  #rvr .kpis,#rvr .tgrid,#rvr .ev-grid{grid-template-columns:1fr}
  #rvr .tf.wide,#rvr .tf.summary-main{grid-column:1}
  #rvr .hero h1{font-size:26px}
}
`;

function dayDiff(refDate: string, targetDate: string): number {
  if (!targetDate) return Infinity;
  const base = new Date(refDate + 'T00:00:00');
  const target = new Date(targetDate + 'T00:00:00');
  return Math.floor((base.getTime() - target.getTime()) / 86400000);
}

export default function ReportViewer({ bugs: initialBugs, metadata, reportId, shareToken }: Props) {
  const [bugs, setBugs] = useState<BugRecord[]>(initialBugs);
  const [filterFeature, setFilterFeature] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterDate, setFilterDate] = useState('');
  const [activeFilters, setActiveFilters] = useState({ feature: '', priority: '', status: '', date: '' });
  const [showOpt, setShowOpt] = useState(false);
  const [activeTicket, setActiveTicket] = useState<BugRecord | null>(null);
  const [viewerBug, setViewerBug] = useState<BugRecord | null>(null);
  const [viewerIdx, setViewerIdx] = useState(0);
  const [zoom, setZoom] = useState(1);
  const modalBgRef = useRef<HTMLDivElement>(null);

  const refDate = metadata.report_date || new Date().toISOString().slice(0, 10);

  const features = Array.from(new Set(bugs.map(b => b.feature).filter(Boolean)));
  const priorities = Array.from(new Set(bugs.map(b => b.priority).filter(Boolean)));

  const filteredBugs = bugs.filter(b => {
    if (activeFilters.feature && b.feature !== activeFilters.feature) return false;
    if (activeFilters.priority && b.priority !== activeFilters.priority) return false;
    if (activeFilters.status && b.status !== activeFilters.status) return false;
    if (activeFilters.date) {
      const diff = dayDiff(refDate, b.createdAt);
      if (activeFilters.date === 'today' && diff !== 0) return false;
      if (activeFilters.date === 'last3' && (diff < 0 || diff > 3)) return false;
      if (activeFilters.date === 'last7' && (diff < 0 || diff > 7)) return false;
    }
    return true;
  });

  const applyFilter = useCallback(() => {
    setActiveFilters({ feature: filterFeature, priority: filterPriority, status: filterStatus, date: filterDate });
  }, [filterFeature, filterPriority, filterStatus, filterDate]);

  const resetFilter = useCallback(() => {
    setFilterFeature(''); setFilterPriority(''); setFilterStatus(''); setFilterDate('');
    setActiveFilters({ feature: '', priority: '', status: '', date: '' });
  }, []);

  async function patchBug(bugId: string, data: { note?: string; resolution?: string }) {
    setBugs(prev => prev.map(b => b.id === bugId ? { ...b, ...data } : b));
    try {
      await fetch(`/api/reports/${reportId}/bugs/${bugId}?t=${encodeURIComponent(shareToken)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    } catch (_) { /* best-effort */ }
  }

  function openViewer(bug: BugRecord, idx: number) {
    setViewerBug(bug); setViewerIdx(idx); setZoom(1);
  }

  const openBugs = bugs.filter(b => b.status !== 'Fixed').length;
  const highPri = bugs.filter(b => b.priority?.includes('P2')).length;

  return (
    <div id="rvr" className={showOpt ? 'show-opt' : ''}>
      <style dangerouslySetInnerHTML={{ __html: CSS }} />
      <main className="page">

        {/* ── Hero ── */}
        <header className="hero">
          <h1>{metadata.project_name || 'Bug Report'}</h1>
          <div className="kpis">
            <div className="kpi"><strong>{bugs.length}</strong><span>Total Bugs</span></div>
            <div className="kpi"><strong>{openBugs}</strong><span>Open Bugs</span></div>
            <div className="kpi"><strong>{highPri}</strong><span>High Priority</span></div>
            <div className="kpi"><strong>{metadata.report_date || '—'}</strong><span>Report Date</span></div>
          </div>
        </header>

        {/* ── Bug Table ── */}
        <section id="bug">
          <div className="section-head"><h2>Bug Report Table</h2></div>
          <div className="section-body">

            {/* Filter bar */}
            <div className="filter-bar">
              <div className="ff">
                <label>Feature</label>
                <select value={filterFeature} onChange={e => setFilterFeature(e.target.value)}>
                  <option value="">All</option>
                  {features.map(f => <option key={f} value={f}>{f}</option>)}
                </select>
              </div>
              <div className="ff">
                <label>Priority</label>
                <select value={filterPriority} onChange={e => setFilterPriority(e.target.value)}>
                  <option value="">All</option>
                  {priorities.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </div>
              <div className="ff">
                <label>Status</label>
                <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                  <option value="">All</option>
                  <option value="New">New</option>
                  <option value="Fixed">Fixed</option>
                </select>
              </div>
              <div className="ff">
                <label>Bug Date</label>
                <select value={filterDate} onChange={e => setFilterDate(e.target.value)}>
                  <option value="">All</option>
                  <option value="today">Today</option>
                  <option value="last3">3 days ago</option>
                  <option value="last7">One week ago</option>
                </select>
              </div>
              <button className="btn btn-primary btn-toggle" style={{ alignSelf: 'flex-end' }} onClick={applyFilter}>Filter</button>
              <button className="btn btn-reset" style={{ alignSelf: 'flex-end' }} onClick={resetFilter}>Reset</button>
            </div>

            <button className="btn btn-toggle" onClick={() => setShowOpt(v => !v)}>
              {showOpt ? 'Hide optional fields' : 'Show all bug fields'}
            </button>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Summary</th>
                    <th>Steps to Reproduce</th>
                    <th>Priority</th>
                    <th>Feature</th>
                    <th className="opt">Build Found</th>
                    <th className="opt">Reproducibility</th>
                    <th className="opt">Severity</th>
                    <th className="opt">Frequency</th>
                    <th className="opt">Keyword</th>
                    <th className="opt">Status</th>
                    <th className="opt">Resolution</th>
                    <th className="opt">Note</th>
                    <th className="opt">Suggested Fix</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBugs.map(bug => (
                    <tr key={bug.id}>
                      <td><span className="badge b-bug">{bug.id}</span></td>
                      <td className="summary-cell">{bug.summary}</td>
                      <td style={{ fontSize: 13, lineHeight: 1.5 }}>
                        {bug.steps.map((s, i) => (
                          <span key={i} style={{ display: 'block' }}>B{i + 1}: {s}</span>
                        ))}
                        {bug.expected && <><br /><strong>Expected:</strong> {bug.expected}</>}
                        {bug.observed && <><br /><strong>Observed:</strong> {bug.observed}</>}
                      </td>
                      <td><span className="badge b-priority">{bug.priority}</span></td>
                      <td><span className="badge b-feature">{bug.feature}</span></td>
                      <td className="opt">{bug.build}</td>
                      <td className="opt">{bug.reproducibility}</td>
                      <td className="opt">{bug.severity}</td>
                      <td className="opt">{bug.frequency}</td>
                      <td className="opt" style={{ maxWidth: 200 }}>{bug.keyword}</td>
                      <td className="opt">
                        <span className={`badge ${bug.status === 'Fixed' ? 'b-fixed' : 'b-new'}`}>{bug.status}</span>
                      </td>
                      <td className="opt">
                        <select
                          className="res-sel"
                          value={bug.resolution || 'n/a'}
                          onChange={e => patchBug(bug.id, { resolution: e.target.value })}
                        >
                          {RESOLUTION_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                      </td>
                      <td className="opt">
                        <textarea
                          className="note-ta"
                          defaultValue={bug.note || ''}
                          onBlur={e => patchBug(bug.id, { note: e.target.value })}
                        />
                      </td>
                      <td className="opt" style={{ maxWidth: 220, fontSize: 12 }}>{bug.suggestedFix}</td>
                      <td>
                        <button className="btn btn-primary" onClick={() => setActiveTicket(bug)}>View</button>
                      </td>
                    </tr>
                  ))}
                  {filteredBugs.length === 0 && (
                    <tr><td colSpan={15} style={{ textAlign: 'center', padding: 32, color: '#5f6b7a' }}>No bugs match the current filters.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </main>

      {/* ── Bug Detail Modal ── */}
      {activeTicket && (
        <div
          className="modal-bg"
          ref={modalBgRef}
          onClick={e => { if (e.target === modalBgRef.current) setActiveTicket(null); }}
        >
          <div className="modal" role="dialog" aria-modal="true">
            <div className="modal-hdr">
              <div>
                <h2 className="modal-hdr h2">{activeTicket.id} — {activeTicket.feature}</h2>
                <div className="modal-sub">
                  Priority: {activeTicket.priority} &nbsp;·&nbsp; Status: {activeTicket.status} &nbsp;·&nbsp; Created: {activeTicket.createdAt}
                </div>
              </div>
              <div className="modal-actions">
                <button className="btn" onClick={() => setActiveTicket(null)}>Close</button>
              </div>
            </div>
            <div className="modal-body">
              <div className="tgrid">
                <div className="tf summary-main">
                  <span className="tlabel">Summary</span>
                  <div className="tval" style={{ fontWeight: 700 }}>{activeTicket.summary}</div>
                </div>
                <div className="tf">
                  <span className="tlabel">Bug ID</span>
                  <div className="tval"><span className="badge b-bug">{activeTicket.id}</span></div>
                </div>
                <div className="tf">
                  <span className="tlabel">Priority</span>
                  <div className="tval"><span className="badge b-priority">{activeTicket.priority}</span></div>
                </div>
                <div className="tf">
                  <span className="tlabel">Feature</span>
                  <div className="tval"><span className="badge b-feature">{activeTicket.feature}</span></div>
                </div>
                <div className="tf">
                  <span className="tlabel">Status</span>
                  <div className="tval">
                    <span className={`badge ${activeTicket.status === 'Fixed' ? 'b-fixed' : 'b-new'}`}>{activeTicket.status}</span>
                  </div>
                </div>
                <div className="tf wide">
                  <span className="tlabel">Keyword</span>
                  <div className="tval">{activeTicket.keyword}</div>
                </div>
                <div className="tf full">
                  <span className="tlabel">Steps to Reproduce</span>
                  <ul className="steps">
                    {activeTicket.steps.map((s, i) => (
                      <li key={i}><span className="step-code">B{i + 1}:</span>{s}</li>
                    ))}
                  </ul>
                </div>
                <div className="tf wide f-exp">
                  <span className="tlabel">Expected Result</span>
                  <div className="tval">{activeTicket.expected}</div>
                </div>
                <div className="tf wide f-obs">
                  <span className="tlabel">Observed Result</span>
                  <div className="tval">{activeTicket.observed}</div>
                </div>
                <div className="tf">
                  <span className="tlabel">Build Found</span>
                  <div className="tval">{activeTicket.build}</div>
                </div>
                <div className="tf">
                  <span className="tlabel">Reproducibility</span>
                  <div className="tval">{activeTicket.reproducibility}</div>
                </div>
                <div className="tf">
                  <span className="tlabel">Frequency</span>
                  <div className="tval">{activeTicket.frequency}</div>
                </div>
                <div className="tf">
                  <span className="tlabel">Severity</span>
                  <div className="tval">{activeTicket.severity}</div>
                </div>
                <div className="tf full">
                  <span className="tlabel">Resolution</span>
                  <div className="tval">
                    <select
                      className="res-sel"
                      value={activeTicket.resolution || 'n/a'}
                      onChange={e => {
                        patchBug(activeTicket.id, { resolution: e.target.value });
                        setActiveTicket(t => t ? { ...t, resolution: e.target.value } : t);
                      }}
                    >
                      {RESOLUTION_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                </div>
                <div className="tf full">
                  <span className="tlabel">Note</span>
                  <div className="tval">
                    <textarea
                      className="note-ta"
                      style={{ minHeight: 80 }}
                      defaultValue={activeTicket.note || ''}
                      onBlur={e => {
                        patchBug(activeTicket.id, { note: e.target.value });
                        setActiveTicket(t => t ? { ...t, note: e.target.value } : t);
                      }}
                    />
                  </div>
                </div>
                <div className="tf full">
                  <span className="tlabel">Suggested Fix</span>
                  <div className="tval">{activeTicket.suggestedFix}</div>
                </div>
              </div>

              {/* Evidence */}
              {activeTicket.evidence?.length > 0 && (
                <div className="ev-section">
                  <h3>Step Evidence</h3>
                  <div className="ev-grid">
                    {activeTicket.evidence.map((ev, i) => (
                      <div key={i} className="ev-card" onClick={() => openViewer(activeTicket, i)}>
                        <div className="ev-cap">{ev.title}</div>
                        <div className="ev-img">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={ev.src} alt={ev.title} loading="lazy" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Evidence Viewer ── */}
      {viewerBug && (
        <div className="viewer-bg" onClick={() => setViewerBug(null)}>
          <div className="viewer-panel" onClick={e => e.stopPropagation()}>
            <div className="viewer-hdr">
              <h2>{viewerBug.evidence[viewerIdx]?.title}</h2>
              <div className="modal-actions">
                <button className="btn" onClick={() => setViewerIdx(i => Math.max(0, i - 1))} disabled={viewerIdx === 0}>&lt;</button>
                <button className="btn" onClick={() => setViewerIdx(i => Math.min((viewerBug.evidence.length || 1) - 1, i + 1))} disabled={viewerIdx >= (viewerBug.evidence.length || 1) - 1}>&gt;</button>
                <button className="btn" onClick={() => setZoom(z => Math.max(0.5, +(z - 0.25).toFixed(2)))}>Zoom -</button>
                <button className="btn" onClick={() => setZoom(1)}>Reset</button>
                <button className="btn" onClick={() => setZoom(z => Math.min(2.5, +(z + 0.25).toFixed(2)))}>Zoom +</button>
                <button className="btn" onClick={() => setViewerBug(null)}>Close</button>
              </div>
            </div>
            <div className="viewer-body">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={viewerBug.evidence[viewerIdx]?.src}
                alt={viewerBug.evidence[viewerIdx]?.title}
                style={{ transform: `scale(${zoom})` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
