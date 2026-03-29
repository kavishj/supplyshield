import { useState, useEffect, useCallback, useMemo } from 'react'
import { apiAuditLog } from '../api/bff'
import SearchAutocomplete from '../components/ui/SearchAutocomplete'

const DECISION_COLORS = {
  APPROVED:            { bg: '#38B2AC22', border: '#38B2AC', text: '#38B2AC' },
  'REQUIRES APPROVAL': { bg: '#F59E0B22', border: '#F59E0B', text: '#F59E0B' },
  BLOCKED:             { bg: '#EF444422', border: '#EF4444', text: '#EF4444' },
}

const decStyle = (d) =>
  DECISION_COLORS[d] ?? { bg: 'rgba(163,177,198,0.15)', border: '#A0AEC0', text: '#A0AEC0' }

function Badge({ decision }) {
  const s = decStyle(decision)
  return (
    <span className="text-[0.62rem] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide"
          style={{ color: s.text, background: s.bg, boxShadow: `0 0 0 1px ${s.border}` }}>
      {decision ?? 'UNKNOWN'}
    </span>
  )
}

function StatCard({ value, label, color = 'text-neu-accent' }) {
  return (
    <div className="neu-card-sm p-4 text-center">
      <div className={`font-display text-2xl font-extrabold ${color} leading-none mb-1`}>{value}</div>
      <div className="text-[0.65rem] text-neu-muted uppercase tracking-wide">{label}</div>
    </div>
  )
}

function ScoreBar({ score }) {
  const pct   = Math.min(Math.max(score * 100, 0), 100)
  const color = score >= 0.65 ? '#EF4444' : score >= 0.40 ? '#F59E0B' : '#38B2AC'
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 rounded-full shadow-neu-in overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="text-[0.75rem] font-bold font-display" style={{ color }}>
        {score.toFixed(3)}
      </span>
    </div>
  )
}

