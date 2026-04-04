import { TrendingUp, AlertCircle, Target, Clock, Activity } from 'lucide-react';
import { useSOC } from '../store/SOCContext';

// Historical trend fixtures (storing fixed targets for visual modeling)
const AUTONOMY_TREND = [
  { month: 'Oct', auto: 68, human: 32 }, { month: 'Nov', auto: 74, human: 26 },
  { month: 'Dec', auto: 79, human: 21 }, { month: 'Jan', auto: 83, human: 17 },
  { month: 'Feb', auto: 87, human: 13 }, { month: 'Mar', auto: 91, human: 9 },
];

const FP_TREND = [
  { week: 'W1', rate: 14 }, { week: 'W2', rate: 11 }, { week: 'W3', rate: 9 },
  { week: 'W4', rate: 7 }, { week: 'W5', rate: 7 }, { week: 'W6', rate: 5 },
];

const DURATION_DATA = [
  { stage: 'Triage', min: 2, avg: 8, max: 24 },
  { stage: 'Invest.', min: 15, avg: 45, max: 180 },
  { stage: 'Contain.', min: 5, avg: 18, max: 60 },
  { stage: 'Eradicate', min: 10, avg: 35, max: 120 },
  { stage: 'Recovery', min: 30, avg: 90, max: 240 },
];

const PIE_DATA = [
  { name: 'Autonomous', value: 91, color: '#D84C7F' },
  { name: 'Human-Assist', value: 9, color: '#3B6FE3' },
];

const TOOLTIP_STYLE = {
  backgroundColor: '#111827', border: '1px solid #1F2937', color: '#CBD5E1', fontSize: 11, borderRadius: 6
};

function MetricCard({ icon: Icon, label, value, delta, color }) {
  return (
    <div className="rounded-lg p-4" style={{ background: '#111827', border: '1px solid #1F2937' }}>
      <div className="flex items-center justify-between mb-2">
        <p className="h-label" style={{ color: '#6B7280' }}>{label}</p>
        <Icon size={14} style={{ color }} />
      </div>
      <p className="h-stat" style={{ color }}>{value}</p>
      {delta && <p className="h-meta mt-1" style={{ color: '#88C057' }}>{delta}</p>}
    </div>
  );
}

export default function AnalyticsDashboard() {
  const { agents, autonomy } = useSOC();

  // Derive dynamic agent performance from the current roster
  const liveAgentPerf = (agents || [])
    .slice(0, 6)
    .map(a => ({
      agent: a.id.replace('SENTINEL-', ''),
      success: a.success || 0
    }));

  const avgSuccess = agents?.length 
    ? Math.round(agents.reduce((acc, a) => acc + (a.success || 0), 0) / agents.length)
    : 0;

  const pieData = [
    { name: 'Autonomous', value: autonomy.level, color: '#D84C7F' },
    { name: 'Human-Assist', value: 100 - autonomy.level, color: '#3B6FE3' },
  ];

  return (
    <div className="flex flex-col h-full overflow-y-auto bg-app">
      <div className="flex items-center justify-between px-5 py-3 border-b flex-shrink-0 bg-[#0d1117] border-panel">
        <div className="flex items-center gap-3">
          <TrendingUp size={14} style={{ color: '#88C057' }} />
          <span className="text-xs font-bold tracking-widest text-[#E2E8F0]">PERFORMANCE ANALYTICS</span>
          <span className="text-xs terminal px-2 py-0.5 rounded-full"
            style={{ background: '#88C05720', color: '#88C057', border: '1px solid #88C05740' }}>
            ENGINE.TELEMETRY.AGGR
          </span>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4">
          <MetricCard icon={Target} label="AUTONOMY RATIO" value={`${autonomy.level}%`} delta="↑ 4.1% MoM" color="#D84C7F" />
          <MetricCard icon={AlertCircle} label="FALSE POSITIVE RATE" value="5.2%" delta="↓ 0.8% WoW" color="#88C057" />
          <MetricCard icon={Activity} label="HIVE SUCCESS MEAN" value={`${avgSuccess}%`} delta="↑ 0.2% LIVE" color="#3B6FE3" />
          <MetricCard icon={Clock} label="MTTI (MEAN TIME TO INVEST.)" value="48 min" delta="↓ 14 min AVG" color="#E5A862" />
        </div>

        {/* Autonomy Trend + Pie */}
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2 rounded-xl p-5 border border-panel bg-[#111827]">
            <p className="h-label text-[#6B7280] mb-4">AUTONOMY ADOPTION CURVE</p>
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={AUTONOMY_TREND}>
                <defs>
                  <linearGradient id="autoGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D84C7F" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="#D84C7F" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                <XAxis dataKey="month" tick={{ fill: '#4B5563', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4B5563', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} domain={[50, 100]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Area type="monotone" dataKey="auto" stroke="#D84C7F" fill="url(#autoGrad)" strokeWidth={2} name="AI Autonomous %" />
                <Area type="monotone" dataKey="human" stroke="#3B6FE3" fill="transparent" strokeWidth={1.5} strokeDasharray="4 2" name="Human Assist %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="rounded-xl p-5 border border-panel bg-[#111827] flex flex-col items-center justify-center">
            <p className="h-label text-[#6B7280] mb-4">CURRENT LOAD DISTRIBUTION</p>
            <ResponsiveContainer width="100%" height={150}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={65} dataKey="value" strokeWidth={0}>
                  {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-col gap-2 w-full mt-4">
              {pieData.map(d => (
                <div key={d.name} className="flex items-center justify-between px-2">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: d.color }} />
                    <span className="h-meta">{d.name}</span>
                  </div>
                  <span className="h-stat-sm" style={{ color: d.color }}>{d.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* FP Rate + Agent Perf */}
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-xl p-5 border border-panel bg-[#111827]">
            <p className="h-label text-[#6B7280] mb-4">FALSE POSITIVE SUPPRESSION (6 weeks)</p>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={FP_TREND}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                <XAxis dataKey="week" tick={{ fill: '#4B5563', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4B5563', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} unit="%" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Line type="monotone" dataKey="rate" stroke="#88C057" strokeWidth={2} dot={{ fill: '#88C057', r: 3 }} name="FP Rate" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="rounded-xl p-5 border border-panel bg-[#111827]">
            <p className="h-label text-[#6B7280] mb-4">LIVE AGENT RELIABILITY (Success %)</p>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={liveAgentPerf} barSize={24}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
                <XAxis dataKey="agent" tick={{ fill: '#4B5563', fontSize: 9, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#4B5563', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} domain={[80, 100]} unit="%" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey="success" name="Success %" radius={[4, 4, 0, 0]}>
                  {liveAgentPerf.map((_, i) => (
                    <Cell key={i} fill={['#D84C7F', '#3B6FE3', '#EF4444', '#88C057', '#E5A862', '#3B6FE3'][i % 6]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Duration */}
        <div className="rounded-xl p-5 border border-panel bg-[#111827]">
          <p className="h-label text-[#6B7280] mb-4">PIPELINE LATENCY BY MISSION PHASE (minutes)</p>
          <ResponsiveContainer width="100%" height={130}>
            <BarChart data={DURATION_DATA} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" vertical={false} />
              <XAxis dataKey="stage" tick={{ fill: '#4B5563', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#4B5563', fontSize: 10, fontFamily: 'JetBrains Mono' }} axisLine={false} tickLine={false} unit="m" />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="avg" name="Avg Duration" fill="#3B6FE3" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
