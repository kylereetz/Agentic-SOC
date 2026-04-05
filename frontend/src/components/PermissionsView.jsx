import React, { useState, useEffect, useCallback } from 'react';
import {
  Lock, Shield, User, Users, CheckCircle, XCircle, Eye,
  AlertTriangle, Key, Clock, RefreshCw, ChevronRight, BookOpen,
} from 'lucide-react';
import { useAuth } from '../store/AuthContext';

// ── RBAC Capability Matrix ────────────────────────────────────────────────────
const CAPABILITIES = [
  { action: 'View Alert Queue',          endpoint: 'GET /alerts',              admin: true,  analyst: true,  auditor: true  },
  { action: 'View Asset Inventory',      endpoint: 'GET /inventory',           admin: true,  analyst: true,  auditor: true  },
  { action: 'View Investigations',       endpoint: 'GET /cases',               admin: true,  analyst: true,  auditor: true  },
  { action: 'View Compliance Posture',   endpoint: 'GET /status',              admin: true,  analyst: true,  auditor: true  },
  { action: 'View Pending Actions',      endpoint: 'GET /pending',             admin: true,  analyst: true,  auditor: false },
  { action: 'Approve/Reject HITL Gate',  endpoint: 'POST /approve/{id}',       admin: true,  analyst: false, auditor: false },
  { action: 'Launch Network Audit',      endpoint: 'POST (local run)',         admin: true,  analyst: false, auditor: false },
  { action: 'Admin Kill Switch',         endpoint: 'UI only',                  admin: true,  analyst: false, auditor: false },
  { action: 'View User Roster',          endpoint: 'GET /api/v1/users',        admin: true,  analyst: false, auditor: false },
  { action: 'Agent Deep Telemetry',      endpoint: 'GET /api/agents/{id}/...', admin: true,  analyst: true,  auditor: false },
  { action: 'Network Topology Graph',    endpoint: 'GET /api/v1/topology',     admin: true,  analyst: true,  auditor: true  },
  { action: 'ChitChat / AI Copilot',     endpoint: 'POST /api/v1/chitchat',    admin: true,  analyst: true,  auditor: true  },
  { action: 'Launch Adversary Sim',      endpoint: 'UI + local run',           admin: true,  analyst: false, auditor: false },
  { action: 'Export Reports / Board Pkg',endpoint: 'UI only',                  admin: true,  analyst: true,  auditor: true  },
];

// ── CMMC AC Control Family mapping ───────────────────────────────────────────
const CMMC_CONTROLS = [
  { id: 'AC.1.001', desc: 'Limit system access to authorized users',         role: 'admin',   status: 'pass' },
  { id: 'AC.1.002', desc: 'Limit system access to types of transactions',    role: 'admin',   status: 'pass' },
  { id: 'AC.2.006', desc: 'Protect CUI on systems with multi-user auth',     role: 'all',     status: 'pass' },
  { id: 'AC.3.017', desc: 'Separate duties of individuals',                  role: 'analyst', status: 'pass' },
  { id: 'AC.3.018', desc: 'Prevent non-privileged users from executing priv ops', role: 'admin', status: 'pass' },
  { id: 'AC.3.019', desc: 'Terminate sessions after defined conditions',     role: 'all',     status: 'warn' },
  { id: 'IA.1.076', desc: 'Authenticate identities of users before access',  role: 'all',     status: 'pass' },
  { id: 'IA.2.078', desc: 'Enforce min password complexity and change',      role: 'admin',   status: 'warn' },
  { id: 'IA.3.083', desc: 'Use multifactor authentication for accounts',     role: 'all',     status: 'warn' },
];

const ROLE_STYLES = {
  admin:   { color: '#D84C7F', bg: '#D84C7F18', border: '#D84C7F33', label: 'ADMIN'   },
  analyst: { color: '#3B6FE3', bg: '#3B6FE318', border: '#3B6FE333', label: 'ANALYST' },
  auditor: { color: '#E5A862', bg: '#E5A86218', border: '#E5A86233', label: 'AUDITOR' },
};

