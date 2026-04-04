import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Wrench, RefreshCw, Terminal, RotateCcw, Shield, Server,
  Clock, CheckCircle2, AlertTriangle, Loader2, Copy, Check,
  ChevronRight, FileCode2, Layers
} from 'lucide-react';
import { useAuth } from '../store/AuthContext';

// ── Helpers ─────────────────────────────────────────────────────────────────

const OS_META = {
  windows: { label: 'Windows',  color: '#3B6FE3', ext: '.ps1', icon: '🪟' },
  linux:   { label: 'Linux',    color: '#88C057', ext: '.sh',  icon: '🐧' },
};
const osMeta = (os) => OS_META[os?.toLowerCase()] || OS_META.linux;

const STATUS_META = {
  PENDING_APPROVAL: { color: '#E5A862', bg: 'rgba(229,168,98,0.1)',  label: 'PENDING APPROVAL' },
  APPROVED:         { color: '#88C057', bg: 'rgba(136,192,87,0.1)',  label: 'APPROVED'         },
  APPLIED:          { color: '#3B6FE3', bg: 'rgba(59,111,227,0.1)',  label: 'APPLIED'          },
  ROLLED_BACK:      { color: '#D84C7F', bg: 'rgba(216,76,127,0.1)', label: 'ROLLED BACK'      },
};
const statusMeta = (s) => STATUS_META[s] || STATUS_META.PENDING_APPROVAL;

const relTime = (iso) => {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
};

// ── Syntax highlighter (basic comment/keyword coloring) ──────────────────────
function highlight(code, ext) {
  if (!code) return '';
  const lines = code.split('\n');
  return lines.map((line, i) => {
    let color = '#CBD5E1';
    const trimmed = line.trimStart();
    if (trimmed.startsWith('#')) {
      color = '#4B5563';
    } else if (ext === '.ps1') {
      if (/^\s*(Write-Host|Set-|Get-|Disable-|Enable-|if|exit)/i.test(line)) color = '#93C5FD';
      if (/\$[A-Za-z_]/.test(line)) color = '#FCD34D';
    } else {
      if (/^\s*(echo|dnf|apt|sed|grep|systemctl|id|usermod|exportfs|passwd)/i.test(line)) color = '#93C5FD';
      if (/^\s*(set |if |fi|done|do|then|else)/i.test(line)) color = '#C4B5FD';
    }
    return (
      <div key={i} className="flex gap-3">
        <span className="select-none w-8 text-right flex-shrink-0" style={{ color: '#374151' }}>
          {i + 1}
        </span>
        <span style={{ color }}>{line || ' '}</span>
      </div>
    );
  });
}

// ── Script pane ──────────────────────────────────────────────────────────────
function ScriptPane({ title, content, ext, icon: Icon, accentColor }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="flex flex-col h-full min-h-0 rounded-lg overflow-hidden"
         style={{ border: `1px solid ${accentColor}33`, background: '#080c12' }}>
      {/* Pane header */}
      <div className="flex items-center justify-between px-4 py-2 flex-shrink-0 border-b"
           style={{ borderColor: `${accentColor}22`, background: '#0d1117' }}>
        <div className="flex items-center gap-2">
          <Icon size={12} style={{ color: accentColor }} />
          <span className="text-xs terminal font-bold" style={{ color: accentColor }}>{title}</span>
          <span className="text-[10px] terminal" style={{ color: '#4B5563' }}>{ext}</span>
        </div>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-[10px] terminal px-2 py-1 rounded hover:bg-white/5 transition-all"
          style={{ color: copied ? '#88C057' : '#4B5563' }}>
          {copied ? <Check size={10} /> : <Copy size={10} />}
          {copied ? 'COPIED' : 'COPY'}
        </button>
      </div>
      {/* Code body */}
      <div className="flex-1 overflow-auto p-4">
        <pre className="text-[11px] leading-6" style={{ fontFamily: 'JetBrains Mono, Consolas, monospace' }}>
          {content ? highlight(content, ext) : (
            <span style={{ color: '#374151' }}>No script content available.</span>
          )}
        </pre>
      </div>
    </div>
  );
}

