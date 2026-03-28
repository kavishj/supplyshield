import { useState, useEffect } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { apiAnalyze, apiRecommend, apiGetRecommendation, apiUpdateActionStatus, apiGeneratePdf, apiGetSuppliers } from '../api/bff'
import NeuButton from '../components/ui/NeuButton'
import NeuInput  from '../components/ui/NeuInput'
import SearchAutocomplete, { saveHistory } from '../components/ui/SearchAutocomplete'
import { useToast } from '../contexts/ToastContext'

const COUNTRIES = [
  'AFGHANISTAN','ALBANIA','ALGERIA','ANGOLA','ARGENTINA','ARMENIA','AUSTRALIA','AUSTRIA',
  'AZERBAIJAN','BAHRAIN','BANGLADESH','BELARUS','BELGIUM','BOLIVIA','BRAZIL','BULGARIA',
  'CAMBODIA','CAMEROON','CANADA','CHILE','CHINA','COLOMBIA','CONGO','CROATIA',
  'CUBA','CZECH REPUBLIC','DENMARK','ECUADOR','EGYPT','ETHIOPIA','FINLAND','FRANCE',
  'GEORGIA','GERMANY','GHANA','GREECE','GUATEMALA','HONG KONG','HUNGARY','INDIA',
  'INDONESIA','IRAN','IRAQ','IRELAND','ISRAEL','ITALY','IVORY COAST','JAPAN',
  'JORDAN','KAZAKHSTAN','KENYA','KUWAIT','KYRGYZSTAN','LAOS','LATVIA','LEBANON',
  'LIBYA','LITHUANIA','MALAYSIA','MEXICO','MOLDOVA','MONGOLIA','MOROCCO','MOZAMBIQUE',
  'MYANMAR','NEPAL','NETHERLANDS','NEW ZEALAND','NICARAGUA','NIGERIA','NORTH KOREA',
  'NORWAY','OMAN','PAKISTAN','PANAMA','PERU','PHILIPPINES','POLAND','PORTUGAL',
  'QATAR','ROMANIA','RUSSIA','SAUDI ARABIA','SENEGAL','SERBIA','SINGAPORE','SLOVAKIA',
  'SOMALIA','SOUTH AFRICA','SOUTH KOREA','SPAIN','SRI LANKA','SUDAN','SWEDEN',
  'SWITZERLAND','SYRIA','TAIWAN','TAJIKISTAN','TANZANIA','THAILAND','TUNISIA',
  'TURKEY','TURKMENISTAN','UGANDA','UKRAINE','UAE','UNITED KINGDOM','UNITED STATES',
  'UZBEKISTAN','VENEZUELA','VIETNAM','YEMEN','ZAMBIA','ZIMBABWE',
]

// ── Risk colour helpers ───────────────────────────────────────────────────────
const riskColor = (score) =>
  score >= 0.75 ? '#EF4444' : score >= 0.45 ? '#F59E0B' : '#10B981'

const decisionStyle = {
  BLOCKED:           { bg: 'bg-[#FEF2F2]', border: 'border-l-4 border-neu-risk-hi', text: 'text-neu-risk-hi',  label: 'BLOCKED — OFAC Sanctions Match' },
  REQUIRES_APPROVAL: { bg: 'bg-[#FFFBEB]', border: 'border-l-4 border-neu-risk-md', text: 'text-neu-risk-md',  label: 'REQUIRES PROCUREMENT APPROVAL' },
  AUTO_APPROVED:     { bg: 'bg-[#F0FDF4]', border: 'border-l-4 border-neu-teal',    text: 'text-neu-teal',     label: 'AUTO-APPROVED' },
}

// ── Custom SVG gauge ──────────────────────────────────────────────────────────
function RiskGauge({ score }) {
  const R  = 78
  const cx = 110, cy = 105
  // Arc endpoint — always large=0 since we're drawing ≤180° of the semicircle
  const ang = score * Math.PI
  const ex  = cx + R * Math.cos(Math.PI + ang)
  const ey  = cy + R * Math.sin(Math.PI + ang)
  const color = riskColor(score)

  // Needle: from center pivot to a point slightly inside the arc
  const needleLen = R - 10
  const nx = cx + needleLen * Math.cos(Math.PI + ang)
  const ny = cy + needleLen * Math.sin(Math.PI + ang)

  return (
    <svg viewBox="0 0 220 130" className="w-full max-w-[280px] mx-auto">
      {/* Track */}
      <path d={`M ${cx - R} ${cy} A ${R} ${R} 0 0 1 ${cx + R} ${cy}`}
            fill="none" stroke="rgba(163,177,198,0.25)" strokeWidth="16" strokeLinecap="round" />
      {/* Filled arc — large flag always 0 */}
      {score > 0 && (
        <path d={`M ${cx - R} ${cy} A ${R} ${R} 0 0 1 ${ex} ${ey}`}
              fill="none" stroke={color} strokeWidth="16" strokeLinecap="round" />
      )}
      {/* Needle */}
      <line x1={cx} y1={cy} x2={nx} y2={ny}
            stroke={color} strokeWidth="3" strokeLinecap="round" />
      {/* Pivot circle */}
      <circle cx={cx} cy={cy} r="5" fill={color} />
      {/* Score text */}
      <text x={cx} y={cy - 18} textAnchor="middle" fill={color}
            fontSize="28" fontWeight="800" fontFamily="Plus Jakarta Sans, sans-serif">
        {score.toFixed(3)}
      </text>
      {/* Labels */}
      <text x={cx - R - 4} y={cy + 16} textAnchor="middle" fill="#10B981" fontSize="9" fontFamily="DM Sans, sans-serif">LOW</text>
      <text x={cx}          y={cy + 22} textAnchor="middle" fill="#F59E0B" fontSize="9" fontFamily="DM Sans, sans-serif">MED</text>
      <text x={cx + R + 4} y={cy + 16} textAnchor="middle" fill="#EF4444" fontSize="9" fontFamily="DM Sans, sans-serif">HIGH</text>
    </svg>
  )
}