const STATUS_STYLES = {
  pass: { icon: CheckCircle, color: '#88C057', label: 'PASS' },
  warn: { icon: AlertTriangle, color: '#E5A862', label: 'WARN' },
  fail: { icon: XCircle,     color: '#EF4444', label: 'FAIL' },
};

// ── Sub-Components ────────────────────────────────────────────────────────────

function RoleBadge({ role }) {
  const s = ROLE_STYLES[role] || { color: '#6B7280', bg: '#6B728018', border: '#6B728033', label: role?.toUpperCase() };
  return (
    <span
      className="inline-flex items-center gap-1 text-xs font-bold terminal px-2 py-0.5 rounded"
      style={{ background: s.bg, border: `1px solid ${s.border}`, color: s.color }}>
      {s.label}
    </span>
  );
}

function CapabilityCell({ allowed }) {
  return allowed
    ? <CheckCircle size={13} style={{ color: '#88C057', margin: 'auto' }} />
    : <XCircle    size={13} style={{ color: '#1F2937',  margin: 'auto' }} />;
}

function UserCard({ userData, isSelf }) {
  const s = ROLE_STYLES[userData.role] || ROLE_STYLES.auditor;
  return (
    <div
      className="rounded-lg p-4 flex items-center gap-4 transition-all hover:brightness-110"
      style={{
        background: '#111827',
        border: `1px solid ${isSelf ? s.border : '#1F2937'}`,
        boxShadow: isSelf ? `0 0 12px ${s.color}18` : 'none',
      }}>
      {/* Avatar */}
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
        style={{ background: `${s.color}22`, border: `1px solid ${s.border}`, color: s.color }}>
        {userData.username.substring(0, 2).toUpperCase()}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-bold" style={{ color: '#E2E8F0' }}>{userData.username}</span>
          {isSelf && (
            <span className="text-[10px] terminal px-1.5 py-0.5 rounded"
              style={{ background: '#88C05718', color: '#88C057', border: '1px solid #88C05733' }}>
              YOU
            </span>
          )}
        </div>
        <RoleBadge role={userData.role} />
      </div>

      {/* Auth indicator */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <span className="w-1.5 h-1.5 rounded-full animate-blink" style={{ background: '#88C057' }} />
        <span className="text-xs terminal" style={{ color: '#4B5563' }}>JWT AUTH</span>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function PermissionsView() {
  const { user, authenticatedFetch } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [activeTab, setActiveTab] = useState('users');

  const fetchUsers = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError(null);
    try {
      const res = await authenticatedFetch('http://localhost:8000/api/v1/users');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setUsers(data);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [isAdmin, authenticatedFetch]);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  // For non-admin: synthesize single-user view from JWT claims
  const displayUsers = isAdmin ? users : (user ? [{ username: user.username, role: user.role }] : []);

  const tokenExpiry = (() => {
    try {
      const token = localStorage.getItem('soc_token');
      if (!token) return null;
      const payload = JSON.parse(atob(token.split('.')[1]));
      return new Date(payload.exp * 1000);
    } catch { return null; }
  })();

  return (
    <div className="flex flex-col h-full" style={{ background: '#0B1117' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="flex items-center gap-3">
          <Lock size={14} style={{ color: '#E5A862' }} />
          <span className="text-xs font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
            PERMISSIONS & IDENTITY
          </span>
          <span className="text-xs terminal ml-1" style={{ color: '#6B7280' }}>
            QUILL-GATEKEEPER · AC / IA NIST 800-171
          </span>
        </div>

        <div className="flex items-center gap-3">
          {isAdmin && (
            <button
              onClick={fetchUsers}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs terminal px-3 py-1.5 rounded transition-all hover:brightness-125 action-btn"
              style={{ background: '#111827', color: '#6B7280', border: '1px solid #1F2937' }}>
              <RefreshCw size={11} className={loading ? 'animate-spin-slow' : ''} />
              REFRESH
            </button>
          )}
          <div className="flex items-center gap-1.5 px-2 py-1 rounded"
            style={{ background: '#E5A86210', border: '1px solid #E5A86230' }}>
            <Key size={11} style={{ color: '#E5A862' }} />
            <span className="text-[10px] terminal" style={{ color: '#E5A862' }}>HS256 · 8h SESSION</span>
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex border-b flex-shrink-0" style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        {[
          { id: 'users',    label: '👤 User Roster' },
          { id: 'rbac',     label: '⚔️  RBAC Matrix' },
          { id: 'cmmc',     label: '📋 CMMC AC Controls' },
          { id: 'session',  label: '🔑 My Session' },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className="text-xs terminal px-4 py-3 transition-all"
            style={{
              color: activeTab === tab.id ? '#E2E8F0' : '#6B7280',
              borderBottom: activeTab === tab.id ? '2px solid #E5A862' : '2px solid transparent',
            }}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">

        {/* ── USER ROSTER TAB ── */}
        {activeTab === 'users' && (
          <div className="p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Users size={12} style={{ color: '#6B7280' }} />
                <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>
                  {isAdmin ? `OPERATOR ROSTER — ${displayUsers.length} ACCOUNTS` : 'YOUR PROFILE'}
                </span>
              </div>
              {lastRefresh && (
                <span className="text-xs terminal" style={{ color: '#4B5563' }}>
                  <Clock size={9} className="inline mr-1" />
                  Refreshed {lastRefresh.toLocaleTimeString()}
                </span>
              )}
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 mb-4 rounded-lg text-xs"
                style={{ background: '#EF444411', border: '1px solid #EF444433', color: '#EF4444' }}>
                <AlertTriangle size={13} />
                Failed to load users: {error}
              </div>
            )}

            {!isAdmin && (
              <div className="flex items-center gap-2 p-3 mb-4 rounded-lg text-xs"
                style={{ background: '#3B6FE311', border: '1px solid #3B6FE333', color: '#3B6FE3' }}>
                <Eye size={13} />
                You are viewing your own profile. Admin access required to view all operators.
              </div>
            )}

            <div className="space-y-2">
              {displayUsers.map(u => (
                <UserCard key={u.username} userData={u} isSelf={u.username === user?.username} />
              ))}
              {displayUsers.length === 0 && !loading && (
                <div className="flex flex-col items-center justify-center py-16 gap-3">
                  <Users size={32} style={{ color: '#1F2937' }} />
                  <p className="text-xs terminal" style={{ color: '#374151' }}>No users loaded.</p>
                </div>
              )}
            </div>

            {/* Role legend */}
            <div className="mt-8 rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
              <p className="text-xs terminal mb-3" style={{ color: '#4B5563' }}>ROLE DEFINITIONS</p>
              <div className="space-y-3">
                {Object.entries(ROLE_STYLES).map(([role, s]) => (
                  <div key={role} className="flex items-start gap-3">
                    <RoleBadge role={role} />
                    <p className="text-xs" style={{ color: '#9CA3AF', lineHeight: 1.6 }}>
                      {role === 'admin' && 'Full system control — can approve containment actions, manage system autonomy, and view all operators. Maps to CMMC AC.3.018 (privileged operations).'}
                      {role === 'analyst' && 'Operational responder — can view and work pending actions but cannot approve enforcement. Maps to CMMC AC.3.017 (separation of duties).'}
                      {role === 'auditor' && 'Read-only compliance observer — case and alert visibility only, no write access. Maps to CMMC AC.1.002 (restricted transaction types).'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── RBAC MATRIX TAB ── */}
        {activeTab === 'rbac' && (
          <div className="p-5">
            <p className="text-xs terminal mb-4" style={{ color: '#4B5563' }}>
              CAPABILITY MATRIX — WHO CAN DO WHAT
            </p>

            {/* Column headers */}
            <div className="grid text-xs terminal mb-1 px-3"
              style={{ gridTemplateColumns: '1fr 220px 80px 80px 80px', color: '#374151' }}>
              <span>ACTION</span>
              <span>API / SURFACE</span>
              <span className="text-center" style={{ color: ROLE_STYLES.admin.color }}>ADMIN</span>
              <span className="text-center" style={{ color: ROLE_STYLES.analyst.color }}>ANALYST</span>
              <span className="text-center" style={{ color: ROLE_STYLES.auditor.color }}>AUDITOR</span>
            </div>

            <div className="rounded-lg overflow-hidden" style={{ border: '1px solid #1F2937' }}>
              {CAPABILITIES.map((cap, i) => (
                <div
                  key={i}
                  className="grid items-center px-3 py-2.5 border-b transition-all hover:bg-white/5"
                  style={{
                    gridTemplateColumns: '1fr 220px 80px 80px 80px',
                    borderColor: '#1F2937',
                    background: i % 2 === 0 ? '#0d1117' : '#111827',
                  }}>
                  <span className="text-xs" style={{ color: '#CBD5E1' }}>{cap.action}</span>
                  <span className="text-xs terminal truncate" style={{ color: '#4B5563' }}>{cap.endpoint}</span>
                  <CapabilityCell allowed={cap.admin} />
                  <CapabilityCell allowed={cap.analyst} />
                  <CapabilityCell allowed={cap.auditor} />
                </div>
              ))}
            </div>

            {/* Current role highlight */}
            <div className="mt-4 flex items-center gap-2 p-3 rounded-lg"
              style={{ background: `${(ROLE_STYLES[user?.role] || ROLE_STYLES.auditor).color}0d`, border: `1px solid ${(ROLE_STYLES[user?.role] || ROLE_STYLES.auditor).border}` }}>
              <Shield size={13} style={{ color: (ROLE_STYLES[user?.role] || ROLE_STYLES.auditor).color }} />
              <span className="text-xs terminal" style={{ color: '#9CA3AF' }}>
                You are authenticated as{' '}
                <span style={{ color: (ROLE_STYLES[user?.role] || ROLE_STYLES.auditor).color }}>
                  {user?.username}
                </span>
                {' '}with role{' '}
                <span style={{ color: (ROLE_STYLES[user?.role] || ROLE_STYLES.auditor).color }}>
                  {user?.role?.toUpperCase()}
                </span>
                . Rows with <XCircle size={10} className="inline" style={{ color: '#1F2937' }} /> are inaccessible to your account.
              </span>
            </div>
          </div>
        )}

        {/* ── CMMC AC CONTROLS TAB ── */}
        {activeTab === 'cmmc' && (
          <div className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen size={12} style={{ color: '#A78BFA' }} />
              <span className="text-xs terminal font-bold" style={{ color: '#6B7280' }}>
                CMMC 2.0 LEVEL 3 — ACCESS CONTROL & IDENTIFICATION/AUTH CONTROLS
              </span>
            </div>
            <p className="text-xs mb-5" style={{ color: '#4B5563', lineHeight: 1.7 }}>
              The following NIST 800-171 / CMMC controls are satisfied or partially satisfied by the
              QUILL-GATEKEEPER agent, this RBAC system, and the JWT authentication layer.
              Warnings indicate controls that require additional configuration outside this dashboard.
            </p>

            <div className="rounded-lg overflow-hidden" style={{ border: '1px solid #1F2937' }}>
              {/* Header */}
              <div className="grid text-xs terminal px-4 py-2 border-b"
                style={{ gridTemplateColumns: '100px 1fr 80px 80px', borderColor: '#1F2937', color: '#374151', background: '#0d1117' }}>
                <span>CONTROL</span>
                <span>DESCRIPTION</span>
                <span>APPLIES TO</span>
                <span>STATUS</span>
              </div>
              {CMMC_CONTROLS.map((ctrl, i) => {
                const st = STATUS_STYLES[ctrl.status];
                const Icon = st.icon;
                return (
                  <div key={ctrl.id}
                    className="grid items-center px-4 py-3 border-b hover:bg-white/5 transition-all"
                    style={{
                      gridTemplateColumns: '100px 1fr 80px 80px',
                      borderColor: '#1F2937',
                      background: i % 2 === 0 ? '#111827' : '#0d1117',
                    }}>
                    <span className="text-xs terminal font-bold" style={{ color: '#A78BFA' }}>{ctrl.id}</span>
                    <span className="text-xs pr-4" style={{ color: '#9CA3AF', lineHeight: 1.5 }}>{ctrl.desc}</span>
                    <span>
                      {ctrl.role === 'all'
                        ? <span className="text-xs terminal" style={{ color: '#6B7280' }}>ALL</span>
                        : <RoleBadge role={ctrl.role} />}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <Icon size={13} style={{ color: st.color, flexShrink: 0 }} />
                      <span className="text-xs terminal font-bold" style={{ color: st.color }}>{st.label}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
              <p className="text-xs terminal font-bold mb-2" style={{ color: '#E5A862' }}>⚠ WARNINGS REQUIRE ATTENTION</p>
              <ul className="space-y-1.5 text-xs" style={{ color: '#9CA3AF', lineHeight: 1.6 }}>
                <li><ChevronRight size={10} className="inline mr-1" style={{ color: '#E5A862' }} />
                  <strong style={{ color: '#E2E8F0' }}>AC.3.019 (Session Termination):</strong>{' '}
                  JWT tokens expire after 8h. For CMMC compliance, consider reducing the token TTL
                  or adding idle-session detection in the frontend.
                </li>
                <li><ChevronRight size={10} className="inline mr-1" style={{ color: '#E5A862' }} />
                  <strong style={{ color: '#E2E8F0' }}>IA.2.078 (Password Complexity):</strong>{' '}
                  Current credentials in <code style={{ color: '#D84C7F' }}>_RAW_USERS</code> use
                  default weak passwords. Migrate to Vault-loaded credentials or an external IdP
                  before any CMMC assessment.
                </li>
                <li><ChevronRight size={10} className="inline mr-1" style={{ color: '#E5A862' }} />
                  <strong style={{ color: '#E2E8F0' }}>IA.3.083 (MFA):</strong>{' '}
                  The login flow is currently single-factor (username + password). CMMC Level 3
                  requires MFA for privileged accounts. TOTP integration is recommended.
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* ── SESSION TAB ── */}
        {activeTab === 'session' && (
          <div className="p-5 max-w-xl">
            <p className="text-xs terminal mb-4" style={{ color: '#4B5563' }}>CURRENT OPERATOR SESSION</p>

            <div className="space-y-3">
              {[
                { label: 'OPERATOR ALIAS',   value: user?.username || '—', color: '#E2E8F0' },
                { label: 'ASSIGNED ROLE',    value: user?.role?.toUpperCase() || '—', color: (ROLE_STYLES[user?.role] || ROLE_STYLES.auditor).color },
                { label: 'AUTH METHOD',      value: 'JWT / HS256', color: '#3B6FE3' },
                { label: 'TOKEN LIFETIME',   value: '8 hours (480 min)', color: '#9CA3AF' },
                { label: 'SESSION EXPIRES',  value: tokenExpiry ? tokenExpiry.toLocaleString() : 'Unknown', color: '#E5A862' },
                { label: 'IDENTITY BROKER',  value: 'QUILL-GATEKEEPER', color: '#D84C7F' },
                { label: 'ENCRYPTION',       value: 'TLS (local) · Vault-backed secret key', color: '#88C057' },
              ].map(({ label, value, color }) => (
                <div key={label} className="flex items-center justify-between px-4 py-3 rounded-lg"
                  style={{ background: '#111827', border: '1px solid #1F2937' }}>
                  <span className="text-xs terminal" style={{ color: '#4B5563' }}>{label}</span>
                  <span className="text-xs font-bold terminal" style={{ color }}>{value}</span>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-lg p-4 neon-border"
              style={{ background: '#D84C7F08', border: '1px solid #D84C7F33' }}>
              <p className="text-xs terminal font-bold mb-2" style={{ color: '#D84C7F' }}>QUILL-GATEKEEPER STATUS</p>
              <p className="text-xs" style={{ color: '#9CA3AF', lineHeight: 1.7 }}>
                All sessions are cryptographically signed and validated on every API request.
                QUILL-GATEKEEPER monitors for anomalous access patterns, rotates Non-Human
                Identity (NHI) credentials, and enforces least-privilege on all agent-to-agent
                communication within the Service Mesh.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <span className="w-1.5 h-1.5 rounded-full animate-blink" style={{ background: '#88C057' }} />
                <span className="text-xs terminal" style={{ color: '#88C057' }}>AGENT ONLINE · HEARTBEAT OK</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
