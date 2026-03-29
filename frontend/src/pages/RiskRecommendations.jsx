import { useState, useEffect, useCallback } from 'react'
import {
  apiRiskySuppliers, apiRecommend, apiUpdateActionStatus, apiGeneratePdf,
  apiGetSuppliers, apiGetSupplierAccountStatus, apiCreateSupplierAccount, apiNotifySupplier,
} from '../api/bff'
import NeuButton from '../components/ui/NeuButton'
import { useToast } from '../contexts/ToastContext'

// Map the normalised decision string back to what generate_supplier_pdf expects
const _gateKey = (d) => {
  if (!d) return 'AUTO_APPROVED'
  const u = d.toUpperCase()
  if (u === 'BLOCKED')                          return 'BLOCKED'
  if (u === 'REQUIRES APPROVAL' || u === 'REQUIRES_APPROVAL') return 'REQUIRES_APPROVAL'
  return 'AUTO_APPROVED'
}

const HIGH_THRESHOLD   = 0.65
const MEDIUM_THRESHOLD = 0.40

const riskColor = (score) =>
  score >= HIGH_THRESHOLD ? '#EF4444' : '#F59E0B'

function StatCard({ value, label, color = 'text-neu-accent' }) {
  return (
    <div className="neu-card-sm p-4 text-center">
      <div className={`font-display text-2xl font-extrabold ${color} leading-none mb-1`}>{value}</div>
      <div className="text-[0.65rem] text-neu-muted uppercase tracking-wide">{label}</div>
    </div>
  )
}

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

// ── Notify Modal ─────────────────────────────────────────────────────────────

