import React, { useState, useEffect } from 'react';
import { Activity, Shield, Map, AlertTriangle, Info } from 'lucide-react';
import { useAuth } from '../store/AuthContext';

export default function HeatmapView() {
  const { authenticatedFetch } = useAuth();
  const [heatmap, setHeatmap] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHeatmap = async () => {
      try {
        const res = await authenticatedFetch('http://localhost:8000/reports/triage/triage_heatmap.json');
        if (res.ok) {
          const data = await res.json();
          setHeatmap(data);
        }
      } catch (err) {
        console.error('Failed to fetch heatmap:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchHeatmap();
    const id = setInterval(fetchHeatmap, 10000);
    return () => clearInterval(id);
  }, [authenticatedFetch]);

  const sortedNodes = Object.entries(heatmap).sort((a, b) => {
    const sevScore = { 'CRITICAL': 3, 'WARNING': 2, 'INFO': 1 };
    return sevScore[b[1].max_severity] - sevScore[a[1].max_severity] || b[1].hits - a[1].hits;
  });

  return (
    <div className="flex flex-col h-full bg-[#0B1117]">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-[#1F2937] bg-[#0d1117]">
        <Activity size={16} className="text-[#E5A862] animate-pulse" />
        <h2 className="panel-heading">Subnet Risk Heatmap</h2>
        <div className="ml-auto flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#EF4444] shadow-[0_0_8px_#EF4444]" />
            <span className="text-[10px] terminal text-[#6B7280]">CRITICAL</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#E5A862]" />
            <span className="text-[10px] terminal text-[#6B7280]">WARNING</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-[#88C057]" />
            <span className="text-[10px] terminal text-[#6B7280]">BENIGN</span>
          </div>
        </div>
      </div>

      {/* Grid Container */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="flex items-center gap-2 mb-6">
          <Map size={14} className="text-[#4B5563]" />
          <span className="text-xs terminal text-[#4B5563] uppercase tracking-widest">Aggregated Risk Vectors (Stateful Intelligence)</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-2 border-[#E5A862] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : sortedNodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 opacity-30">
            <Shield size={48} className="text-[#1F2937] mb-4" />
            <p className="terminal text-sm">No risk data available for current segment.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {sortedNodes.map(([ip, data]) => {
              const isCritical = data.max_severity === 'CRITICAL';
              const isWarning = data.max_severity === 'WARNING';
              const color = isCritical ? '#EF4444' : isWarning ? '#E5A862' : '#88C057';
              
              return (
                <div key={ip} 
                  className="p-4 rounded-xl border transition-all hover:scale-[1.02] cursor-pointer group"
                  style={{ 
                    background: `${color}05`, 
                    borderColor: `${color}22`,
                    boxShadow: isCritical ? `0 0 20px ${color}08` : 'none'
                  }}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex flex-col">
                      <span className="text-[10px] terminal tracking-tighter opacity-40 uppercase">Source IP</span>
                      <span className="text-sm font-bold terminal" style={{ color: '#E2E8F0' }}>{ip}</span>
                    </div>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isCritical ? 'animate-pulse' : ''}`}
                      style={{ background: `${color}15`, border: `1px solid ${color}33` }}>
                      {isCritical ? <AlertTriangle size={18} style={{ color }} /> : <Shield size={18} style={{ color }} />}
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="flex justify-between items-end">
                      <div className="flex flex-col">
                        <span className="text-[14px] font-bold terminal" style={{ color }}>{data.max_severity}</span>
                        <span className="text-[9px] terminal opacity-40 uppercase">Highest Severity</span>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-[14px] font-bold terminal text-[#E2E8F0]">{data.hits}</span>
                        <span className="text-[9px] terminal opacity-40 uppercase">Total Hits</span>
                      </div>
                    </div>

                    {/* Mini Heat Strip */}
                    <div className="h-1.5 rounded-full overflow-hidden flex gap-0.5" style={{ background: '#1F2937' }}>
                      {Array.from({ length: Math.min(10, Math.ceil(data.hits / 5)) }).map((_, i) => (
                        <div key={i} className="flex-1 h-full rounded-full" style={{ background: color }} />
                      ))}
                    </div>

                    <div className="flex items-center gap-2 pt-2 border-t border-[#1F2937]">
                      <Info size={10} className="text-[#4B5563]" />
                      <span className="text-[9px] terminal text-[#4B5563]">Last event detected {new Date(data.last_seen).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer / Stats */}
      <div className="px-5 py-3 border-t border-[#1F2937] bg-[#0d1117] flex items-center justify-between">
        <div className="flex gap-6">
          <div className="flex flex-col">
            <span className="text-[16px] font-bold terminal text-[#EF4444]">{sortedNodes.filter(n => n[1].max_severity === 'CRITICAL').length}</span>
            <span className="text-[9px] terminal text-[#4B5563] uppercase">Critical Nodes</span>
          </div>
          <div className="flex flex-col">
            <span className="text-[16px] font-bold terminal text-[#E5A862]">{sortedNodes.filter(n => n[1].max_severity === 'WARNING').length}</span>
            <span className="text-[9px] terminal text-[#4B5563] uppercase">Warning Nodes</span>
          </div>
        </div>
        <button className="text-[10px] terminal px-4 py-2 rounded border border-[#1F2937] text-[#6B7280] hover:bg-white/5 transition-all">
          EXPORT RISK MANIFEST
        </button>
      </div>
    </div>
  );
}
