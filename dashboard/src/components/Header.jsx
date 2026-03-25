import React, { useState } from 'react';
import { PowerOff, Bell, Search, Shield, ChevronDown, AlertTriangle, LogOut } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { useSOC } from '../store/SOCContext';

export default function Header({ chitchatOpen, onToggleChitChat }) {
  const { user, logout } = useAuth();
  const { autonomy } = useSOC();
  const [killActive, setKillActive] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center justify-between px-4 border-b scanline-overlay"
      style={{ background: 'rgba(11,17,23,0.96)', borderColor: '#1F2937', backdropFilter: 'blur(10px)' }}>

      {/* LEFT: Logo */}
      <div className="flex items-center gap-3 min-w-[220px]">
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center animate-pulse-blue"
          style={{ background: 'linear-gradient(135deg,#1a2240,#0d1117)', border: '1px solid #3B6FE388' }}>
          <Shield size={17} style={{ color: '#3B6FE3' }} />
        </div>
        <div className="flex items-baseline gap-0.5">
          <span className="font-bold tracking-widest text-sm" style={{ color: '#3B6FE3', textShadow: '0 0 12px rgba(59,111,227,0.5)' }}>AEGIS</span>
          <span className="font-bold tracking-widest text-sm" style={{ color: '#E2E8F0' }}>AGENT</span>
        </div>
        <div className="flex items-center gap-1.5 ml-2">
          <span className="animate-blink w-2 h-2 rounded-full inline-block" style={{ background: '#88C057', boxShadow: '0 0 6px #88C057' }} />
          <span className="text-xs terminal font-mono" style={{ color: '#88C057', textShadow: '0 0 8px rgba(136,192,87,0.5)' }}>LIVE</span>
        </div>
      </div>

      {/* CENTER: Global Search */}
      <div className="flex-1 max-w-xl mx-6">
        <div className="relative group">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 transition-colors group-hover:text-blue-400" style={{ color: '#4B5563' }} />
          <input
            type="text"
            placeholder="Search Global Intelligence — entities, IPs, IOCs, incidents..."
            className="w-full text-xs rounded-lg py-2 pl-9 pr-16 focus:outline-none terminal transition-all"
            style={{
              background: '#0d1117',
              border: '1px solid #1F2937',
              color: '#9CA3AF',
            }}
            onFocus={e => { e.target.style.borderColor = '#3B6FE355'; e.target.style.boxShadow = '0 0 0 3px rgba(59,111,227,0.08)'; }}
            onBlur={e => { e.target.style.borderColor = '#1F2937'; e.target.style.boxShadow = 'none'; }}
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
            <kbd className="text-xs terminal" style={{ color: '#4B5563' }}>⌘K</kbd>
          </div>
        </div>
      </div>

      {/* RIGHT: Controls */}
      <div className="flex items-center gap-4 justify-end flex-1 max-w-[500px]">
        {/* User Identity & Autonomy (Consolidated here to fix overlap) */}
        <div className="hidden lg:flex items-center gap-4 pr-2 border-r" style={{ borderColor: '#1F2937' }}>
          <div className="flex flex-col items-end">
            <span className="text-[10px] terminal text-[#4B5563] tracking-tighter">IDENTITY: {user?.username?.toUpperCase() || 'UNKNOWN'}</span>
            <span className="text-[10px] terminal tracking-tighter" style={{ color: user?.role === 'admin' ? '#D84C7F' : '#3B6FE3' }}>
              {user?.role?.toUpperCase() || 'GUEST'}
            </span>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-[#88C05710] border border-[#88C05730]">
             <span className="text-[10px] terminal font-bold" style={{ color: '#88C057' }}>AI {autonomy?.level || 0}%</span>
          </div>
        </div>

        {/* Kill Switch */}
        <button
          onClick={() => setKillActive(v => !v)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold tracking-widest transition-all action-btn ${
            killActive ? 'bg-red-600' : 'bg-red-500/10'
          }`}
          style={{
            border: `1px solid ${killActive ? '#EF4444' : '#EF444466'}`,
            color: killActive ? 'white' : '#EF4444',
          }}>
          <PowerOff size={11} className={killActive ? 'animate-spin-slow' : ''} />
          <span className="hidden xl:inline">EMERGENCY KILL</span>
          <span className="xl:hidden">KILL</span>
        </button>

        {/* Bell */}
        <button
          className="relative p-2 rounded-lg transition-all hover:bg-white/5"
          onClick={() => setNotifOpen(v => !v)}>
          <Bell size={15} style={{ color: '#9CA3AF' }} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full animate-blink"
            style={{ background: '#EF4444', boxShadow: '0 0 6px #EF4444' }} />
        </button>

        {/* User profile dropdown trigger */}
        <div className="relative">
          <button 
            className="flex items-center gap-2 px-2 py-1 rounded-lg transition-all hover:bg-white/5"
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}>
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: 'linear-gradient(135deg,#3B6FE3,#6B8FE8)', color: 'white', boxShadow: '0 0 8px rgba(59,111,227,0.4)' }}>
              {user?.username?.substring(0,2).toUpperCase() || '??'}
            </div>
            <ChevronDown size={11} style={{ color: '#4B5563' }} />
          </button>

          {userDropdownOpen && (
            <div className="absolute top-10 right-0 w-40 rounded-lg overflow-hidden z-[100] shadow-2xl animate-slide-in-up"
                 style={{ background: '#111827', border: '1px solid #1F2937' }}>
              <button 
                onClick={logout}
                className="w-full flex items-center gap-3 px-4 py-2.5 text-xs terminal text-red-400 hover:bg-red-500/10 transition-colors">
                <LogOut size={12} />
                LOGOUT SYSTEM
              </button>
            </div>
          )}
        </div>

        {/* Copilot Toggle Button */}
        <button
          onClick={onToggleChitChat}
          className="flex items-center gap-1.5 text-xs terminal px-3 py-1.5 rounded-lg hover:brightness-125 transition-all"
          style={{ background: chitchatOpen ? '#3B6FE322' : '#111827', color: '#3B6FE3', border: '1px solid #3B6FE344' }}>
          ✦ ChitChat
        </button>
      </div>

      {/* Notification dropdown */}
      {notifOpen && (
        <div
          className="absolute top-14 right-4 w-72 rounded-xl overflow-hidden animate-slide-in-down z-50"
          style={{ background: '#111827', border: '1px solid #1F2937', boxShadow: '0 16px 40px rgba(0,0,0,0.6)' }}>
          <div className="px-4 py-2.5 border-b flex items-center justify-between" style={{ borderColor: '#1F2937' }}>
            <span className="text-xs font-bold terminal" style={{ color: '#E2E8F0' }}>NOTIFICATIONS</span>
            <span className="text-xs terminal px-1.5 py-0.5 rounded" style={{ background: '#EF444418', color: '#EF4444' }}>3 NEW</span>
          </div>
          {[
            { color: '#EF4444', icon: '🔴', text: 'Host isolation confirmed — Host-DX9', time: '2m ago' },
            { color: '#E5A862', icon: '⚠', text: 'WARDEN-07 waiting for approval',      time: '4m ago' },
            { color: '#D84C7F', icon: '🧠', text: 'New hypothesis: Silver Ticket attack', time: '6m ago' },
          ].map((n, i) => (
            <div key={i} className="flex items-start gap-3 px-4 py-3 border-b hover:bg-white/5 transition-colors cursor-pointer"
              style={{ borderColor: '#1F2937' }}>
              <span className="text-sm mt-0.5">{n.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="text-xs" style={{ color: '#CBD5E1' }}>{n.text}</p>
                <p className="text-xs terminal mt-0.5" style={{ color: '#4B5563' }}>{n.time}</p>
              </div>
              <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: n.color }} />
            </div>
          ))}
        </div>
      )}
    </header>
  );
}