function NotifyModal({ supplier, riskCat, onClose }) {
  const toast = useToast()

  // Step: 'loading' | 'create-account' | 'compose' | 'sending' | 'done'
  const [step,        setStep]        = useState('loading')
  const [supplierId,  setSupplierId]  = useState(null)
  const [accountData, setAccountData] = useState(null)

  // Create account form
  const [username,    setUsername]    = useState('')
  const [password,    setPassword]    = useState('')
  const [email,       setEmail]       = useState('')
  const [contactName, setContactName] = useState('')
  const [createErr,   setCreateErr]   = useState('')
  const [creating,    setCreating]    = useState(false)

  // Compose notification form
  const [message,    setMessage]    = useState(
    riskCat === 'HIGH'
      ? `Your organisation has been assessed as HIGH RISK. Immediate action is required to maintain your supply relationship with us.`
      : `Your organisation has been flagged as MEDIUM RISK. Please review the action items below and respond promptly.`
  )
  const immediateDefaults = (supplier.immediate_actions ?? []).map(a => a.action ?? a)
  const [immediateText, setImmediateText] = useState(immediateDefaults.join('\n'))
  const [sendErr,  setSendErr]  = useState('')

  // On mount: lookup supplier id then check account
  useEffect(() => {
    const init = async () => {
      try {
        const { data: allSuppliers } = await apiGetSuppliers()
        const match = (allSuppliers.suppliers ?? allSuppliers).find(
          s => s.name?.toLowerCase() === supplier.name?.toLowerCase()
        )
        if (!match) { setStep('create-account'); return }
        setSupplierId(match.id)
        const { data: status } = await apiGetSupplierAccountStatus(match.id)
        if (status.exists) {
          setAccountData(status.account)
          setStep('compose')
        } else {
          setStep('create-account')
        }
      } catch {
        setStep('create-account')
      }
    }
    init()
  }, [supplier.name])

  const handleCreateAccount = async (e) => {
    e.preventDefault()
    if (!supplierId) { setCreateErr('Supplier not found in onboarded list.'); return }
    setCreating(true); setCreateErr('')
    try {
      const { data } = await apiCreateSupplierAccount({
        supplier_id:  supplierId,
        username,
        password,
        email:        email || null,
        contact_name: contactName || null,
      })
      setAccountData(data)
      setStep('compose')
    } catch (e) {
      setCreateErr(e.response?.data?.detail ?? 'Failed to create account.')
    } finally {
      setCreating(false)
    }
  }

  const handleSend = async () => {
    setSendErr('')
    const sid = accountData?.supplier_id ?? supplierId
    if (!sid) { setSendErr('No supplier account found.'); return }
    setStep('sending')
    try {
      const parseLines = (text) => text.split('\n').map(l => l.trim()).filter(Boolean)
      await apiNotifySupplier({
        supplier_id:       sid,
        risk_category:     riskCat,
        message,
        immediate_actions: parseLines(immediateText).map(a => ({ action: a })),
        long_term_actions: [],
      })
      setStep('done')
      toast(`Notification sent to ${supplier.name}.`, 'success')
    } catch (e) {
      setSendErr(e.response?.data?.detail ?? 'Failed to send notification.')
      setStep('compose')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="neu-card p-6 w-full max-w-lg animate-fade-in max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between mb-5">
          <div>
            <span className="neu-badge mb-2">Notify Supplier</span>
            <h2 className="font-display text-[1.1rem] font-bold text-neu-fg tracking-tight">
              {supplier.name}
            </h2>
            <p className="text-[0.73rem] text-neu-muted mt-0.5">
              {riskCat === 'HIGH' ? '🔴' : '🟡'} {riskCat} RISK
            </p>
          </div>
          <button onClick={onClose} className="text-neu-muted hover:text-neu-fg text-xl leading-none mt-1">×</button>
        </div>

        {/* Loading */}
        {step === 'loading' && (
          <p className="text-neu-muted text-[0.85rem] py-6 text-center">Checking account…</p>
        )}

        {/* Create account */}
        {step === 'create-account' && (
          <form onSubmit={handleCreateAccount}>
            <p className="text-[0.8rem] text-neu-muted mb-4 leading-relaxed">
              This supplier doesn't have a portal account yet. Create one to send notifications.
            </p>
            {[
              { label: 'Username *',     val: username,    set: setUsername,    type: 'text',     ph: 'e.g. acme_supplier' },
              { label: 'Password *',     val: password,    set: setPassword,    type: 'password', ph: 'Strong password' },
              { label: 'Contact name',   val: contactName, set: setContactName, type: 'text',     ph: 'e.g. John Smith' },
              { label: 'Email',          val: email,       set: setEmail,       type: 'email',    ph: 'contact@supplier.com' },
            ].map(({ label, val, set, type, ph }) => (
              <div key={label} className="mb-3">
                <label className="block text-[0.72rem] font-bold uppercase tracking-wider text-neu-muted mb-1">{label}</label>
                <input
                  type={type}
                  value={val}
                  onChange={e => set(e.target.value)}
                  placeholder={ph}
                  className="neu-input text-[0.82rem] w-full"
                  required={label.endsWith('*')}
                />
              </div>
            ))}
            {createErr && <p className="text-[0.75rem] text-neu-risk-hi mb-3">{createErr}</p>}
            <div className="flex gap-2 mt-4">
              <NeuButton type="submit" loading={creating} className="flex-1">
                Create Account & Continue →
              </NeuButton>
            </div>
          </form>
        )}

        {/* Compose */}
        {step === 'compose' && (
          <div>
            {accountData && (
              <div className="neu-well px-4 py-2.5 mb-4 text-[0.75rem] text-neu-muted">
                Account: <span className="font-semibold text-neu-fg">@{accountData.username}</span>
                {accountData.contact_name && ` · ${accountData.contact_name}`}
                {accountData.email && ` · ${accountData.email}`}
              </div>
            )}
            <div className="mb-3">
              <label className="block text-[0.72rem] font-bold uppercase tracking-wider text-neu-muted mb-1">Message</label>
              <textarea
                rows={3}
                value={message}
                onChange={e => setMessage(e.target.value)}
                className="neu-input text-[0.82rem] w-full resize-none"
              />
            </div>
            <div className="mb-3">
              <label className="block text-[0.72rem] font-bold uppercase tracking-wider text-red-400 mb-1">
                Immediate Actions (one per line)
              </label>
              <textarea
                rows={4}
                value={immediateText}
                onChange={e => setImmediateText(e.target.value)}
                placeholder="Each action on a new line…"
                className="neu-input text-[0.8rem] w-full resize-none"
              />
            </div>
            {sendErr && <p className="text-[0.75rem] text-neu-risk-hi mb-3">{sendErr}</p>}
            <NeuButton onClick={handleSend}>
              Send Notification →
            </NeuButton>
          </div>
        )}

        {/* Sending */}
        {step === 'sending' && (
          <p className="text-neu-muted text-[0.85rem] py-6 text-center">Sending…</p>
        )}

        {/* Done */}
        {step === 'done' && (
          <div className="text-center py-6">
            <p className="text-[1.5rem] mb-2">✅</p>
            <p className="font-semibold text-neu-fg text-[0.9rem]">Notification sent!</p>
            <p className="text-neu-muted text-[0.78rem] mt-1 mb-4">
              {supplier.name} will see it the next time they log in.
            </p>
            <button onClick={onClose} className="neu-btn px-6 py-2 text-[0.82rem]">Close</button>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────

function SupplierRecsCard({ supplier, onRegenerate }) {
  const score     = supplier.last_score ?? 0
  const riskCat   = score >= HIGH_THRESHOLD ? 'HIGH' : 'MEDIUM'
  const color     = riskColor(score)
  const hasRecs   = Boolean(supplier.immediate_actions?.length)
  const [actionStatus, setActionStatus] = useState(supplier.action_status ?? {})
  const [genLoading,   setGenLoading]   = useState(false)
  const [pdfLoading,   setPdfLoading]   = useState(false)
  const [open,         setOpen]         = useState(false)
  const [showNotify,   setShowNotify]   = useState(false)

  const totalActions    = (supplier.immediate_actions?.length ?? 0) + (supplier.long_term_actions?.length ?? 0)
  const completedActions = Object.values(actionStatus).filter(Boolean).length

  const handleToggle = (id, val) => setActionStatus(prev => ({ ...prev, [id]: val }))

  const handleGenerate = async () => {
    setGenLoading(true)
    try {
      await onRegenerate(supplier)
    } finally {
      setGenLoading(false)
    }
  }

  const handlePdf = async (e) => {
    e.stopPropagation()
    setPdfLoading(true)
    try {
      const payload = {
        company_name:     supplier.name,
        country:          supplier.country ?? 'N/A',
        gate_decision:    _gateKey(supplier.last_decision),
        risk_score:       score,
        risk_category:    riskCat,
        ofac_status:      'N/A',
        ofac_matches:     0,
        records_searched: 18708,
        risk_components:  {},
        recommendation:   riskCat === 'HIGH'
          ? 'Immediate escalation and mitigation required.'
          : 'Procurement approval and risk review required.',
        recommendations: {
          immediate_actions: supplier.immediate_actions ?? [],
          long_term_actions: supplier.long_term_actions ?? [],
          web_sources:       supplier.web_sources       ?? [],
          model:             'SupplyShield AI',
          generated_at:      supplier.generated_at      ?? '',
        },
      }
      const blob = await apiGeneratePdf(payload)
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = `SupplyShield_${supplier.name.replace(/ /g, '_')}_Recommendations_${new Date().toISOString().slice(0,10)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch { /* silent */ }
    finally { setPdfLoading(false) }
  }

  return (
    <>
    {showNotify && (
      <NotifyModal
        supplier={supplier}
        riskCat={riskCat}
        onClose={() => setShowNotify(false)}
      />
    )}
    <div className="neu-card-sm overflow-hidden">
      {/* Header — always visible */}
      <button className="w-full p-4 flex items-center justify-between gap-4 text-left hover:bg-[rgba(163,177,198,0.05)] transition-colors"
              onClick={() => setOpen(v => !v)}>
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-[1.1rem]">{riskCat === 'HIGH' ? '🔴' : '🟡'}</span>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-[0.92rem] text-neu-fg">{supplier.name}</span>
              <span className="text-[0.62rem] font-bold px-2 py-0.5 rounded-full"
                    style={{ color, background: `${color}22`, boxShadow: `0 0 0 1px ${color}` }}>
                {riskCat}
              </span>
              {hasRecs && totalActions > 0 && (
                <span className="text-[0.62rem] font-semibold text-neu-teal">
                  {completedActions}/{totalActions} done
                </span>
              )}
            </div>
            <p className="text-[0.72rem] text-neu-muted mt-0.5">
              Score: <strong style={{ color }}>{score.toFixed(3)}</strong>
              {supplier.country && ` · ${supplier.country}`}
              {supplier.category && ` · ${supplier.category}`}
              {hasRecs && supplier.generated_at && ` · Recs: ${supplier.generated_at.slice(0,16)}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <NeuButton fullWidth={false} variant={hasRecs ? 'secondary' : 'primary'}
                     className="!w-28 !py-1.5 !text-[0.75rem]"
                     loading={genLoading}
                     onClick={(e) => { e.stopPropagation(); handleGenerate() }}>
            {hasRecs ? 'Regenerate' : 'Generate'}
          </NeuButton>
          {hasRecs && (
            <NeuButton fullWidth={false} variant="secondary"
                       className="!w-32 !py-1.5 !text-[0.75rem]"
                       loading={pdfLoading}
                       onClick={handlePdf}>
              ↓ PDF Report
            </NeuButton>
          )}
          <button
            onClick={(e) => { e.stopPropagation(); setShowNotify(true) }}
            title="Notify supplier"
            className="neu-card-sm px-3 py-1.5 text-[0.75rem] font-semibold text-neu-muted
                       hover:shadow-neu-out hover:text-neu-fg transition-all duration-200"
          >
            Report
          </button>
          <span className="text-neu-muted text-[0.8rem]">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* Expanded content */}
      {open && (
        <div className="px-5 pb-5 animate-fade-in">
          {!hasRecs ? (
            <div className="neu-well p-4 rounded-neu-sm text-center">
              <p className="text-[0.82rem] text-neu-muted">No recommendations generated yet.</p>
              <p className="text-[0.72rem] text-[#A0AEC0] mt-1">Click Generate above to run AI-powered web search.</p>
            </div>
          ) : (
            <>
              {[
                ['Immediate Actions (within 30 days)', supplier.immediate_actions, 'immediate', '#EF4444'],
                ['Long-term Actions (3–18 months)',    supplier.long_term_actions,  'long_term', '#0891B2'],
              ].map(([label, actions, prefix, accent]) => (
                actions?.length > 0 && (
                  <div key={prefix} className="mb-4">
                    <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] mb-2" style={{ color: accent }}>
                      {label}
                    </p>
                    {actions.map((act, i) => (
                      <ActionItem
                        key={i}
                        act={act}
                        actionId={`${prefix}_${i}`}
                        completed={actionStatus[`${prefix}_${i}`] ?? false}
                        supplierName={supplier.name}
                        onToggle={handleToggle}
                      />
                    ))}
                  </div>
                )
              ))}

              {supplier.web_sources?.filter(s => s.url && s.title).length > 0 && (
                <details className="mt-1">
                  <summary className="text-[0.72rem] font-semibold text-neu-accent cursor-pointer mb-2">
                    Intelligence Sources ({supplier.web_sources.filter(s => s.url).length})
                  </summary>
                  <ul className="space-y-1.5 mt-2">
                    {supplier.web_sources.filter(s => s.url && s.title).slice(0,6).map((s, i) => (
                      <li key={i} className="text-[0.74rem]">
                        <strong className="text-neu-fg">{s.title}</strong>
                        {' — '}
                        <a href={s.url} target="_blank" rel="noopener noreferrer"
                           className="text-neu-accent hover:underline">{s.url.slice(0,55)}</a>
                        {s.snippet && <p className="text-[#A0AEC0] text-[0.68rem] mt-0.5">{s.snippet}</p>}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </>
          )}
        </div>
      )}
    </div>
    </>
  )
}

export default function RiskRecommendations() {
  const [suppliers, setSuppliers] = useState([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState('')

  const load = useCallback(async () => {
    try {
      const res = await apiRiskySuppliers()
      setSuppliers(res.data.suppliers ?? [])
    } catch {
      setError('Could not load risky suppliers. Run Supplier Analysis first.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleRegenerate = async (supplier) => {
    const score    = supplier.last_score ?? 0
    const riskCat  = score >= HIGH_THRESHOLD ? 'HIGH' : 'MEDIUM'
    const payload  = {
      supplier_name:   supplier.name,
      country:         supplier.country ?? 'N/A',
      category:        supplier.category ?? 'N/A',
      risk_score:      score,
      risk_category:   riskCat,
      risk_components: {},
      ofac_status:     supplier.last_decision ?? 'CLEAR',
      news_risk:       'NONE',
      news_headlines:  [],
      summary:         '',
      key_concerns:    [],
      gaps:            [],
      company_name_buyer: '',
      company_industry:   '',
      custom_weights:     {},
    }
    try {
      await apiRecommend(payload)
      load()
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Generation failed.')
    }
  }

  // Stats
  const total       = suppliers.length
  const highCount   = suppliers.filter(s => (s.last_score ?? 0) >= HIGH_THRESHOLD).length
  const mediumCount = total - highCount
  const withRecs    = suppliers.filter(s => s.immediate_actions?.length).length
  const totalAct    = suppliers.reduce((acc, s) => acc + (s.immediate_actions?.length ?? 0) + (s.long_term_actions?.length ?? 0), 0)
  const doneAct     = suppliers.reduce((acc, s) => acc + Object.values(s.action_status ?? {}).filter(Boolean).length, 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="neu-card p-8 text-neu-muted text-sm animate-pulse">Loading recommendations…</div>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-extrabold text-neu-fg tracking-tight mb-1">Risk Recommendations</h1>
        <p className="text-[0.85rem] text-neu-muted">
          AI-generated mitigation actions for HIGH and MEDIUM risk suppliers — powered by live web intelligence.
        </p>
      </div>

      {error && (
        <div className="neu-well p-4 rounded-neu-sm mb-5 text-[0.82rem] text-neu-muted">{error}</div>
      )}

      {total > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          <StatCard value={total}             label="Need Attention" />
          <StatCard value={highCount}         label="HIGH Risk"   color="text-neu-risk-hi" />
          <StatCard value={mediumCount}       label="MEDIUM Risk" color="text-neu-risk-md" />
          <StatCard value={`${withRecs}/${total}`} label="With Recs" color="text-neu-teal" />
          <StatCard value={`${doneAct}/${totalAct}`} label="Actions Done" color="text-neu-accent" />
        </div>
      )}

      {suppliers.length === 0 ? (
        <div className="neu-card p-12 text-center">
          <p className="text-neu-muted text-[0.9rem]">No HIGH or MEDIUM risk suppliers found.</p>
          <p className="text-[0.78rem] text-[#A0AEC0] mt-1">Run Supplier Analysis on individual suppliers first.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {suppliers.map(s => (
            <SupplierRecsCard key={s.name} supplier={s} onRegenerate={handleRegenerate} />
          ))}
        </div>
      )}
    </div>
  )
}
