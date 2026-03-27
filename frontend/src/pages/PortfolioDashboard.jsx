import { useState, useEffect, useCallback } from 'react'
import { apiPortfolio, apiGetProfile } from '../api/bff'
import SupplierWorldMap from '../components/SupplierWorldMap'
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'

// ── Design tokens ────────────────────────────────────────────────────────────
const GATE_COLORS = {
  APPROVED:          '#38B2AC',
  'REQUIRES APPROVAL': '#F59E0B',
  BLOCKED:           '#EF4444',
}
const SCORE_ZONES = [
  { range: '0.00–0.20', color: '#38B2AC' },
  { range: '0.20–0.40', color: '#6C63FF' },
  { range: '0.40–0.60', color: '#F59E0B' },
  { range: '0.60–0.80', color: '#F97316' },
  { range: '0.80–1.00', color: '#EF4444' },
]
const BAR_COLOR = '#6C63FF'
const COUNTRY_COLOR = '#0891B2'

const fmt = (n) => (n === undefined || n === null ? '—' : n)
const pct = (n, total) => total > 0 ? `${((n / total) * 100).toFixed(1)}%` : '—'

// ── Shared tooltip style ──────────────────────────────────────────────────────
const TooltipBox = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="neu-card-sm px-3 py-2 text-[0.78rem]">
      {label && <p className="text-neu-muted mb-1 font-semibold">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color ?? p.fill ?? '#6C63FF' }}>
          {p.name ?? p.dataKey}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  )
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function KpiCard({ value, label, sub, color = 'text-neu-accent' }) {
  return (
    <div className="neu-card-sm p-4 text-center">
      <div className={`font-display text-2xl font-extrabold ${color} leading-none mb-0.5`}>{fmt(value)}</div>
      <div className="text-[0.65rem] text-neu-muted uppercase tracking-wide leading-tight">{label}</div>
      {sub && <div className="text-[0.62rem] text-[#A0AEC0] mt-0.5">{sub}</div>}
    </div>
  )
}

// ── Chart section wrapper ─────────────────────────────────────────────────────
function ChartCard({ title, subtitle, children }) {
  return (
    <div className="neu-card p-5 relative z-10">
      <p className="text-[0.7rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-0.5">{title}</p>
      {subtitle && <p className="text-[0.72rem] text-[#A0AEC0] mb-4">{subtitle}</p>}
      {!subtitle && <div className="mb-4" />}
      {children}
    </div>
  )
}

// ── Gate decision donut ───────────────────────────────────────────────────────
function GateDonut({ data }) {
  if (!data?.length) return <p className="text-neu-muted text-[0.82rem] text-center py-8">No data</p>
  const entries = data.map(d => ({ name: d.decision, value: d.count, color: GATE_COLORS[d.decision] ?? '#A0AEC0' }))
  const total   = entries.reduce((a, b) => a + b.value, 0)
  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie data={entries} cx="50%" cy="50%" innerRadius={62} outerRadius={96}
             dataKey="value" nameKey="name" paddingAngle={3}
             label={({ name, value }) => `${name} (${pct(value, total)})`}
             labelLine={false}>
          {entries.map((e, i) => (
            <Cell key={i} fill={e.color} stroke="transparent" />
          ))}
        </Pie>
        <Tooltip content={<TooltipBox />} />
        <Legend iconType="circle" iconSize={8}
                formatter={(v) => <span className="text-[0.72rem] text-neu-fg">{v}</span>} />
      </PieChart>
    </ResponsiveContainer>
  )
}

