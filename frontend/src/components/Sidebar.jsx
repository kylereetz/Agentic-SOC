import React from 'react';
import {
  Search, AlertTriangle, Bot, BarChart2, Lock,
  FlaskConical, ChevronLeft, ChevronRight, Activity, Wifi,
  TrendingUp, Shield, Network, Crosshair, FileText
} from 'lucide-react';
import { useSOC } from '../store/SOCContext';

const NAV_ITEMS = [
  { icon: Search,       label: 'Investigations',  badge: '3',  color: '#3B6FE3' },
  { icon: Network,      label: 'Discovery / Audit',             color: '#D84C7F' },
  { icon: AlertTriangle,label: 'Alert Queue',      badge: '14', color: '#EF4444' },
  { icon: FileText,     label: 'Log Guardian',                  color: '#88C057' },
  { icon: Wifi,         label: 'Netflow / Traffic',             color: '#3B6FE3' },
  { icon: Bot,          label: 'Agents',           badge: '24', color: '#D84C7F' },
  { icon: TrendingUp,   label: 'Threat Intel',     badge: '2',  color: '#EF4444' },
  { icon: Shield,       label: 'Governance',                    color: '#A78BFA' },
  { icon: BarChart2,    label: 'Analytics',                     color: '#88C057' },
  { icon: Crosshair,    label: 'Adversary Sim',                 color: '#EF4444' },
  { icon: Lock,         label: 'Permissions',                   color: '#E5A862' },
  { icon: FlaskConical, label: 'Simulation Mode',               color: '#A78BFA' },
];

export default function Sidebar({ collapsed, onToggle, activeNav, onNavChange }) {
  const { pendingActions } = useSOC();
  const pendingCount = pendingActions.length;

  return (
    <div
      className="fixed left-0 top-14 bottom-0 z-40 flex flex-col transition-all duration-300 border-r"
      style={{ width: collapsed ? 56 : 220, background: '#0a0e17', borderColor: '#1F2937' }}>

      {/* Nav Items */}
      <nav className="flex-1 py-2 overflow-y-auto">
        {NAV_ITEMS.map(({ icon: Icon, label, badge, color }) => {
          const active = activeNav === label;
          const isPending = label === 'Alert Queue' && pendingCount > 0;
          const displayBadge = label === 'Agents' ? `${badge}` : badge;

          return (
            <button
              key={label}
              onClick={() => onNavChange(label)}
              title={collapsed ? label : ''}
              className="sidebar-nav-item w-full flex items-center gap-3 px-3.5 py-2.5 group"
              style={{
                '--item-color': color,
                background: active
                  ? `linear-gradient(to right, ${color}12, ${color}06)`
                  : 'transparent',
                borderLeft: active ? `2px solid ${color}` : '2px solid transparent',
              }}>

              {/* Icon */}
              <div className="relative flex-shrink-0">
                <Icon
                  size={15}
                  style={{ color: active ? color : '#4B5563', minWidth: 15, transition: 'color 0.2s' }}
                  className={active ? '' : 'group-hover:!text-gray-300'}
                />
                {/* Dot badge in collapsed mode */}
                {collapsed && badge && (
                  <span className="absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full animate-blink"
                    style={{ background: color, boxShadow: `0 0 4px ${color}` }} />
                )}
              </div>

              {/* Label + badge */}
              {!collapsed && (
                <>
                  <span
                    className={`h-title-sm whitespace-nowrap transition-colors duration-200 ${active ? '' : 'text-[#6B7280] group-hover:text-gray-300'}`}
                  >
                    {label}
                  </span>
                  {displayBadge && (
                    <span
                      className="ml-auto h-meta px-1.5 py-0.5 rounded-full transition-all"
                      style={{
                        background: `${color}22`,
                        color: color,
                        boxShadow: active ? `0 0 6px ${color}44` : 'none',
                      }}>
                      {displayBadge}
                    </span>
                  )}
                </>
              )}
            </button>
          );
        })}
      </nav>

      {/* Agent Mesh status */}
      {!collapsed && (
        <div className="px-3 py-3 border-t" style={{ borderColor: '#1F2937' }}>
          <div className="flex items-center gap-2 mb-2">
            <Activity size={11} style={{ color: '#88C057' }} className="animate-pulse" />
            <span className="h-label" style={{ color: '#4B5563' }}>Agent Mesh</span>
          </div>
          {/* Mini node grid — 24 agents */}
          <div className="grid grid-cols-6 gap-1">
            {Array.from({ length: 24 }).map((_, i) => (
              <div key={i}
                className="w-2.5 h-2.5 rounded-sm transition-all"
                style={{
                  background: i < 22 ? '#88C057' : i === 22 ? '#E5A862' : '#EF4444',
                  boxShadow: i < 22 ? '0 0 3px rgba(136,192,87,0.5)' : i === 22 ? '0 0 3px rgba(229,168,98,0.5)' : '0 0 3px rgba(239,68,68,0.5)',
                }} />
            ))}
          </div>
          <p className="h-meta mt-1.5" style={{ color: '#4B5563' }}>22/24 ONLINE · 1 PENDING</p>

          {/* Pending approvals */}
          {pendingCount > 0 && (
            <div className="mt-2 flex items-center gap-1.5 px-2 py-1 rounded"
              style={{ background: '#E5A86218', border: '1px solid #E5A86233' }}>
              <span className="animate-blink w-1.5 h-1.5 rounded-full" style={{ background: '#E5A862' }} />
              <span className="h-meta font-bold" style={{ color: '#E5A862' }}>{pendingCount} PENDING</span>
            </div>
          )}
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="absolute -right-3.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full flex items-center justify-center z-10 hover:brightness-125 transition-all action-btn"
        style={{ background: '#1a2035', border: '1px solid #2D3748', boxShadow: '0 2px 8px rgba(0,0,0,0.4)' }}>
        {collapsed
          ? <ChevronRight size={11} style={{ color: '#6B7280' }} />
          : <ChevronLeft  size={11} style={{ color: '#6B7280' }} />}
      </button>
    </div>
  );
}