// ── Draft list item ──────────────────────────────────────────────────────────
function DraftRow({ draft, selected, onSelect }) {
  const os  = osMeta(draft.target_os);
  const st  = statusMeta(draft.status);

  return (
    <button
      onClick={() => onSelect(draft)}
      className="w-full text-left px-4 py-3 border-b transition-all hover:bg-white/[0.02] flex flex-col gap-1"
      style={{
        borderColor: '#1F2937',
        background: selected ? `${os.color}0A` : 'transparent',
        borderLeft: selected ? `2px solid ${os.color}` : '2px solid transparent',
      }}>
      {/* Row 1: OS pill + title */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] terminal px-1.5 py-0.5 rounded flex-shrink-0"
          style={{ background: `${os.color}18`, color: os.color, border: `1px solid ${os.color}33` }}>
          {os.icon} {os.label}
        </span>
        <span className="text-xs font-semibold truncate" style={{ color: selected ? '#E2E8F0' : '#9CA3AF' }}>
          {draft.title}
        </span>
      </div>
      {/* Row 2: metadata */}
      <div className="flex items-center gap-3">
        <span className="text-[10px] terminal" style={{ color: '#4B5563' }}>{draft.patch_id}</span>
        {draft.nist_control && (
          <span className="text-[10px] terminal font-bold" style={{ color: '#E5A86299' }}>
            NIST {draft.nist_control}
          </span>
        )}
        <span className="ml-auto text-[10px] terminal" style={{ color: '#374151' }}>
          {relTime(draft.created_at)}
        </span>
      </div>
      {/* Row 3: status + host */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] terminal px-1.5 py-0.5 rounded"
          style={{ background: st.bg, color: st.color, border: `1px solid ${st.color}33` }}>
          {st.label}
        </span>
        {draft.target_host && draft.target_host !== 'unknown' && (
          <span className="text-[10px] terminal flex items-center gap-1" style={{ color: '#4B5563' }}>
            <Server size={9} /> {draft.target_host}
          </span>
        )}
      </div>
    </button>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────
function EmptyState({ onRefresh }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4">
      <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
           style={{ background: '#111827', border: '1px solid #1F2937' }}>
        <Wrench size={30} style={{ color: '#1F293788' }} />
      </div>
      <div className="text-center">
        <p className="h-title" style={{ color: '#6B7280' }}>No Patch Drafts</p>
        <p className="h-meta mt-1 max-w-xs" style={{ color: '#374151' }}>
          SENTINEL-PATCH-PILOT generates remediation scripts when triage alerts<br />
          match known NIST hardening gaps. No drafts pending approval yet.
        </p>
      </div>
      <button
        onClick={onRefresh}
        className="flex items-center gap-2 text-xs terminal px-4 py-2 rounded-lg hover:brightness-125 transition-all"
        style={{ background: '#88C05718', color: '#88C057', border: '1px solid #88C05744' }}>
        <RefreshCw size={12} /> Refresh Drafts
      </button>
    </div>
  );
}

// ── No selection state ────────────────────────────────────────────────────────
function NoSelection() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3">
      <FileCode2 size={32} style={{ color: '#1F2937' }} />
      <p className="text-xs terminal" style={{ color: '#374151' }}>
        Select a draft from the left to inspect its scripts
      </p>
    </div>
  );
}

