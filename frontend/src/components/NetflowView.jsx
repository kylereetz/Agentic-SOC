import React, { useState, useEffect, useCallback } from 'react';
import { Activity, Wifi, ShieldAlert, ArrowRightLeft, Clock, ShieldCheck, Filter } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';

export default function NetflowView() {
  const { token } = useAuth();
  const { setSelectedHost } = useSOC();
  const [flows, setFlows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterStr, setFilterStr] = useState('');

  const fetchNetflow = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch('http://localhost:8000/api/v1/netflow', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setFlows(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch netflow:', err);
      setError('Connection to Traffic Sieve failed');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchNetflow();
    const interval = setInterval(fetchNetflow, 10000); // 10s polling
    return () => clearInterval(interval);
  }, [fetchNetflow]);

  // Aggregate stats
  const totalFlows = flows.length;
  const totalBytes = flows.reduce((sum, f) => sum + (f.bytes_transfer || 0), 0);
  const totalEvents = flows.reduce((sum, f) => sum + (f.connection_count || 1), 0);

  // Format bytes helper
  const formatBytes = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(2) + ' MB';
  };

  // Format date helper
  const formatTime = (ts) => {
    if (!ts) return '—';
    const d = new Date(ts * 1000);
    return d.toLocaleTimeString([], { hour12: false });
  };

  const filteredFlows = flows.filter(f => 
    !filterStr || 
    f.source.includes(filterStr) || 
    f.target.includes(filterStr)
  );

  return (
    <div className="flex flex-col h-full bg-app">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0 border-panel bg-[#0d1117]">
        <div className="flex items-center gap-3">
          <Wifi size={14} style={{ color: '#3B6FE3' }} className="animate-pulse" />
          <span className="text-xs font-bold tracking-widest text-[#E2E8F0]">
            NETFLOW / TRAFFIC DASHBOARD
          </span>
          <span className="text-xs terminal px-2 py-0.5 rounded-full"
            style={{ background: '#3B6FE320', color: '#3B6FE3', border: '1px solid #3B6FE340' }}>
            SENTINEL-TRAFFIC-SIEVE
          </span>
        </div>
        
        {/* KPI Summaries up top */}
        <div className="flex items-center gap-6">
          <div className="flex flex-col items-end">
            <span className="h-stat-sm" style={{ color: '#3B6FE3' }}>{formatBytes(totalBytes)}</span>
            <span className="h-meta mt-0.5 text-[#6B7280]">TOTAL VOLUME</span>
          </div>
          <div className="flex flex-col items-end">
            <span className="h-stat-sm" style={{ color: '#88C057' }}>{totalEvents}</span>
            <span className="h-meta mt-0.5 text-[#6B7280]">ACTIVE CONNECTIONS</span>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-4 px-5 py-3 border-b border-panel flex-shrink-0">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-panel" style={{ background: '#111827' }}>
          <Filter size={12} color="#6B7280" />
          <input 
            type="text" 
            placeholder="Filter by IP / Hostname..." 
            value={filterStr}
            onChange={e => setFilterStr(e.target.value)}
            className="bg-transparent border-none outline-none text-xs terminal text-[#CBD5E1] w-48 placeholder-[#4B5563]"
          />
        </div>
      </div>

      {/* Data Grid Header */}
      <div className="grid h-label px-5 py-2.5 border-b flex-shrink-0"
        style={{ gridTemplateColumns: 'flex-1 40px flex-1 120px 100px 100px 130px 130px', borderColor: '#1F2937', background: '#080d14' }}>
        <span>Source</span>
        <span className="text-center"></span>
        <span>Destination</span>
        <span>Ports</span>
        <span>Bytes</span>
        <span>Count</span>
        <span>First Seen</span>
        <span>Last Seen</span>
      </div>

      {/* Data Grid Body */}
      <div className="flex-1 overflow-y-auto">
        {loading && flows.length === 0 ? (
           <div className="flex flex-col items-center justify-center p-12 gap-3 opacity-50">
             <div className="w-8 h-8 border-2 border-[#3B6FE3] border-t-transparent flex-shrink-0 rounded-full animate-spin" />
             <p className="h-meta">Ingesting Flow Telemetry...</p>
           </div>
        ) : error ? (
           <div className="flex flex-col items-center justify-center p-12 gap-3">
             <ShieldAlert size={24} color="#EF4444" />
             <p className="h-body text-[#EF4444]">{error}</p>
           </div>
        ) : filteredFlows.length === 0 ? (
           <div className="flex flex-col items-center justify-center p-12 gap-3 opacity-50">
             <ShieldCheck size={24} color="#6B7280" />
             <p className="h-body text-[#6B7280]">No active flows mapped.</p>
           </div>
        ) : (
          filteredFlows.map((flow, i) => {
            // Determine structural anomaly based on high bytes vs mean (simplified heuristic for UI highlight)
            const isAnomalous = flow.bytes_transfer > flow.mean_bytes * 5 && flow.bytes_transfer > 500000;
            const rowBg = isAnomalous ? '#EF444410' : (i % 2 === 0 ? 'transparent' : '#111827');
            const rowBorder = isAnomalous ? '2px solid #EF444480' : '2px solid transparent';
            
            return (
              <div key={i} className="grid items-center px-5 py-3 border-b hover:brightness-125 transition-all animate-fade-scale"
                style={{ 
                  gridTemplateColumns: 'minmax(0,1fr) 40px minmax(0,1fr) 120px 100px 100px 130px 130px', 
                  borderColor: '#1F2937', 
                  background: rowBg,
                  borderLeft: rowBorder
                }}>
                <span 
                  className="h-title-sm truncate hover:underline cursor-pointer" 
                  style={{ color: isAnomalous ? '#FECACA' : '#93C5FD' }}
                  onClick={() => setSelectedHost(flow.source)}>
                  {flow.source}
                </span>
                <div className="flex justify-center">
                   <ArrowRightLeft size={12} color="#4B5563" />
                </div>
                <span 
                  className="h-title-sm truncate text-[#E2E8F0] hover:underline cursor-pointer"
                  onClick={() => setSelectedHost(flow.target)}>
                  {flow.target}
                </span>
                
                <div className="flex flex-wrap gap-1 pr-4">
                  {(flow.ports || []).slice(0, 3).map(p => (
                    <span key={p} className="h-meta px-1.5 py-0.5 rounded" style={{ background: '#3B6FE315', color: '#3B6FE3' }}>
                      {p}
                    </span>
                  ))}
                  {flow.ports?.length > 3 && <span className="h-meta text-[#6B7280]">+{flow.ports.length - 3}</span>}
                </div>
                
                <span className="h-meta" style={{ color: isAnomalous ? '#E5A862' : '#CBD5E1' }}>
                  {formatBytes(flow.bytes_transfer)}
                </span>
                
                <span className="h-meta text-[#9CA3AF]">{flow.connection_count}</span>
                
                <span className="h-meta text-[#6B7280]">{formatTime(flow.first_seen)}</span>
                <span className="h-meta text-[#9CA3AF]">{formatTime(flow.last_seen)}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