function downloadCsv(rows) {
  const headers = ['Timestamp', 'Supplier', 'Country', 'Category', 'Score', 'Decision', 'OFAC', 'Summary']
  const lines = [
    headers.join(','),
    ...rows.map(r => [
      r.timestamp ?? '',
      `"${(r.supplier_name ?? '').replace(/"/g, '""')}"`,
      r.country ?? '',
      r.category ?? '',
      r.risk_score ?? '',
      r.decision ?? '',
      r.ofac_status ?? '',
      `"${(r.summary ?? '').replace(/"/g, '""')}"`,
    ].join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `supplyshield-audit-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function AuditLog() {
  const [entries,  setEntries]  = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState('')
  const [search,   setSearch]   = useState('')
  const [decFilter, setDecFilter] = useState('ALL')
  const [expanded,  setExpanded]  = useState(null)

  const load = useCallback(async () => {
    try {
      const res = await apiAuditLog()
      setEntries(res.data.log ?? [])
    } catch {
      setError('Could not load audit log.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const decisions = useMemo(() => {
    const s = new Set(entries.map(e => e.decision).filter(Boolean))
    return ['ALL', ...Array.from(s)]
  }, [entries])

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    return entries.filter(e => {
      if (decFilter !== 'ALL' && e.decision !== decFilter) return false
      if (q) {
        const hay = `${e.supplier_name} ${e.country} ${e.category} ${e.decision}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      return true
    })
  }, [entries, search, decFilter])

  // Stats
  const total       = entries.length
  const blocked     = entries.filter(e => e.decision === 'BLOCKED').length
  const reqApproval = entries.filter(e => e.decision === 'REQUIRES APPROVAL').length
  const approved    = entries.filter(e => e.decision === 'APPROVED').length

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="neu-card p-8 text-neu-muted text-sm animate-pulse">Loading audit log…</div>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-extrabold text-neu-fg tracking-tight mb-1">Audit Log</h1>
        <p className="text-[0.85rem] text-neu-muted">
          Full history of all supplier risk analyses with decisions and AI summaries.
        </p>
      </div>

      {error && (
        <div className="neu-well p-4 rounded-neu-sm mb-5 text-[0.82rem] text-neu-muted">{error}</div>
      )}

      {/* Stats */}
      {total > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <StatCard value={total}       label="Total Analyses"  />
          <StatCard value={blocked}     label="Blocked"         color="text-neu-risk-hi" />
          <StatCard value={reqApproval} label="Needs Approval"  color="text-neu-risk-md" />
          <StatCard value={approved}    label="Approved"        color="text-neu-teal" />
        </div>
      )}

      {/* Filter bar */}
      {total > 0 && (
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {/* Search */}
          <SearchAutocomplete
            value={search}
            onChange={e => setSearch(e.target.value)}
            storageKey="ss-audit-search"
            saveOnBlur={true}
            placeholder="Search supplier, country…"
            className="flex-1 min-w-[180px] max-w-xs !mb-0"
          />

          {/* Decision filter pills */}
          <div className="flex items-center gap-2 flex-wrap">
            {decisions.map(d => {
              const active = decFilter === d
              const s      = d === 'ALL' ? null : decStyle(d)
              return (
                <button
                  key={d}
                  onClick={() => setDecFilter(d)}
                  className={`text-[0.68rem] font-bold px-3 py-1 rounded-full uppercase tracking-wide transition-all duration-200
                    ${active
                      ? 'shadow-neu-in'
                      : 'shadow-neu-out-sm hover:shadow-neu-out'}`}
                  style={active && s ? { color: s.text, boxShadow: `inset 2px 2px 5px rgba(163,177,198,0.6), inset -2px -2px 5px #fff` } : {}}
                >
                  {d === 'ALL' ? 'All' : d}
                </button>
              )
            })}
          </div>

          {/* CSV export */}
          <button
            onClick={() => downloadCsv(filtered)}
            className="ml-auto text-[0.72rem] font-semibold px-3 py-1.5 rounded-neu-sm shadow-neu-out-sm hover:shadow-neu-out text-neu-accent transition-all duration-200"
          >
            ↓ Export CSV
          </button>
        </div>
      )}

      {/* Empty states */}
      {total === 0 && !error && (
        <div className="neu-card p-12 text-center">
          <p className="text-neu-muted text-[0.9rem]">No analyses recorded yet.</p>
          <p className="text-[0.78rem] text-[#A0AEC0] mt-1">Run Supplier Analysis to start building your audit trail.</p>
        </div>
      )}

      {total > 0 && filtered.length === 0 && (
        <div className="neu-well p-6 text-center text-[0.82rem] text-neu-muted rounded-neu-sm">
          No entries match your filter.
        </div>
      )}

      {/* Table */}
      {filtered.length > 0 && (
        <div className="flex flex-col gap-2">
          {filtered.map((entry, i) => {
            const isOpen = expanded === i
            const score  = entry.risk_score ?? 0
            return (
              <div key={i} className="neu-card-sm overflow-hidden">
                {/* Row header — click to expand */}
                <button
                  className="w-full p-4 flex items-center gap-4 text-left hover:bg-[rgba(163,177,198,0.05)] transition-colors"
                  onClick={() => setExpanded(isOpen ? null : i)}
                >
                  {/* Timestamp */}
                  <span className="text-[0.68rem] text-neu-muted whitespace-nowrap flex-shrink-0 w-32">
                    {entry.timestamp ? entry.timestamp.replace('T', ' ').slice(0, 16) : '—'}
                  </span>

                  {/* Supplier name */}
                  <span className="font-semibold text-[0.88rem] text-neu-fg flex-1 min-w-0 truncate">
                    {entry.supplier_name ?? '—'}
                  </span>

                  {/* Country & category */}
                  <span className="text-[0.72rem] text-neu-muted hidden sm:block flex-shrink-0 w-28 truncate">
                    {entry.country ?? '—'}{entry.category ? ` · ${entry.category}` : ''}
                  </span>

                  {/* Score bar */}
                  <div className="hidden md:block flex-shrink-0">
                    <ScoreBar score={score} />
                  </div>

                  {/* Decision badge */}
                  <div className="flex-shrink-0">
                    <Badge decision={entry.decision} />
                  </div>

                  <span className="text-neu-muted text-[0.75rem] flex-shrink-0">{isOpen ? '▲' : '▼'}</span>
                </button>

                {/* Expanded detail */}
                {isOpen && (
                  <div className="px-5 pb-5 animate-fade-in border-t border-[rgba(163,177,198,0.15)]">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">

                      {/* Left: key facts */}
                      <div>
                        <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">Analysis Details</p>
                        <dl className="space-y-1.5">
                          {[
                            ['Supplier',    entry.supplier_name],
                            ['Country',     entry.country],
                            ['Category',    entry.category],
                            ['Risk Score',  score.toFixed(4)],
                            ['OFAC Status', entry.ofac_status],
                            ['Decision',    entry.decision],
                            ['News Risk',   entry.news_risk],
                          ].map(([k, v]) => v != null && (
                            <div key={k} className="flex gap-2 text-[0.78rem]">
                              <dt className="text-neu-muted w-24 flex-shrink-0">{k}</dt>
                              <dd className="text-neu-fg font-medium">{v}</dd>
                            </div>
                          ))}
                        </dl>

                        {/* Key concerns */}
                        {entry.key_concerns?.length > 0 && (
                          <div className="mt-3">
                            <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-1.5">Key Concerns</p>
                            <ul className="space-y-1">
                              {entry.key_concerns.map((c, j) => (
                                <li key={j} className="text-[0.76rem] text-neu-fg flex items-start gap-2">
                                  <span className="text-neu-risk-hi mt-0.5">•</span>{c}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Right: AI summary + risk components */}
                      <div>
                        {entry.summary && (
                          <div className="mb-3">
                            <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-1.5">AI Summary</p>
                            <p className="text-[0.78rem] text-neu-fg leading-relaxed neu-well p-3 rounded-neu-sm">
                              {entry.summary}
                            </p>
                          </div>
                        )}

                        {/* Risk components */}
                        {entry.risk_components && Object.keys(entry.risk_components).length > 0 && (
                          <div>
                            <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">Risk Components</p>
                            <div className="space-y-1.5">
                              {Object.entries(entry.risk_components).map(([k, v]) => {
                                const val = typeof v === 'number' ? v : 0
                                const pct = Math.min(val * 100, 100)
                                const col = val >= 0.65 ? '#EF4444' : val >= 0.40 ? '#F59E0B' : '#38B2AC'
                                return (
                                  <div key={k} className="flex items-center gap-2">
                                    <span className="text-[0.68rem] text-neu-muted w-28 flex-shrink-0 capitalize">
                                      {k.replace(/_/g, ' ')}
                                    </span>
                                    <div className="flex-1 h-1.5 rounded-full shadow-neu-in overflow-hidden">
                                      <div className="h-full rounded-full" style={{ width: `${pct}%`, background: col }} />
                                    </div>
                                    <span className="text-[0.68rem] font-bold" style={{ color: col }}>
                                      {val.toFixed(2)}
                                    </span>
                                  </div>
                                )
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* News headlines */}
                    {entry.news_headlines?.length > 0 && (
                      <div className="mt-4">
                        <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">
                          News Headlines ({entry.news_headlines.length})
                        </p>
                        <ul className="space-y-1">
                          {entry.news_headlines.slice(0, 5).map((h, j) => (
                            <li key={j} className="text-[0.74rem] text-neu-muted flex items-start gap-2">
                              <span className="text-neu-accent mt-0.5 flex-shrink-0">›</span>{h}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {filtered.length > 0 && (
        <p className="text-center text-[0.68rem] text-[#A0AEC0] mt-4">
          Showing {filtered.length} of {total} entries
        </p>
      )}
    </div>
  )
}