// ── Mock drafts (shown when backend has no data yet) ─────────────────────────
const MOCK_DRAFTS = [
  {
    patch_id: 'RCA-DEMO-353',
    title: 'Configure PAM TOTP (Google Authenticator)',
    target_os: 'linux',
    nist_control: '3.5.3',
    finding_description: 'SSH does not enforce multi-factor authentication via PAM.',
    target_host: 'MFG-PROD-01',
    status: 'PENDING_APPROVAL',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    script_content: `#!/bin/bash
# ===========================================================================
# RCA Patch Pilot — Remediation Script (Bash)
# ===========================================================================
# Patch ID   : RCA-DEMO-353
# Title      : Configure PAM TOTP (Google Authenticator)
# NIST Control: 3.5.3
# Finding    : SSH does not enforce multi-factor authentication.
# Status     : PENDING_APPROVAL — DO NOT EXECUTE WITHOUT HUMAN APPROVAL
# ===========================================================================
set -euo pipefail

# ---- PRE-FLIGHT CHECK ----
echo "[RCA_EVENT] { \\"task\\": \\"preflight\\", \\"status\\": \\"starting\\" }"
if rpm -q google-authenticator; then echo 'already_installed'; exit 0; fi

# ---- FIX ----
echo "[RCA_EVENT] { \\"task\\": \\"fix\\", \\"status\\": \\"executing\\" }"
dnf install -y google-authenticator
systemctl restart sshd

# ---- VERIFICATION ----
echo "[RCA_EVENT] { \\"task\\": \\"verify\\", \\"status\\": \\"executing\\" }"
grep 'pam_google_authenticator' /etc/pam.d/sshd

echo "[RCA_EVENT] { \\"task\\": \\"complete\\", \\"status\\": \\"success\\" }"
echo "[RCA Patch Pilot] Remediation complete. Please verify manually."`,
    rollback_content: `#!/bin/bash
# ===========================================================================
# RCA Patch Pilot — ROLLBACK Script (Bash)
# ===========================================================================
# Patch ID   : RCA-DEMO-353
# Title      : ROLLBACK — Configure PAM TOTP
# ===========================================================================
set -euo pipefail

echo "[RCA_EVENT] { \\"task\\": \\"rollback\\", \\"status\\": \\"executing\\" }"
sed -i '/pam_google_authenticator/d' /etc/pam.d/sshd
echo "[RCA_EVENT] { \\"task\\": \\"rollback\\", \\"status\\": \\"success\\" }"`,
  },
  {
    patch_id: 'RCA-DEMO-311',
    title: 'Disable Guest Account',
    target_os: 'windows',
    nist_control: '3.1.1',
    finding_description: 'Guest account is enabled on domain workstation.',
    target_host: 'Host-DX9',
    status: 'PENDING_APPROVAL',
    created_at: new Date(Date.now() - 7200000).toISOString(),
    script_content: `# ===========================================================================
# RCA Patch Pilot — Remediation Script (PowerShell)
# ===========================================================================
# Patch ID   : RCA-DEMO-311
# Title      : Disable Guest Account
# NIST Control: 3.1.1
# Finding    : Guest account is enabled on domain workstation.
# Status     : PENDING_APPROVAL — DO NOT EXECUTE WITHOUT HUMAN APPROVAL
# ===========================================================================

# ---- PRE-FLIGHT CHECK ----
Write-Host "[RCA_EVENT] { 'task': 'preflight', 'status': 'starting' }"
if ((Get-LocalUser -Name 'Guest').Enabled -eq $false) {
  Write-Host "[RCA_EVENT] { 'task': 'preflight', 'status': 'skipped', 'reason': 'already_disabled' }"
  exit 0
}

# ---- FIX ----
Write-Host "[RCA_EVENT] { 'task': 'fix', 'status': 'executing' }"
Disable-LocalUser -Name 'Guest'

# ---- VERIFICATION ----
Write-Host "[RCA_EVENT] { 'task': 'verify', 'status': 'executing' }"
Get-LocalUser -Name 'Guest' | Select-Object Name, Enabled

Write-Host "[RCA_EVENT] { 'task': 'complete', 'status': 'success' }"
Write-Host "[RCA Patch Pilot] Remediation complete. Please verify manually."`,
    rollback_content: `# ===========================================================================
# RCA Patch Pilot — ROLLBACK Script (PowerShell)
# ===========================================================================
# Patch ID   : RCA-DEMO-311
# Title      : ROLLBACK — Disable Guest Account
# ===========================================================================

Write-Host "[RCA Patch Pilot] Rolling back: Disable Guest Account"
Enable-LocalUser -Name 'Guest'
Write-Host "[RCA Patch Pilot] Rollback complete."`,
  },
];

