import React, { useState } from 'react';
import { useAuth } from '../store/AuthContext';
import { Shield, Lock, User, AlertCircle, Loader2 } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const success = await login(username, password);
    if (!success) {
      setError('Invalid identity credentials or unauthorized access attempt.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 scanline-overlay" style={{ background: '#0B1117' }}>
      <div className="w-full max-w-md animate-slide-in-up">
        {/* Branding */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 neon-border-blue"
            style={{ background: '#111827', border: '1px solid #3B6FE344' }}>
            <Shield size={32} style={{ color: '#3B6FE3' }} className="animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold tracking-widest text-[#E2E8F0] mb-2">AEGIS AGENT</h1>
          <p className="text-xs terminal text-[#4B5563]">AGENTIC SIEM COMMAND CENTER v1.0 MVP</p>
        </div>

        {/* Login Card */}
        <div className="rounded-2xl p-8 shadow-2xl transition-all"
          style={{ background: '#111827', border: '1px solid #1F2937' }}>
          
          <div className="mb-6">
            <h2 className="text-lg font-bold text-[#D84C7F]">IDENTITY AUTHENTICATION</h2>
            <p className="text-xs terminal text-[#6B7280] mt-1">SENTINEL-GATEKEEPER PROXY ACTIVE</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs terminal text-[#4B5563] mb-2">OPERATOR ALIAS</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#1F2937]">
                  <User size={16} />
                </span>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1F2937] rounded-lg py-2.5 pl-10 pr-4 text-sm text-[#E2E8F0] focus:outline-none focus:border-[#3B6FE3] transition-all"
                  placeholder="e.g. admin"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs terminal text-[#4B5563] mb-2">ACCESS KEY</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#1F2937]">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1F2937] rounded-lg py-2.5 pl-10 pr-4 text-sm text-[#E2E8F0] focus:outline-none focus:border-[#D84C7F] transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-[#EF444411] border border-[#EF444433] text-[#EF4444] text-xs">
                <AlertCircle size={14} className="flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg font-bold text-xs terminal tracking-widest transition-all flex items-center justify-center gap-2 group"
              style={{
                background: loading ? '#1F2937' : 'linear-gradient(45deg, #3B6FE3, #D84C7F)',
                color: '#FFF',
                opacity: loading ? 0.7 : 1,
              }}>
              {loading ? <Loader2 size={16} className="animate-spin" /> : 'AUTHORIZE SESSION'}
            </button>
          </form>

          {/* Footer Info */}
          <div className="mt-8 pt-6 border-t border-[#1F2937] text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#88C05711] border border-[#88C05722]">
              <div className="w-1.5 h-1.5 rounded-full bg-[#88C057] animate-blink" />
              <span className="text-[10px] terminal text-[#88C057]">ENCRYPTED MFA TUNNEL ESTABLISHED</span>
            </div>
          </div>
        </div>

        <p className="text-center mt-6 text-[10px] terminal text-[#374151]">
          UNAUTHORIZED ACCESS IS PROHIBITED. ALL SESSIONS ARE MONITORED BY SENTINEL-AUDITOR.
        </p>
      </div>
    </div>
  );
}