// ── Risk breakdown bar chart ──────────────────────────────────────────────────
const FACTOR_LABELS = {
  geography:     'Geographic Conc.',
  news:          'News Sentiment',
  single_source: 'Single-Source',
  lead_time:     'Lead Time',
}

function BreakdownChart({ components, weights, score }) {
  const data = Object.entries(FACTOR_LABELS).map(([key, label]) => {
    const raw      = components[key] ?? 0
    const w        = weights[key]    ?? 0
    const weighted = raw * w
    return { label, raw, weighted, pct: score > 0 ? weighted / score * 100 : 0 }
  })

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ left: 0, right: 40, top: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(163,177,198,0.3)" horizontal={false} />
        <XAxis type="number" domain={[0, 1]} tick={{ fill: '#6B7280', fontSize: 10 }}
               tickFormatter={v => v.toFixed(1)} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="label" width={110}
               tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: '#E0E5EC', border: 'none', borderRadius: 12,
                          boxShadow: '5px 5px 10px rgb(163,177,198,0.6),-5px -5px 10px rgba(255,255,255,0.5)',
                          fontSize: 12 }}
          formatter={(v, name) => [v.toFixed(4), name === 'raw' ? 'Raw Score' : 'Weighted']}
          cursor={{ fill: 'rgba(163,177,198,0.1)' }}
        />
        <Bar dataKey="raw" name="raw" radius={[0, 4, 4, 0]}>
          {data.map((d, i) => <Cell key={i} fill={riskColor(d.raw)} opacity={0.5} />)}
        </Bar>
        <Bar dataKey="weighted" name="weighted" radius={[0, 4, 4, 0]}>
          {data.map((d, i) => <Cell key={i} fill={riskColor(d.weighted / (Object.values(weights)[0] || 1))} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

// ── Action item ───────────────────────────────────────────────────────────────
function ActionItem({ act, actionId, completed, supplierName, onToggle }) {
  const [toggling, setToggling] = useState(false)
  const accent = actionId.startsWith('immediate') ? '#EF4444' : '#0891B2'

  const handleToggle = async () => {
    setToggling(true)
    await apiUpdateActionStatus(supplierName, actionId, !completed)
    onToggle(actionId, !completed)
    setToggling(false)
  }

  return (
    <div className={`neu-card-sm p-4 mb-2 transition-opacity ${completed ? 'opacity-50' : ''}`}
         style={{ borderLeft: `3px solid ${accent}` }}>
      <div className="flex items-start gap-3">
        <button onClick={handleToggle} disabled={toggling}
          className={`w-5 h-5 rounded-[5px] flex-shrink-0 mt-0.5 flex items-center justify-center
                      transition-all duration-300 ${completed ? 'bg-neu-teal shadow-neu-btn-active' : 'shadow-neu-in'}`}>
          {completed && <span className="text-white text-xs font-bold">✓</span>}
        </button>
        <div className="flex-1 min-w-0">
          <p className={`text-[0.85rem] font-semibold text-neu-fg ${completed ? 'line-through' : ''}`}>
            {act.action}
          </p>
          <p className="text-[0.76rem] text-neu-muted mt-1 leading-relaxed">{act.rationale}</p>
          {(act.timeline || act.priority) && (
            <p className="text-[0.72rem] font-semibold mt-1" style={{ color: accent }}>
              {act.timeline || act.priority}
            </p>
          )}
          {act.source && act.source !== 'Internal Analysis' && (
            <a href={act.source} target="_blank" rel="noopener noreferrer"
               className="text-[0.7rem] text-neu-accent hover:underline mt-1 block truncate">
              {act.source.slice(0, 70)}
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function Tab({ label, active, onClick }) {
  return (
    <button onClick={onClick}
      className={`px-4 py-2 text-[0.78rem] font-semibold rounded-neu-sm transition-all duration-300
        ${active ? 'shadow-neu-in text-neu-accent' : 'text-neu-muted hover:shadow-neu-out-sm hover:text-neu-fg'}`}>
      {label}
    </button>
  )
}

// ── Batch: single supplier row ────────────────────────────────────────────────
function BatchRow({ item }) {
  const { supplier, status, result, error } = item
  const CRIT_COLOR = { Critical: '#EF4444', High: '#F97316', Medium: '#6C63FF', Low: '#38B2AC' }
  const critColor  = CRIT_COLOR[supplier.criticality] ?? '#A0AEC0'

  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-neu-sm transition-opacity
      ${status === 'pending' ? 'opacity-40' : ''}`}
      style={{ background: 'rgba(163,177,198,0.06)' }}>

      {/* Criticality dot */}
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: critColor }} />

      {/* Supplier info */}
      <div className="flex-1 min-w-0">
        <span className="text-[0.85rem] font-semibold text-neu-fg">{supplier.name}</span>
        {supplier.country && (
          <span className="text-[0.72rem] text-neu-muted ml-2">{supplier.country}</span>
        )}
      </div>

      {/* Status */}
      <div className="flex-shrink-0 flex items-center gap-2">
        {status === 'pending' && (
          <span className="text-[0.7rem] text-neu-muted">Pending</span>
        )}
        {status === 'running' && (
          <span className="text-[0.7rem] text-neu-accent font-semibold animate-pulse">Running…</span>
        )}
        {status === 'done' && result && (() => {
          const sc  = result.risk_score ?? 0
          const col = riskColor(sc)
          const dec = result.gate_decision
          const decLabel = dec === 'BLOCKED' ? 'Blocked' : dec === 'REQUIRES_APPROVAL' ? 'Needs Approval' : 'Approved'
          const decColor = dec === 'BLOCKED' ? '#EF4444' : dec === 'REQUIRES_APPROVAL' ? '#F59E0B' : '#38B2AC'
          return (
            <>
              <span className="font-display font-bold text-[0.82rem]" style={{ color: col }}>{sc.toFixed(3)}</span>
              <span className="text-[0.65rem] font-bold px-2 py-0.5 rounded-full"
                    style={{ color: decColor, background: `${decColor}22`, boxShadow: `0 0 0 1px ${decColor}` }}>
                {decLabel}
              </span>
            </>
          )
        })()}
        {status === 'error' && (
          <span className="text-[0.7rem] text-neu-risk-hi font-semibold truncate max-w-[160px]" title={error}>
            Error: {error?.slice(0, 40)}
          </span>
        )}
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function SupplierAnalysis() {
  const location = useLocation()
  const navigate = useNavigate()
  const toast    = useToast()
  const prefill  = location.state?.prefill ?? {}

  // ── Mode ────────────────────────────────────────────────────────────────────
  const [mode, setMode] = useState('single') // 'single' | 'batch'

  // ── Single analysis state ────────────────────────────────────────────────────
  const [form, setForm] = useState({
    company_name:  prefill.company_name  ?? '',
    country:       prefill.country       ?? '',
    geo_conc:      prefill.geo_conc      ?? 0.5,
    single_source: prefill.single_source ?? false,
    lead_time:     prefill.lead_time     ?? 12,
    include_summary: true,
    include_recs:  false,
    w_geo: 38, w_news: 31, w_single: 16, w_lead: 15,
  })
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showWeights, setShowWeights] = useState(() => {
    try { return localStorage.getItem('ss_showWeights') === 'true' } catch { return false }
  })
  const [running,    setRunning]    = useState(false)
  const [result,     setResult]     = useState(null)
  const [error,      setError]      = useState('')
  const [tab,        setTab]        = useState(0)
  const [actionStatus, setActionStatus] = useState({})
  const [genRecs,    setGenRecs]    = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)

  // ── Batch state ──────────────────────────────────────────────────────────────
  const [onboardedSuppliers, setOnboardedSuppliers] = useState([])
  const [loadingSuppliers,   setLoadingSuppliers]   = useState(false)
  const [selectedIds,        setSelectedIds]        = useState(new Set())
  const [batchIncludeSummary, setBatchIncludeSummary] = useState(false)
  const [batchRunning,       setBatchRunning]       = useState(false)
  const [batchProgress,      setBatchProgress]      = useState([])  // [{ supplier, status, result, error }]
  const [batchHighMed,       setBatchHighMed]        = useState(null) // count after run

  // Load onboarded suppliers when batch tab is opened
  useEffect(() => {
    if (mode !== 'batch' || onboardedSuppliers.length > 0) return
    setLoadingSuppliers(true)
    apiGetSuppliers()
      .then(res => {
        const list = Array.isArray(res.data) ? res.data : (res.data.suppliers ?? [])
        setOnboardedSuppliers(list)
        setSelectedIds(new Set(list.map(s => s.id)))
      })
      .catch(() => {})
      .finally(() => setLoadingSuppliers(false))
  }, [mode])

  // ── Single helpers ───────────────────────────────────────────────────────────
  const set = k => v => setForm(p => ({ ...p, [k]: v }))
  const inp = k => e => setForm(p => ({ ...p, [k]: e.target.value }))

  const weightTotal = form.w_geo + form.w_news + form.w_single + form.w_lead
  const useCustomW  = (form.w_geo !== 38 || form.w_news !== 31 || form.w_single !== 16 || form.w_lead !== 15)
  const customWeights = useCustomW
    ? { geography: form.w_geo/100, news: form.w_news/100, single_source: form.w_single/100, lead_time: form.w_lead/100 }
    : null

  const handleRun = async () => {
    if (!form.company_name.trim()) { setError('Company name is required.'); return }
    setError(''); setRunning(true); setResult(null)
    try {
      const payload = {
        company_name:             form.company_name.trim(),
        country:                  form.country.trim().toUpperCase() || null,
        geo_concentration:        parseFloat(form.geo_conc),
        single_source:            form.single_source,
        lead_time_weeks:          parseFloat(form.lead_time),
        include_summary:          form.include_summary,
        include_recommendations:  form.include_recs,
        ...(customWeights ? { custom_weights: customWeights } : {}),
      }
      const res = await apiAnalyze(payload)
      setResult(res.data)
      setActionStatus(res.data.recommendations?.action_status ?? {})
      saveHistory('ss-company-history', form.company_name.trim())
      if (form.country.trim()) saveHistory('ss-country-history', form.country.trim().toUpperCase())
      const sc  = res.data.risk_score ?? 0
      const cat = res.data.risk_category ?? ''
      toast(`Analysis complete — ${cat} risk · Score ${sc.toFixed(3)}`, cat === 'HIGH' ? 'error' : cat === 'MEDIUM' ? 'warn' : 'success')
      setTab(0)
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Pipeline error. Check that all services are running.')
    } finally {
      setRunning(false)
    }
  }

  const handleGenerateRecs = async () => {
    if (!result) return
    setGenRecs(true)
    try {
      const payload = {
        supplier_name:   result.company_name,
        country:         result.country || 'N/A',
        category:        'N/A',
        risk_score:      result.risk_score,
        risk_category:   result.risk_category,
        risk_components: result.risk_components,
        ofac_status:     result.ofac_status,
        news_risk:       result.news_risk ?? 'NONE',
        news_headlines:  result.news_headlines ?? [],
        summary:         result.ai_summary ?? '',
        key_concerns:    result.key_concerns ?? [],
        gaps:            result.gaps ?? [],
        company_name_buyer: '',
        company_industry:   '',
        custom_weights:     customWeights ?? {},
      }
      const res = await apiRecommend(payload)
      setResult(prev => ({ ...prev, recommendations: res.data }))
      setActionStatus(res.data.action_status ?? {})
      toast('Recommendations generated successfully.', 'success')
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Recommendation generation failed.')
      toast('Recommendation generation failed.', 'error')
    } finally {
      setGenRecs(false)
    }
  }

  const handleActionToggle = (id, val) => setActionStatus(prev => ({ ...prev, [id]: val }))

  const handlePdf = async () => {
    setPdfLoading(true)
    try {
      const blob = await apiGeneratePdf(result)
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `SupplyShield_${result.company_name?.replace(/ /g,'_')}_${new Date().toISOString().slice(0,10)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast('PDF report downloaded.', 'info')
    } catch {
      toast('PDF generation failed.', 'error')
    }
    finally { setPdfLoading(false) }
  }

  const gateStyle = result ? (decisionStyle[result.gate_decision] ?? decisionStyle.AUTO_APPROVED) : null
  const TABS = ['OFAC Screening', 'Risk Breakdown', 'AI Summary', 'Recommendations']

  // ── Batch helpers ────────────────────────────────────────────────────────────
  const toggleSelect = (id) => setSelectedIds(prev => {
    const next = new Set(prev)
    next.has(id) ? next.delete(id) : next.add(id)
    return next
  })

  const selectAll   = () => setSelectedIds(new Set(onboardedSuppliers.map(s => s.id)))
  const deselectAll = () => setSelectedIds(new Set())

  const handleRunBatch = async () => {
    const selected = onboardedSuppliers.filter(s => selectedIds.has(s.id))
    if (!selected.length) return

    setBatchRunning(true)
    setBatchHighMed(null)
    const initial = selected.map(s => ({ supplier: s, status: 'pending', result: null, error: null }))
    setBatchProgress(initial)

    let highMedCount = 0

    for (let i = 0; i < selected.length; i++) {
      const s = selected[i]
      setBatchProgress(prev => prev.map((p, idx) => idx === i ? { ...p, status: 'running' } : p))
      try {
        const res = await apiAnalyze({
          company_name:            s.name,
          country:                 s.country || null,
          geo_concentration:       0.5,
          single_source:           !!s.sole_source,
          lead_time_weeks:         parseFloat(s.lead_time_weeks) || 12,
          include_summary:         batchIncludeSummary,
          include_recommendations: false,
        })
        const r = res.data
        if (['HIGH', 'MEDIUM'].includes(r.risk_category)) highMedCount++
        setBatchProgress(prev => prev.map((p, idx) => idx === i ? { ...p, status: 'done', result: r } : p))
      } catch (e) {
        const msg = e.response?.data?.detail ?? 'Pipeline error'
        setBatchProgress(prev => prev.map((p, idx) => idx === i ? { ...p, status: 'error', error: msg } : p))
      }
    }

    setBatchHighMed(highMedCount)
    setBatchRunning(false)
  }

  const batchDone    = batchProgress.filter(p => p.status === 'done').length
  const batchErrors  = batchProgress.filter(p => p.status === 'error').length
  const batchTotal   = batchProgress.length
  const batchFinished = !batchRunning && batchTotal > 0

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <h1 className="font-display text-2xl font-extrabold text-neu-fg tracking-tight mb-1">Supplier Analysis</h1>
        <p className="text-[0.85rem] text-neu-muted">Screen any supplier against OFAC sanctions, geopolitical risk, and adverse news.</p>
      </div>

      {/* Mode toggle */}
      <div className="flex gap-2 mb-5">
        {[['single', 'Single Analysis'], ['batch', 'Batch — My Suppliers']].map(([m, label]) => (
          <button key={m} onClick={() => setMode(m)}
            className={`px-4 py-2 text-[0.78rem] font-semibold rounded-neu-sm transition-all duration-300
              ${mode === m ? 'shadow-neu-in text-neu-accent' : 'text-neu-muted shadow-neu-out-sm hover:shadow-neu-out hover:text-neu-fg'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* ── Single Analysis ─────────────────────────────────────────────────── */}
      {mode === 'single' && (
        <>
          {/* Input form */}
          <div className="neu-card p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 mb-2">
              <SearchAutocomplete
                label="Company Name *"
                value={form.company_name}
                onChange={inp('company_name')}
                storageKey="ss-company-history"
                placeholder="e.g. Shenzhen Electronics Ltd"
              />
              <SearchAutocomplete
                label="Country"
                value={form.country}
                onChange={inp('country')}
                storageKey="ss-country-history"
                staticOptions={COUNTRIES}
                placeholder="e.g. CHINA, GERMANY, IRAN"
              />
            </div>

            {/* Advanced toggle */}
            <button onClick={() => setShowAdvanced(v => !v)}
              className="text-[0.75rem] text-neu-accent font-semibold mb-4 hover:text-neu-accent-lt transition-colors">
              {showAdvanced ? '▲ Hide' : '▼ Advanced'} Risk Parameters
            </button>

            {showAdvanced && (
              <div className="neu-well p-5 rounded-neu-sm mb-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6">
                  <div className="mb-4">
                    <label className="block mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.9px] text-neu-muted">
                      Geographic Concentration: {Number(form.geo_conc).toFixed(2)}
                    </label>
                    <input type="range" min="0" max="1" step="0.05" value={form.geo_conc}
                      onChange={e => set('geo_conc')(parseFloat(e.target.value))}
                      className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
                      style={{ background: `linear-gradient(to right, #6C63FF ${form.geo_conc*100}%, rgba(163,177,198,0.4) ${form.geo_conc*100}%)` }} />
                  </div>
                  <NeuInput label="Lead Time (weeks)" type="number" min="1" max="104"
                            value={form.lead_time} onChange={inp('lead_time')} />
                  <div className="flex items-center gap-3 pt-6">
                    <div onClick={() => set('single_source')(!form.single_source)}
                      className={`w-5 h-5 rounded-[6px] flex-shrink-0 flex items-center justify-center cursor-pointer transition-all duration-300
                        ${form.single_source ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}>
                      {form.single_source && <span className="text-white text-xs font-bold">✓</span>}
                    </div>
                    <span className="text-[0.82rem] text-neu-fg font-medium">Single Source Supplier</span>
                  </div>
                </div>

                {/* Custom weights — nested toggle */}
                <div className="mt-3 pt-3 border-t border-[rgba(163,177,198,0.3)]">
                  <button
                    onClick={() => {
                      const next = !showWeights
                      setShowWeights(next)
                      try { localStorage.setItem('ss_showWeights', String(next)) } catch {}
                    }}
                    className="text-[0.7rem] text-neu-accent font-semibold hover:text-neu-accent-lt transition-colors mb-2">
                    {showWeights ? '▲ Hide' : '▼ Custom'} Risk Weights
                  </button>
                  {showWeights && (
                    <div>
                      <p className="text-[0.62rem] text-neu-muted mb-3">
                        Must sum to 100%
                        {weightTotal !== 100 && <span className="text-neu-risk-md ml-2">· Currently: {weightTotal}%</span>}
                      </p>
                      <div className="grid grid-cols-4 gap-3">
                        {[['w_geo','Geography %'],['w_news','News %'],['w_single','Single-Source %'],['w_lead','Lead Time %']].map(([k,l]) => (
                          <div key={k}>
                            <label className="block mb-1 text-[0.62rem] font-semibold uppercase tracking-wide text-neu-muted">{l}</label>
                            <input type="number" min="0" max="100" step="1" value={form[k]}
                              onChange={e => set(k)(parseInt(e.target.value) || 0)}
                              className="neu-input !py-2 text-center text-sm" />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Options row */}
            <div className="flex flex-wrap items-center gap-6 mb-4">
              {[
                ['include_summary', 'AI Executive Summary'],
                ['include_recs',    'Generate Recommendations'],
              ].map(([k, label]) => (
                <label key={k} className="flex items-center gap-2 cursor-pointer">
                  <div onClick={() => set(k)(!form[k])}
                    className={`w-[18px] h-[18px] rounded-[5px] flex-shrink-0 flex items-center justify-center cursor-pointer transition-all duration-300
                      ${form[k] ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}>
                    {form[k] && <span className="text-white" style={{ fontSize: 10, fontWeight: 800 }}>✓</span>}
                  </div>
                  <span className="text-[0.8rem] text-neu-fg">{label}</span>
                </label>
              ))}
            </div>

            {error && <p className="mb-3 text-[0.78rem] text-neu-risk-hi font-medium neu-well px-4 py-2.5">{error}</p>}

            <NeuButton loading={running} onClick={handleRun}>
              {running ? 'Running agent pipeline…' : 'Run Analysis →'}
            </NeuButton>
          </div>

          {/* ── Results ─────────────────────────────────────────────── */}
          {result && (
            <div className="animate-fade-in">
              <div className="flex flex-wrap gap-3 mb-5">
                {result.agents_log?.map((ag) => (
                  <div key={ag.agent} className="neu-card-sm px-4 py-2.5 flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${ag.status === 'ok' ? 'bg-neu-teal' : 'bg-neu-risk-md'}`} />
                    <span className="text-[0.7rem] font-semibold text-neu-muted">{ag.agent}</span>
                    <span className="text-[0.65rem] text-[#A0AEC0]">{ag.elapsed_ms?.toFixed(0)}ms</span>
                  </div>
                ))}
                <div className="neu-card-sm px-4 py-2.5 text-[0.7rem] text-neu-muted font-semibold">
                  Total: {result.total_elapsed_ms}ms
                </div>
              </div>

              {gateStyle && (
                <div className={`rounded-neu-sm p-5 mb-5 ${gateStyle.bg} ${gateStyle.border}`}>
                  <p className={`font-display text-[1rem] font-bold tracking-wide ${gateStyle.text}`}>{gateStyle.label}</p>
                  <p className="text-[0.82rem] text-neu-muted mt-1">{result.gate_reason}</p>
                  {result.gate_action && <p className="text-[0.78rem] text-neu-muted mt-0.5">{result.gate_action}</p>}
                </div>
              )}

              {(() => {
                const rule50 = result.ofac_50_percent_rule
                const rule50Status = rule50?.status ?? null
                const rule50Color  = rule50Status === 'BLOCKED' ? '#EF4444' : rule50Status === 'MANUAL_REVIEW' ? '#F59E0B' : '#38B2AC'
                const rule50Value  = rule50Status === 'BLOCKED' ? 'BLOCKED' : rule50Status === 'MANUAL_REVIEW' ? 'REVIEW' : rule50Status === 'CLEAR' ? 'CLEAR' : 'N/A'
                const cards = [
                  ['Risk Score',    result.risk_score?.toFixed(3),      riskColor(result.risk_score)],
                  ['Risk Category', result.risk_category,               riskColor(result.risk_score)],
                  ['OFAC Status',   result.ofac_status,                 result.ofac_status === 'CLEAR' ? '#38B2AC' : '#EF4444'],
                  ['SDN Matches',   result.ofac_matches,                result.ofac_matches > 0 ? '#EF4444' : '#38B2AC'],
                  ['News Risk',     result.news_risk ?? 'N/A',          result.news_risk === 'HIGH' ? '#EF4444' : result.news_risk === 'MEDIUM' ? '#F59E0B' : '#38B2AC'],
                  ...(rule50Status ? [['50% Rule', rule50Value, rule50Color]] : []),
                ]
                return (
                  <div className={`grid grid-cols-2 md:grid-cols-${rule50Status ? 6 : 5} gap-3 mb-5`}>
                    {cards.map(([label, value, color]) => (
                      <div key={label} className="neu-card-sm p-3 text-center">
                        <div className="font-display text-lg font-extrabold leading-none mb-1" style={{ color }}>{value}</div>
                        <div className="text-[0.65rem] font-semibold uppercase tracking-wide text-neu-muted">{label}</div>
                      </div>
                    ))}
                  </div>
                )
              })()}

              <div className="neu-card p-6">
                <div className="flex flex-wrap gap-2 mb-5">
                  {TABS.map((t, i) => <Tab key={t} label={t} active={tab === i} onClick={() => setTab(i)} />)}
                </div>

                {tab === 0 && (
                  <div>
                    <div className="grid grid-cols-3 gap-4 mb-5">
                      {[
                        ['Status',           result.ofac_status],
                        ['Matches Found',    result.ofac_matches],
                        ['Records Searched', (result.records_searched ?? 18708).toLocaleString()],
                      ].map(([l, v]) => (
                        <div key={l} className="neu-card-sm p-4 text-center">
                          <div className="font-display text-xl font-extrabold text-neu-accent leading-none mb-1">{v}</div>
                          <div className="text-[0.65rem] text-neu-muted uppercase tracking-wide">{l}</div>
                        </div>
                      ))}
                    </div>
                    {result.matched_entities?.length > 0 ? (
                      <div className="neu-well p-4 rounded-neu-sm">
                        <p className="text-[0.72rem] font-bold uppercase tracking-[1.2px] text-neu-risk-hi mb-3">
                          {result.ofac_matches} entity match(es) on OFAC SDN list
                        </p>
                        <div className="overflow-x-auto">
                          <table className="w-full text-[0.78rem]">
                            <thead>
                              <tr className="text-neu-muted text-[0.65rem] uppercase tracking-wide border-b border-[rgba(163,177,198,0.3)]">
                                {Object.keys(result.matched_entities[0]).map(k => <th key={k} className="text-left py-1.5 pr-4 font-semibold">{k}</th>)}
                              </tr>
                            </thead>
                            <tbody>
                              {result.matched_entities.map((e, i) => (
                                <tr key={i} className="border-b border-[rgba(163,177,198,0.15)]">
                                  {Object.values(e).map((v, j) => <td key={j} className="py-1.5 pr-4 text-neu-fg">{v}</td>)}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ) : (
                      <div className="neu-well p-4 rounded-neu-sm text-center">
                        <p className="text-neu-teal font-semibold text-[0.88rem]">✓ {result.company_name} — CLEAR</p>
                        <p className="text-[0.75rem] text-neu-muted mt-1">No matches in {(result.records_searched ?? 18708).toLocaleString()} OFAC SDN records · 85% fuzzy threshold</p>
                      </div>
                    )}
                    {/* ── OFAC 50% Rule ─────────────────────────────── */}
                    {(() => {
                      const rule = result.ofac_50_percent_rule
                      if (!rule) return null
                      const isBlocked = rule.status === 'BLOCKED'
                      const isManual  = rule.status === 'MANUAL_REVIEW'
                      const isClear   = rule.status === 'CLEAR'
                      return (
                        <div className="mt-4">
                          <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">
                            OFAC 50% Ownership Rule
                          </p>
                          {isBlocked && (
                            <div className="neu-well p-4 rounded-neu-sm border-l-4 border-neu-risk-hi bg-[#FEF2F2]">
                              <p className="text-[0.82rem] font-bold text-neu-risk-hi mb-1">
                                BLOCKED — 50% Rule Triggered
                              </p>
                              <p className="text-[0.76rem] text-neu-muted mb-3">{rule.note}</p>
                              {rule.shareholders?.length > 0 && (
                                <>
                                  <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">
                                    Identified Shareholders
                                  </p>
                                  <div className="overflow-x-auto">
                                    <table className="w-full text-[0.78rem]">
                                      <thead>
                                        <tr className="text-neu-muted text-[0.65rem] uppercase tracking-wide border-b border-[rgba(163,177,198,0.3)]">
                                          <th className="text-left py-1.5 pr-4 font-semibold">Shareholder</th>
                                          <th className="text-left py-1.5 pr-4 font-semibold">Ownership %</th>
                                          <th className="text-left py-1.5 pr-4 font-semibold">OFAC Status</th>
                                          <th className="text-left py-1.5 pr-4 font-semibold">OFAC Match</th>
                                          <th className="text-left py-1.5 pr-4 font-semibold">Program</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {rule.shareholders.map((sh, i) => {
                                          const match = rule.ofac_shareholders?.find(
                                            o => o.shareholder_name === sh.name
                                          )
                                          return (
                                            <tr key={i} className="border-b border-[rgba(163,177,198,0.15)]"
                                                style={match ? { background: 'rgba(239,68,68,0.06)' } : {}}>
                                              <td className="py-1.5 pr-4 text-neu-fg font-medium">{sh.name}</td>
                                              <td className="py-1.5 pr-4 text-neu-fg">{sh.ownership_pct}%</td>
                                              <td className="py-1.5 pr-4">
                                                {match
                                                  ? <span className="text-neu-risk-hi font-bold">SANCTIONED</span>
                                                  : <span className="text-neu-teal font-semibold">CLEAR</span>}
                                              </td>
                                              <td className="py-1.5 pr-4 text-neu-muted text-[0.72rem]">
                                                {match ? `${match.ofac_match} (${match.similarity}%)` : '—'}
                                              </td>
                                              <td className="py-1.5 pr-4 text-neu-muted text-[0.72rem]">
                                                {match?.program ?? '—'}
                                              </td>
                                            </tr>
                                          )
                                        })}
                                      </tbody>
                                    </table>
                                  </div>
                                  <p className="text-[0.72rem] font-bold text-neu-risk-hi mt-3">
                                    Cumulative OFAC-held stake: {rule.cumulative_ofac_pct}%
                                  </p>
                                </>
                              )}
                            </div>
                          )}
                          {isManual && (
                            <div className="neu-well p-4 rounded-neu-sm border-l-4 border-neu-risk-md bg-[#FFFBEB]">
                              <p className="text-[0.82rem] font-semibold text-neu-risk-md">Manual Review Recommended</p>
                              <p className="text-[0.76rem] text-neu-muted mt-1">{rule.note}</p>
                            </div>
                          )}
                          {isClear && (
                            <div className="neu-well p-4 rounded-neu-sm border-l-4 border-neu-teal bg-[#F0FDF4]">
                              <p className="text-[0.82rem] font-semibold text-neu-teal">✓ 50% Rule — CLEAR</p>
                              <p className="text-[0.76rem] text-neu-muted mt-1">{rule.note}</p>
                            </div>
                          )}
                        </div>
                      )
                    })()}

                    {result.news_headlines?.length > 0 && (
                      <div className="mt-4">
                        <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">Live News Intelligence</p>
                        <div className="flex flex-col gap-2">
                          {result.news_headlines.map((h, i) => (
                            <div key={i} className="neu-card-sm px-4 py-2.5 text-[0.8rem] text-neu-fg">{h}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {tab === 1 && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div>
                      <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-3">Score Gauge</p>
                      <RiskGauge score={result.risk_score} />
                      <p className="text-[0.7rem] text-neu-muted text-center mt-2">
                        Approval threshold: {0.75} · Above this requires procurement sign-off
                      </p>
                    </div>
                    <div>
                      <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-3">Component Breakdown</p>
                      <BreakdownChart
                        components={result.risk_components ?? {}}
                        weights={result.risk_weights ?? { geography:0.38,news:0.31,single_source:0.16,lead_time:0.15 }}
                        score={result.risk_score}
                      />
                    </div>
                  </div>
                )}

                {tab === 2 && (
                  <div>
                    {result.ai_summary ? (
                      <>
                        <p className="text-[0.72rem] text-neu-muted mb-3">Generated by {result.summary_model}</p>
                        <div className="neu-well p-5 rounded-neu-sm text-[0.88rem] text-neu-fg leading-relaxed whitespace-pre-line">
                          {result.ai_summary}
                        </div>
                        {result.key_concerns?.length > 0 && (
                          <div className="mt-4">
                            <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">Key Concerns</p>
                            <ul className="space-y-1">
                              {result.key_concerns.map((c, i) => (
                                <li key={i} className="text-[0.82rem] text-neu-fg flex items-start gap-2">
                                  <span className="text-neu-risk-hi mt-0.5">•</span>{c}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="text-neu-muted text-[0.88rem]">Enable AI Executive Summary above and run analysis again.</p>
                    )}
                  </div>
                )}

                {tab === 3 && (
                  <div>
                    {(() => {
                      const recs = result.recommendations
                      if (!recs?.immediate_actions?.length && !recs?.long_term_actions?.length) {
                        if (['HIGH','MEDIUM'].includes(result.risk_category)) {
                          return (
                            <div className="text-center py-4">
                              <p className="text-neu-muted text-[0.88rem] mb-4">No recommendations generated yet.</p>
                              <NeuButton fullWidth={false} className="!w-64" loading={genRecs} onClick={handleGenerateRecs}>
                                Generate Recommendations
                              </NeuButton>
                            </div>
                          )
                        }
                        return <p className="text-neu-teal text-[0.88rem]">This supplier has LOW risk — no mitigation recommendations required.</p>
                      }
                      return (
                        <>
                          <p className="text-[0.72rem] text-neu-muted mb-4">
                            Generated by {recs.model} · {recs.generated_at?.slice(0,16)}
                          </p>
                          {[
                            ['Immediate Actions (within 30 days)', recs.immediate_actions, 'immediate', '#EF4444'],
                            ['Long-term Actions (3–18 months)',    recs.long_term_actions,  'long_term', '#0891B2'],
                          ].map(([label, actions, prefix, accent]) => (
                            actions?.length > 0 && (
                              <div key={prefix} className="mb-5">
                                <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] mb-2" style={{ color: accent }}>{label}</p>
                                {actions.map((act, i) => (
                                  <ActionItem key={i} act={act} actionId={`${prefix}_${i}`}
                                    completed={actionStatus[`${prefix}_${i}`] ?? false}
                                    supplierName={result.company_name} onToggle={handleActionToggle} />
                                ))}
                              </div>
                            )
                          ))}
                          {recs.web_sources?.filter(s => s.url && s.title).length > 0 && (
                            <details className="mt-2">
                              <summary className="text-[0.75rem] font-semibold text-neu-accent cursor-pointer mb-2">Intelligence Sources</summary>
                              <ul className="space-y-1.5 mt-2">
                                {recs.web_sources.filter(s => s.url && s.title).slice(0,8).map((s, i) => (
                                  <li key={i} className="text-[0.76rem]">
                                    <strong className="text-neu-fg">{s.title}</strong>
                                    {' — '}
                                    <a href={s.url} target="_blank" rel="noopener noreferrer"
                                       className="text-neu-accent hover:underline">{s.url.slice(0,60)}</a>
                                  </li>
                                ))}
                              </ul>
                            </details>
                          )}
                          <div className="mt-4 pt-4 border-t border-[rgba(163,177,198,0.3)]">
                            <NeuButton fullWidth={false} variant="secondary" className="!w-56" loading={genRecs} onClick={handleGenerateRecs}>
                              Regenerate Recommendations
                            </NeuButton>
                          </div>
                        </>
                      )
                    })()}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-4 mt-4">
                <NeuButton fullWidth={false} variant="secondary" className="!w-52" loading={pdfLoading} onClick={handlePdf}>
                  Download PDF Report
                </NeuButton>
                <p className="text-[0.74rem] text-neu-muted">
                  Board-ready PDF — risk breakdown, OFAC entities, AI briefing, and recommended actions.
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Batch Analysis ──────────────────────────────────────────────────── */}
      {mode === 'batch' && (
        <div className="neu-card p-6">
          <div className="mb-5">
            <h2 className="font-display text-[1rem] font-bold text-neu-fg mb-1">Batch Screen — My Suppliers</h2>
            <p className="text-[0.82rem] text-neu-muted">
              Select suppliers from your onboarded list to run simultaneously through the full risk pipeline.
              Results are saved to the Audit Log and high/medium risk suppliers appear automatically in Risk Recommendations.
            </p>
          </div>

          {loadingSuppliers && (
            <p className="text-neu-muted text-[0.82rem] animate-pulse py-6 text-center">Loading your suppliers…</p>
          )}

          {!loadingSuppliers && onboardedSuppliers.length === 0 && (
            <div className="neu-well p-6 text-center rounded-neu-sm">
              <p className="text-neu-muted text-[0.88rem]">No onboarded suppliers found.</p>
              <p className="text-[0.76rem] text-[#A0AEC0] mt-1">
                Add suppliers in{' '}
                <Link to="/suppliers" className="text-neu-accent hover:underline">My Suppliers</Link>
                {' '}first.
              </p>
            </div>
          )}

          {!loadingSuppliers && onboardedSuppliers.length > 0 && (
            <>
              {/* Controls row */}
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <button onClick={selectAll}
                  className="text-[0.72rem] font-semibold text-neu-accent hover:underline">
                  Select All
                </button>
                <span className="text-neu-muted text-[0.7rem]">·</span>
                <button onClick={deselectAll}
                  className="text-[0.72rem] font-semibold text-neu-muted hover:text-neu-fg">
                  Deselect All
                </button>
                <span className="text-[0.72rem] text-neu-muted ml-2">
                  {selectedIds.size} of {onboardedSuppliers.length} selected
                </span>

                <div className="ml-auto flex items-center gap-2">
                  <div onClick={() => setBatchIncludeSummary(v => !v)}
                    className={`w-[18px] h-[18px] rounded-[5px] flex-shrink-0 flex items-center justify-center cursor-pointer transition-all duration-300
                      ${batchIncludeSummary ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}>
                    {batchIncludeSummary && <span className="text-white" style={{ fontSize: 10, fontWeight: 800 }}>✓</span>}
                  </div>
                  <span className="text-[0.8rem] text-neu-fg">Include AI Summary</span>
                  <span className="text-[0.7rem] text-neu-muted">(+~15s per supplier)</span>
                </div>
              </div>

              {/* Supplier checklist */}
              <div className="flex flex-col gap-1.5 mb-5 max-h-72 overflow-y-auto pr-1">
                {onboardedSuppliers.map(s => {
                  const CRIT_COLOR = { Critical: '#EF4444', High: '#F97316', Medium: '#6C63FF', Low: '#38B2AC' }
                  const critColor  = CRIT_COLOR[s.criticality] ?? '#A0AEC0'
                  const checked    = selectedIds.has(s.id)
                  return (
                    <label key={s.id}
                      className={`flex items-center gap-3 px-4 py-3 rounded-neu-sm cursor-pointer transition-all
                        hover:bg-[rgba(163,177,198,0.08)] ${checked ? '' : 'opacity-50'}`}>
                      <div onClick={() => toggleSelect(s.id)}
                        className={`w-[18px] h-[18px] rounded-[5px] flex-shrink-0 flex items-center justify-center
                          transition-all duration-200 ${checked ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}>
                        {checked && <span className="text-white" style={{ fontSize: 10, fontWeight: 800 }}>✓</span>}
                      </div>
                      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: critColor }} />
                      <span className="font-semibold text-[0.85rem] text-neu-fg flex-1">{s.name}</span>
                      {s.country && <span className="text-[0.72rem] text-neu-muted">{s.country}</span>}
                      {s.criticality && (
                        <span className="text-[0.62rem] font-bold px-2 py-0.5 rounded-full"
                              style={{ color: critColor, background: `${critColor}22`, boxShadow: `0 0 0 1px ${critColor}` }}>
                          {s.criticality}
                        </span>
                      )}
                    </label>
                  )
                })}
              </div>

              <NeuButton
                loading={batchRunning}
                onClick={handleRunBatch}
                disabled={selectedIds.size === 0 || batchRunning}>
                {batchRunning
                  ? `Running… (${batchDone}/${batchTotal})`
                  : `Run Batch Analysis — ${selectedIds.size} supplier${selectedIds.size !== 1 ? 's' : ''} →`}
              </NeuButton>
            </>
          )}

          {/* Live progress */}
          {batchProgress.length > 0 && (
            <div className="mt-6">
              <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-3">
                Progress — {batchDone}/{batchTotal} complete{batchErrors > 0 ? ` · ${batchErrors} error(s)` : ''}
              </p>

              {/* Progress bar */}
              <div className="w-full h-1.5 rounded-full shadow-neu-in overflow-hidden mb-4">
                <div className="h-full rounded-full bg-neu-accent transition-all duration-500"
                     style={{ width: batchTotal > 0 ? `${(batchDone / batchTotal) * 100}%` : '0%' }} />
              </div>

              <div className="flex flex-col gap-1.5">
                {batchProgress.map((item, i) => (
                  <BatchRow key={i} item={item} />
                ))}
              </div>
            </div>
          )}

          {/* Completion notice */}
          {batchFinished && batchHighMed !== null && (
            <div className="mt-5 neu-well p-4 rounded-neu-sm flex items-center justify-between gap-4">
              <div>
                <p className="text-[0.85rem] font-semibold text-neu-fg">
                  Batch complete — {batchDone} screened
                  {batchHighMed > 0
                    ? `, ${batchHighMed} HIGH/MEDIUM risk supplier${batchHighMed !== 1 ? 's' : ''} added to Risk Recommendations`
                    : ', no HIGH/MEDIUM risk suppliers found'}
                </p>
                {batchErrors > 0 && (
                  <p className="text-[0.75rem] text-neu-risk-md mt-0.5">{batchErrors} supplier(s) failed — check service availability.</p>
                )}
              </div>
              {batchHighMed > 0 && (
                <Link to="/recommendations"
                  className="text-[0.78rem] font-semibold text-neu-accent hover:underline whitespace-nowrap">
                  View Recommendations →
                </Link>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
