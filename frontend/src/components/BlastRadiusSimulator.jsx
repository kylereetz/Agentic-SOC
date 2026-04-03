import React, { useState } from 'react';
import { Shield, AlertTriangle, X, Users, Server, Wifi, TrendingDown } from 'lucide-react';

const IMPACT_DATA = {
  affectedSystems: ['Host-DX9', 'srv-dc01', 'Host-WS4', '192.168.1.105'],
  connectedHosts: ['wks-kyler', '10.0.0.22', 'Host-WS7', 'Host-WS9', 'OT-PLC-01'],
  usersImpacted: ['KR\\admin', 'KR\\svc_sql', 'KR\\jdoe'],
  riskReduction: 78,
  containmentTime: '~12 min',
};

export default function BlastRadiusSimulator({ onClose }) {
  const [confirmed, setConfirmed] = useState(false);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center"
      style={{ background: 'rgba(11,17,23,0.88)', backdropFilter: 'blur(4px)' }}>
      <div className="w-full max-w-xl rounded-xl overflow-hidden animate-slide-in"
        style={{ background: '#111827', border: '1px solid #EF444444', boxShadow: '0 0 40px rgba(239,68,68,0.15)' }}>
        
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b"
          style={{ borderColor: '#EF444433', background: '#0d1117' }}>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: '#EF444422', border: '1px solid #EF444444' }}>
            <Shield size={16} style={{ color: '#EF4444' }} />
          </div>
          <div>
            <p className="text-sm font-bold" style={{ color: '#EF4444' }}>BLAST RADIUS SIMULATOR</p>
            <p className="text-xs terminal" style={{ color: '#6B7280' }}>Predicted containment impact for: isolate_host --id "Host-DX9"</p>
          </div>
          <button onClick={onClose} className="ml-auto p-1.5 rounded hover:bg-white/5 transition-colors">
            <X size={14} style={{ color: '#6B7280' }} />
          </button>
        </div>

        {/* Impact Metrics */}
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            {[
              { icon: Server, label: 'Affected Systems', items: IMPACT_DATA.affectedSystems, color: '#EF4444' },
              { icon: Wifi, label: 'Connected Hosts', items: IMPACT_DATA.connectedHosts, color: '#E5A862' },
              { icon: Users, label: 'Users Impacted', items: IMPACT_DATA.usersImpacted, color: '#3B6FE3' },
            ].map(({ icon: Icon, label, items, color }) => (
              <div key={label} className="rounded-lg p-3" style={{ background: '#0B1117', border: `1px solid ${color}22` }}>
                <div className="flex items-center gap-2 mb-2">
                  <Icon size={12} style={{ color }} />
                  <span className="text-xs terminal font-bold" style={{ color }}>{label}</span>
                  <span className="ml-auto text-xs terminal" style={{ color: '#6B7280' }}>{items.length}</span>
                </div>
                <ul className="space-y-1">
                  {items.map(item => (
                    <li key={item} className="text-xs terminal" style={{ color: '#9CA3AF' }}>• {item}</li>
                  ))}
                </ul>
              </div>
            ))}

            {/* Risk Reduction */}
            <div className="rounded-lg p-3 flex flex-col justify-center items-center"
              style={{ background: '#0B1117', border: '1px solid #88C05733' }}>
              <TrendingDown size={20} style={{ color: '#88C057' }} />
              <p className="text-3xl font-bold mt-1" style={{ color: '#88C057' }}>{IMPACT_DATA.riskReduction}%</p>
              <p className="text-xs terminal mt-1" style={{ color: '#6B7280' }}>Risk Reduction</p>
              <p className="text-xs terminal mt-2 text-center" style={{ color: '#6B7280' }}>
                Est. containment time:<br />
                <span style={{ color: '#E5A862' }}>{IMPACT_DATA.containmentTime}</span>
              </p>
            </div>
          </div>

          {/* Warning */}
          <div className="flex items-start gap-2 p-3 rounded-lg"
            style={{ background: '#E5A86211', border: '1px solid #E5A86233' }}>
            <AlertTriangle size={13} style={{ color: '#E5A862', flexShrink: 0, marginTop: 1 }} />
            <p className="text-xs" style={{ color: '#E5A862' }}>
              This containment will temporarily affect 5 connected hosts. OT-PLC-01 will lose remote monitoring capabilities for ~12 minutes. Notify OT team before executing.
            </p>
          </div>

          {/* Confirm */}
          {!confirmed ? (
            <div className="flex gap-3">
              <button onClick={() => setConfirmed(true)}
                className="flex-1 text-sm font-bold terminal py-2.5 rounded-lg hover:brightness-125 transition-all glow-red"
                style={{ background: '#EF444422', color: '#EF4444', border: '1px solid #EF444444' }}>
                Confirm Containment
              </button>
              <button onClick={onClose}
                className="text-sm terminal px-5 py-2.5 rounded-lg hover:bg-white/5 transition-colors"
                style={{ color: '#6B7280', border: '1px solid #1F2937' }}>
                Cancel
              </button>
            </div>
          ) : (
            <div className="text-center py-3">
              <p className="text-sm font-bold" style={{ color: '#88C057' }}>✓ Containment command dispatched to WARDEN-07</p>
              <button onClick={onClose} className="mt-2 text-xs terminal" style={{ color: '#4B5563' }}>Close</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