// ── Risk by country bar (horizontal) ─────────────────────────────────────────
function CountryBar({ data }) {
  if (!data?.length) return <p className="text-neu-muted text-[0.82rem] text-center py-8">No data</p>
  const sorted = [...data].sort((a, b) => b.avg_score - a.avg_score).slice(0, 10)
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, sorted.length * 32)}>
      <BarChart layout="vertical" data={sorted} margin={{ left: 0, right: 20, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(163,177,198,0.25)" horizontal={false} />
        <XAxis type="number" domain={[0, 1]} tickFormatter={v => v.toFixed(1)}
               tick={{ fontSize: 10, fill: '#6B7280' }} />
        <YAxis type="category" dataKey="country" width={110}
               tick={{ fontSize: 10, fill: '#6B7280' }} />
        <Tooltip content={<TooltipBox />} />
        <Bar dataKey="avg_score" name="Avg Risk Score" fill={COUNTRY_COLOR} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Score distribution histogram ─────────────────────────────────────────────
function ScoreHistogram({ data }) {
  if (!data?.length) return <p className="text-neu-muted text-[0.82rem] text-center py-8">No data</p>
  const bins = [
    { range: '0.0–0.2', count: 0 },
    { range: '0.2–0.4', count: 0 },
    { range: '0.4–0.6', count: 0 },
    { range: '0.6–0.8', count: 0 },
    { range: '0.8–1.0', count: 0 },
  ]
  data.forEach(({ score }) => {
    const idx = Math.min(Math.floor(score * 5), 4)
    bins[idx].count++
  })
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={bins} margin={{ left: -10, right: 10, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(163,177,198,0.25)" vertical={false} />
        <XAxis dataKey="range" tick={{ fontSize: 10, fill: '#6B7280' }} />
        <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: '#6B7280' }} />
        <Tooltip content={<TooltipBox />} />
        <Bar dataKey="count" name="Suppliers" radius={[4, 4, 0, 0]}>
          {bins.map((b, i) => <Cell key={i} fill={SCORE_ZONES[i].color} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Risk by category bar ───────────────────────────────────────────────────────
function CategoryBar({ data }) {
  if (!data?.length) return <p className="text-neu-muted text-[0.82rem] text-center py-8">No data</p>
  const sorted = [...data].sort((a, b) => b.avg_score - a.avg_score)
  return (
    <ResponsiveContainer width="100%" height={Math.max(200, sorted.length * 34)}>
      <BarChart layout="vertical" data={sorted} margin={{ left: 0, right: 20, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(163,177,198,0.25)" horizontal={false} />
        <XAxis type="number" domain={[0, 1]} tickFormatter={v => v.toFixed(1)}
               tick={{ fontSize: 10, fill: '#6B7280' }} />
        <YAxis type="category" dataKey="category" width={130}
               tick={{ fontSize: 10, fill: '#6B7280' }} />
        <Tooltip content={<TooltipBox />} />
        <Bar dataKey="avg_score" name="Avg Risk Score" fill={BAR_COLOR} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Top-10 highest risk suppliers table ───────────────────────────────────────
function TopRiskTable({ suppliers }) {
  if (!suppliers?.length) return null
  const top10 = [...suppliers].sort((a, b) => b.score - a.score).slice(0, 10)
  const decColor = (d) => {
    if (d === 'BLOCKED') return 'text-neu-risk-hi'
    if (d === 'REQUIRES APPROVAL') return 'text-neu-risk-md'
    return 'text-neu-teal'
  }
  return (
    <div className="neu-card p-5">
      <p className="text-[0.7rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-4">
        Top 10 Highest Risk Suppliers
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-[0.78rem]">
          <thead>
            <tr className="text-left">
              <th className="text-[0.65rem] font-bold uppercase tracking-[0.8px] text-neu-muted pb-2 pr-4">#</th>
              <th className="text-[0.65rem] font-bold uppercase tracking-[0.8px] text-neu-muted pb-2 pr-4">Supplier</th>
              <th className="text-[0.65rem] font-bold uppercase tracking-[0.8px] text-neu-muted pb-2 pr-4">Country</th>
              <th className="text-[0.65rem] font-bold uppercase tracking-[0.8px] text-neu-muted pb-2 pr-4">Category</th>
              <th className="text-[0.65rem] font-bold uppercase tracking-[0.8px] text-neu-muted pb-2 pr-4">Score</th>
              <th className="text-[0.65rem] font-bold uppercase tracking-[0.8px] text-neu-muted pb-2">Decision</th>
            </tr>
          </thead>
          <tbody>
            {top10.map((s, i) => {
              const score = s.score ?? 0
              const scoreColor = score >= 0.75 ? '#EF4444' : score >= 0.45 ? '#F59E0B' : '#38B2AC'
              return (
                <tr key={i} className="border-t border-[rgba(163,177,198,0.2)] hover:bg-[rgba(163,177,198,0.04)] transition-colors">
                  <td className="py-2.5 pr-4 text-neu-muted font-semibold">{i + 1}</td>
                  <td className="py-2.5 pr-4 font-semibold text-neu-fg">{s.supplier_name}</td>
                  <td className="py-2.5 pr-4 text-neu-muted">{s.country ?? '—'}</td>
                  <td className="py-2.5 pr-4 text-neu-muted">{s.category ?? '—'}</td>
                  <td className="py-2.5 pr-4 font-bold font-display" style={{ color: scoreColor }}>
                    {score.toFixed(3)}
                  </td>
                  <td className={`py-2.5 font-semibold text-[0.72rem] uppercase ${decColor(s.decision)}`}>
                    {s.decision ?? '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function PortfolioDashboard() {
  const [data,        setData]        = useState(null)
  const [homeCountry, setHomeCountry] = useState('')
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [portRes, profRes] = await Promise.all([
        apiPortfolio(),
        apiGetProfile().catch(() => ({ data: {} })),
      ])
      setData(portRes.data)
      setHomeCountry((profRes.data?.country ?? '').toUpperCase().trim())
    } catch {
      setError('Could not load portfolio. Run Supplier Analysis on at least one supplier first.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="neu-card p-8 text-neu-muted text-sm animate-pulse">Loading portfolio…</div>
      </div>
    )
  }

  const kpis = data?.summary ?? {}
  const total      = kpis.total_analyzed    ?? 0
  const blocked    = kpis.blocked           ?? 0
  const reqApproval= kpis.requires_approval ?? 0
  const approved   = kpis.approved          ?? 0
  const avgScore   = kpis.avg_risk_score    ?? null
  const highRisk   = kpis.high_risk_count   ?? 0

  const suppliers      = data?.suppliers        ?? []
  const gateBreakdown  = data?.gate_breakdown   ?? []
  const countryRisk    = data?.country_risk      ?? []
  const categoryRisk   = data?.category_risk    ?? []

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-extrabold text-neu-fg tracking-tight mb-1">Portfolio Dashboard</h1>
        <p className="text-[0.85rem] text-neu-muted">
          Aggregate risk intelligence across your entire supplier portfolio.
        </p>
      </div>

      {error && (
        <div className="neu-well p-4 rounded-neu-sm mb-5 text-[0.82rem] text-neu-muted">{error}</div>
      )}

      {!error && total === 0 && (
        <div className="neu-card p-12 text-center">
          <p className="text-neu-muted text-[0.9rem]">No analysed suppliers yet.</p>
          <p className="text-[0.78rem] text-[#A0AEC0] mt-1">Run Supplier Analysis to populate this dashboard.</p>
        </div>
      )}

      {total > 0 && (
        <>
          {/* KPI Row — sits above the sticky map */}
          <div className="relative z-10 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
            <KpiCard value={total}                    label="Total Analysed"      />
            <KpiCard value={blocked}                  label="Blocked"             color="text-neu-risk-hi" sub={pct(blocked, total)} />
            <KpiCard value={reqApproval}              label="Needs Approval"      color="text-neu-risk-md" sub={pct(reqApproval, total)} />
            <KpiCard value={approved}                 label="Approved"            color="text-neu-teal"    sub={pct(approved, total)} />
            <KpiCard value={avgScore !== null ? avgScore.toFixed(3) : '—'} label="Avg Risk Score"  color="text-neu-accent" />
            <KpiCard value={highRisk}                 label="High Risk (≥0.75)"   color="text-neu-risk-hi" sub={pct(highRisk, total)} />
          </div>

          {/* ── World Map — sticky, fades into background on scroll ── */}
          <SupplierWorldMap suppliers={suppliers} homeCountry={homeCountry} />

          {/* Charts — positioned above the sticky map (z-index > 0) */}
          <div className="relative z-10 mt-4 space-y-4">
            {/* Charts row 1 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ChartCard title="Gate Decision Distribution" subtitle="Proportion of approved, blocked, and conditional suppliers">
                <GateDonut data={gateBreakdown} />
              </ChartCard>
              <ChartCard title="Risk Score Distribution" subtitle="Number of suppliers in each risk band">
                <ScoreHistogram data={suppliers} />
              </ChartCard>
            </div>

            {/* Charts row 2 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ChartCard title="Average Risk by Country" subtitle="Top 10 countries by mean risk score">
                <CountryBar data={countryRisk} />
              </ChartCard>
              <ChartCard title="Average Risk by Category" subtitle="Mean risk score per supplier category">
                <CategoryBar data={categoryRisk} />
              </ChartCard>
            </div>

            {/* Top-10 table */}
            <TopRiskTable suppliers={suppliers} />
          </div>
        </>
      )}
    </div>
  )
}