// ── Main View ─────────────────────────────────────────────────────────────────
export default function PatchPilotView() {
  const { authenticatedFetch } = useAuth();

  const [drafts, setDrafts]       = useState([]);
  const [loading, setLoading]     = useState(true);
  const [isMock, setIsMock]       = useState(false);
  const [selected, setSelected]   = useState(null);
  const [activeScript, setActiveScript] = useState('fix'); // 'fix' | 'rollback'
  const [osFilter, setOsFilter]   = useState('ALL');

  const fetchDrafts = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authenticatedFetch('http://localhost:8000/api/v1/patch/drafts');
      if (res.ok) {
        const data = await res.json();
        if (data.length > 0) {
          setDrafts(data);
          setIsMock(false);
          setSelected(s => s ? data.find(d => d.patch_id === s.patch_id) || data[0] : data[0]);
        } else {
          throw new Error('empty');
        }
      } else {
        throw new Error('fetch failed');
      }
    } catch {
      setDrafts(MOCK_DRAFTS);
      setIsMock(true);
      setSelected(MOCK_DRAFTS[0]);
    } finally {
      setLoading(false);
    }
  }, [authenticatedFetch]);

  useEffect(() => { fetchDrafts(); }, [fetchDrafts]);

  const filtered = useMemo(() =>
    osFilter === 'ALL' ? drafts : drafts.filter(d => d.target_os === osFilter),
    [drafts, osFilter]
  );

  const pending  = drafts.filter(d => d.status === 'PENDING_APPROVAL').length;
  const winCount = drafts.filter(d => d.target_os === 'windows').length;
  const linCount = drafts.filter(d => d.target_os === 'linux').length;

  const selOs = selected ? osMeta(selected.target_os) : null;
  const selExt = selOs?.ext || '.sh';

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>

      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
           style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <Wrench size={14} style={{ color: '#88C057' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            PATCH PILOT — REMEDIATION WORKBENCH
          </span>
          {isMock && (
            <span className="text-[10px] terminal px-2 py-0.5 rounded-full"
                  style={{ background: '#E5A86218', color: '#E5A862', border: '1px solid #E5A86244' }}>
              DEMO DATA
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] terminal" style={{ color: '#4B5563' }}>
            NEVER AUTO-EXECUTED · HUMAN APPROVAL REQUIRED
          </span>
          <Shield size={11} style={{ color: '#E5A862' }} />
          <button
            onClick={fetchDrafts}
            className={`p-1.5 rounded hover:bg-white/5 transition-colors ${loading ? 'animate-spin' : ''}`}>
            <RefreshCw size={13} style={{ color: loading ? '#88C057' : '#6B7280' }} />
          </button>
        </div>
      </div>

      {/* ── KPI Strip ── */}
      <div className="grid grid-cols-4 border-b flex-shrink-0"
           style={{ borderColor: '#1F2937', background: '#080c12' }}>
        {[
          { label: 'TOTAL DRAFTS',    value: drafts.length, color: '#E2E8F0', icon: Layers   },
          { label: 'PENDING APPROVAL',value: pending,       color: '#E5A862', icon: Clock     },
          { label: 'WINDOWS SCRIPTS', value: winCount,      color: '#3B6FE3', icon: Terminal  },
          { label: 'LINUX SCRIPTS',   value: linCount,      color: '#88C057', icon: Terminal  },
        ].map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="flex items-center gap-3 px-5 py-3 border-r last:border-0"
               style={{ borderColor: '#1F2937' }}>
            <Icon size={14} style={{ color, opacity: 0.7, flexShrink: 0 }} />
            <div>
              <p className="h-stat text-xl font-bold" style={{ color }}>{value}</p>
              <p className="h-meta" style={{ color: '#4B5563' }}>{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* ── Body ── */}
      {loading && drafts.length === 0 ? (
        <div className="flex-1 flex items-center justify-center gap-3">
          <Loader2 className="animate-spin" size={20} style={{ color: '#88C057' }} />
          <p className="text-xs terminal" style={{ color: '#88C057' }}>
            Fetching patch drafts from SENTINEL-PATCH-PILOT…
          </p>
        </div>
      ) : drafts.length === 0 ? (
        <div className="flex-1">
          <EmptyState onRefresh={fetchDrafts} />
        </div>
      ) : (
        <div className="flex flex-1 min-h-0">

          {/* ── LEFT: Draft list ── */}
          <div className="flex flex-col border-r flex-shrink-0"
               style={{ flex: '0 0 30%', minWidth: 260, borderColor: '#1F2937', background: '#080c12' }}>

            {/* OS filter */}
            <div className="flex items-center gap-1.5 px-3 py-2 border-b flex-shrink-0"
                 style={{ borderColor: '#1F2937' }}>
              {['ALL', 'windows', 'linux'].map(f => (
                <button key={f}
                  onClick={() => setOsFilter(f)}
                  className="text-[10px] terminal px-2.5 py-1 rounded-full transition-all capitalize"
                  style={{
                    background: osFilter === f ? (f === 'ALL' ? '#1F293788' : `${osMeta(f).color}18`) : 'transparent',
                    color: osFilter === f ? (f === 'ALL' ? '#E2E8F0' : osMeta(f).color) : '#4B5563',
                    border: `1px solid ${osFilter === f ? (f === 'ALL' ? '#374151' : osMeta(f).color + '44') : '#1F2937'}`,
                  }}>
                  {f === 'ALL' ? 'All' : osMeta(f).icon + ' ' + osMeta(f).label}
                </button>
              ))}
              <span className="ml-auto text-[10px] terminal" style={{ color: '#374151' }}>
                {filtered.length}
              </span>
            </div>

            {/* Draft rows */}
            <div className="flex-1 overflow-y-auto">
              {filtered.map(d => (
                <DraftRow
                  key={d.patch_id}
                  draft={d}
                  selected={selected?.patch_id === d.patch_id}
                  onSelect={setSelected}
                />
              ))}
            </div>
          </div>

          {/* ── RIGHT: Script inspector ── */}
          <div className="flex flex-col flex-1 min-w-0">
            {!selected ? <NoSelection /> : (
              <>
                {/* Detail header */}
                <div className="flex items-center gap-3 px-5 py-3 border-b flex-shrink-0"
                     style={{ borderColor: '#1F2937', background: '#0d1117' }}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span style={{ fontSize: 14 }}>{selOs?.icon}</span>
                      <p className="h-title text-sm font-bold truncate" style={{ color: '#E2E8F0' }}>
                        {selected.title}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                      <span className="h-meta" style={{ color: '#4B5563' }}>{selected.patch_id}</span>
                      {selected.nist_control && (
                        <span className="h-meta font-bold" style={{ color: '#E5A86299' }}>
                          NIST {selected.nist_control}
                        </span>
                      )}
                      {selected.target_host && selected.target_host !== 'unknown' && (
                        <span className="h-meta flex items-center gap-1" style={{ color: '#4B5563' }}>
                          <Server size={9} /> {selected.target_host}
                        </span>
                      )}
                    </div>
                  </div>
                  {/* Script tab toggle */}
                  <div className="flex rounded-lg overflow-hidden border" style={{ borderColor: '#1F2937' }}>
                    <button
                      onClick={() => setActiveScript('fix')}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] terminal transition-colors"
                      style={{
                        background: activeScript === 'fix' ? '#88C05718' : 'transparent',
                        color: activeScript === 'fix' ? '#88C057' : '#4B5563',
                      }}>
                      <Terminal size={10} /> FIX
                    </button>
                    <button
                      onClick={() => setActiveScript('rollback')}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] terminal transition-colors border-l"
                      style={{
                        borderColor: '#1F2937',
                        background: activeScript === 'rollback' ? '#D84C7F18' : 'transparent',
                        color: activeScript === 'rollback' ? '#D84C7F' : '#4B5563',
                      }}>
                      <RotateCcw size={10} /> ROLLBACK
                    </button>
                  </div>
                </div>

                {/* Finding banner */}
                {selected.finding_description && (
                  <div className="px-5 py-2 border-b flex items-start gap-2 flex-shrink-0"
                       style={{ borderColor: '#1F2937', background: '#E5A86209' }}>
                    <AlertTriangle size={11} style={{ color: '#E5A862', flexShrink: 0, marginTop: 1 }} />
                    <p className="text-[11px] terminal" style={{ color: '#9CA3AF' }}>
                      <span style={{ color: '#E5A862' }}>FINDING: </span>
                      {selected.finding_description}
                    </p>
                  </div>
                )}

                {/* Script content */}
                <div className="flex-1 min-h-0 p-4">
                  <ScriptPane
                    title={activeScript === 'fix' ? 'Remediation Script' : 'Rollback Script'}
                    content={activeScript === 'fix' ? selected.script_content : selected.rollback_content}
                    ext={selExt}
                    icon={activeScript === 'fix' ? Terminal : RotateCcw}
                    accentColor={activeScript === 'fix' ? selOs?.color : '#D84C7F'}
                  />
                </div>

                {/* PENDING_APPROVAL warning bar */}
                {selected.status === 'PENDING_APPROVAL' && (
                  <div className="flex items-center gap-3 px-5 py-3 border-t flex-shrink-0"
                       style={{ borderColor: '#E5A86233', background: '#E5A86209' }}>
                    <Shield size={13} style={{ color: '#E5A862' }} />
                    <p className="text-xs terminal" style={{ color: '#E5A862' }}>
                      PENDING APPROVAL — This script must not be executed until reviewed and approved by a qualified analyst.
                    </p>
                    <CheckCircle2 size={13} style={{ color: '#E5A86266' }} />
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
