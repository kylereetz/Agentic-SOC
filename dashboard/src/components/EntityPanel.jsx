import React from 'react';
import { X, AlertTriangle, Server, User, Globe, Activity, Hash } from 'lucide-react';
import { useSOC, ENTITY_DB } from '../store/SOCContext';

const TYPE_ICONS   = { IP: Globe, Host: Server, User: User, Process: Activity, Domain: Globe };
const RISK_COLORS  = { Critical: '#EF4444', High: '#E5A862', Medium: '#3B6FE3', Low: '#88C057' };

function Field({ label, value, mono }) {
  return (
    <div>
      <p className="text-xs" style={{ color: '#6B7280' }}>{label}</p>
      <p className={`text-xs mt-0.5 ${mono ? 'terminal' : ''}`} style={{ color: '#CBD5E1' }}>{value || '—'}</p>
    </div>
  );
}

export default function EntityPanel() {
  const { selectedEntity, clearEntityFilter } = useSOC();
  if (!selectedEntity) return null;

  const e = selectedEntity;
  const Icon = TYPE_ICONS[e.type] || Server;
  const riskColor = RISK_COLORS[e.risk] || '#6B7280';

  return (
    <div className="flex flex-col h-full overflow-y-auto border-l"
      style={{ background: '#0B1117', borderColor: '#1F2937', minWidth: 260 }}>

      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2.5 border-b flex-shrink-0"
        style={{ borderColor: '#1F2937', background: '#0d1117' }}>
        <div className="w-7 h-7 rounded flex items-center justify-center flex-shrink-0"
          style={{ background: `${riskColor}18`, border: `1px solid ${riskColor}33` }}>
          <Icon size={13} style={{ color: riskColor }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold terminal truncate" style={{ color: riskColor }}>{e.label}</p>
          <p className="text-xs" style={{ color: '#4B5563' }}>{e.type}</p>
        </div>
        <button onClick={clearEntityFilter} className="p-1 rounded hover:bg-white/5 transition-colors">
          <X size={13} style={{ color: '#6B7280' }} />
        </button>
      </div>

      {/* Risk badge */}
      <div className="px-3 py-2 border-b" style={{ borderColor: '#1F2937' }}>
        <span className="inline-flex items-center gap-1.5 text-xs terminal px-2 py-1 rounded"
          style={{ background: `${riskColor}18`, color: riskColor, border: `1px solid ${riskColor}33` }}>
          <AlertTriangle size={10} /> {e.risk || 'Unknown'} Risk
        </span>
      </div>

      {/* Fields */}
      <div className="p-3 space-y-3 flex-1">
        {/* Type-specific fields */}
        {e.type === 'IP' && <>
          <Field label="IP Address" value={e.id} mono />
          <Field label="Owner" value={e.owner} />
          <Field label="MAC Address" value={e.mac} mono />
          <Field label="VLAN" value={e.vlan} />
          <Field label="First Seen" value={e.firstSeen} mono />
        </>}
        {e.type === 'Host' && <>
          <Field label="Hostname" value={e.id} />
          <Field label="OS" value={e.os} />
          <Field label="IP" value={e.ip} mono />
          <Field label="Domain" value={e.domain} />
          <Field label="Owner" value={e.owner} />
          <Field label="Status" value={e.status} />
        </>}
        {e.type === 'User' && <>
          <Field label="Username" value={e.id} mono />
          <Field label="Department" value={e.department} />
          <Field label="Last Logon" value={e.lastLogon} mono />
          <Field label="Risk Score" value={e.riskScore ? `${e.riskScore}/100` : null} />
          {e.groups?.length > 0 && (
            <div>
              <p className="text-xs mb-1" style={{ color: '#6B7280' }}>Groups</p>
              <div className="flex flex-wrap gap-1">
                {e.groups.map(g => (
                  <span key={g} className="text-xs terminal px-1.5 py-0.5 rounded"
                    style={{ background: '#EF444415', color: '#FF9CA3', border: '1px solid #EF444433' }}>{g}</span>
                ))}
              </div>
            </div>
          )}
        </>}
        {e.type === 'Process' && <>
          <Field label="Process Name" value={e.id} mono />
          <Field label="PID" value={e.pid?.toString()} mono />
          <Field label="Parent" value={e.parent} mono />
          <Field label="Command Line" value={e.cmdline} mono />
          <div>
            <p className="text-xs mb-1" style={{ color: '#6B7280' }}>Hash (SHA256)</p>
            <div className="flex items-center gap-1.5">
              <Hash size={10} style={{ color: '#D84C7F', flexShrink: 0 }} />
              <p className="text-xs terminal break-all" style={{ color: '#D84C7F' }}>{e.hash}</p>
            </div>
          </div>
          {e.signed === false && (
            <div className="p-2 rounded" style={{ background: '#EF444415', border: '1px solid #EF444433' }}>
              <p className="text-xs" style={{ color: '#EF4444' }}>⚠ Unsigned binary — not in allowlist</p>
            </div>
          )}
        </>}

        {/* Alerts */}
        {e.alerts?.length > 0 && (
          <div>
            <p className="text-xs mb-1" style={{ color: '#6B7280' }}>Related Alerts</p>
            <div className="flex flex-wrap gap-1.5">
              {e.alerts.map(a => (
                <span key={a} className="text-xs terminal px-2 py-0.5 rounded"
                  style={{ background: '#EF444415', color: '#EF4444', border: '1px solid #EF444433' }}>{a}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="p-3 border-t space-y-2" style={{ borderColor: '#1F2937' }}>
        <p className="text-xs terminal" style={{ color: '#4B5563' }}>QUICK ACTIONS</p>
        <button className="w-full text-xs terminal py-1.5 rounded hover:brightness-125 transition-all"
          style={{ background: '#EF444418', color: '#EF4444', border: '1px solid #EF444433' }}>
          Isolate Entity
        </button>
        <button className="w-full text-xs terminal py-1.5 rounded hover:brightness-125 transition-all"
          style={{ background: '#3B6FE318', color: '#3B6FE3', border: '1px solid #3B6FE333' }}>
          Add to Investigation
        </button>
      </div>
    </div>
  );
}
