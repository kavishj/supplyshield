import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  apiGetSuppliers, apiSaveSupplier, apiDeleteSupplier,
  apiExcelUpload, getTemplateUrl, apiAnalyze,
} from '../api/bff'
import NeuButton from '../components/ui/NeuButton'
import NeuInput  from '../components/ui/NeuInput'
import SearchAutocomplete, { saveHistory } from '../components/ui/SearchAutocomplete'
import { useToast } from '../contexts/ToastContext'

// ── Constants ─────────────────────────────────────────────────────────────────
const CATEGORIES = [
  'Raw Materials', 'Components & Parts', 'Finished Goods', 'Packaging',
  'Chemicals & Compounds', 'Textiles & Fabrics', 'Electronics & Semiconductors',
  'Machinery & Equipment', 'Logistics & Shipping', 'Software & Technology',
  'Professional Services', 'Other',
]
const CRITICALITY = [
  'Critical — production stops without this supplier',
  'High — significant disruption if unavailable',
  'Medium — manageable with workarounds',
  'Low — easily replaceable',
]
const TIER_OPTIONS = ['Tier 1', 'Tier 2', 'Tier 3']
const FIN_HEALTH   = ['Good', 'Fair', 'Poor']

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

const CRIT_COLORS = {
  Critical: { bg: 'bg-[#FEF2F2]', text: 'text-neu-risk-hi',  ring: 'shadow-[0_0_0_1px_#EF4444]' },
  High:     { bg: 'bg-[#FFFBEB]', text: 'text-neu-risk-md',  ring: 'shadow-[0_0_0_1px_#F59E0B]' },
  Medium:   { bg: 'bg-[#EFF6FF]', text: 'text-neu-accent',   ring: 'shadow-[0_0_0_1px_#6C63FF]' },
  Low:      { bg: 'bg-[#F0FDF4]', text: 'text-neu-teal',     ring: 'shadow-[0_0_0_1px_#38B2AC]' },
}

// ── Scheduled screener helpers ─────────────────────────────────────────────────
const SCHED_KEY = 'ss-screener-schedule'
const DEFAULT_SCHED = { enabled: false, interval: 'weekly', includeSummary: false }

function readSched() {
  try { return { ...DEFAULT_SCHED, ...JSON.parse(localStorage.getItem(SCHED_KEY) || '{}') } }
  catch { return { ...DEFAULT_SCHED } }
}
function writeSched(cfg) { localStorage.setItem(SCHED_KEY, JSON.stringify(cfg)) }
function addInterval(interval, from = new Date()) {
  const d    = new Date(from)
  const days = interval === 'daily' ? 1 : interval === 'weekly' ? 7 : 30
  d.setDate(d.getDate() + days)
  return d.toISOString()
}
function timeUntil(isoStr) {
  if (!isoStr) return null
  const ms = new Date(isoStr) - Date.now()
  if (ms <= 0) return 'now'
  const d = Math.floor(ms / 86400000)
  const h = Math.floor((ms % 86400000) / 3600000)
  return d > 0 ? `${d}d ${h}h` : `${h}h`
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function daysUntil(dateStr) {
  if (!dateStr) return null
  return Math.ceil((new Date(dateStr) - new Date()) / 86400000)
}

function NeuSelect({ label, value, onChange, options, placeholder, className = '' }) {
  return (
    <div className={`mb-4 ${className}`}>
      {label && <label className="block mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.9px] text-neu-muted">{label}</label>}
      <select value={value} onChange={e => onChange(e.target.value)} className="neu-input appearance-none cursor-pointer">
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )
}

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ value, label, color = 'text-neu-accent' }) {
  return (
    <div className="neu-card-sm p-4 text-center">
      <div className={`font-display text-2xl font-extrabold ${color} leading-none mb-1`}>{value}</div>
      <div className="text-[0.68rem] text-neu-muted uppercase tracking-wide">{label}</div>
    </div>
  )
}

// ── Supplier card (revamped) ───────────────────────────────────────────────────
function SupplierCard({ s, onAnalyze, onDelete, onRefresh }) {
  const toast   = useToast()
  const critKey = s.criticality?.split(' ')[0] ?? 'Medium'
  const colors  = CRIT_COLORS[critKey] ?? CRIT_COLORS.Medium
  const days    = daysUntil(s.contract_expiry)

  const [open,    setOpen]    = useState(false)
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState(null)
  const [saving,  setSaving]  = useState(false)
  const [confirm, setConfirm] = useState(false)

  function startEdit() {
    setEditForm({
      name:                  s.name,
      country:               s.country              ?? '',
      what_they_supply:      s.what_they_supply      ?? '',
      criticality:           s.criticality           ?? CRITICALITY[0],
      category:              s.category              ?? CATEGORIES[0],
      annual_spend_usd:      s.annual_spend_usd      ?? '',
      spend_percentage:      s.spend_percentage      ?? '',
      contract_expiry:       s.contract_expiry       ?? '',
      tier_level:            s.tier_level            ?? '',
      sole_source:           Boolean(s.sole_source),
      on_time_delivery_rate: s.on_time_delivery_rate ?? '',
      years_in_relationship: s.years_in_relationship ?? '',
      financial_health:      s.financial_health      ?? '',
      order_fill_rate:       s.order_fill_rate       ?? '',
      audit_pass_rate:       s.audit_pass_rate       ?? '',
      improvement_index:     s.improvement_index     ?? '',
      disruption_frequency:  s.disruption_frequency  ?? '',
      lead_time_variability: s.lead_time_variability ?? '',
      cyber_posture:         s.cyber_posture         ?? '',
      inventory_buffer_days: s.inventory_buffer_days ?? '',
      has_rto_defined:       Boolean(s.has_rto_defined),
      notes:                 s.notes                 ?? '',
    })
    setEditing(true)
    setOpen(true)
  }

  const ef = k => e => setEditForm(p => ({ ...p, [k]: e.target.value }))
  const es = k => v => setEditForm(p => ({ ...p, [k]: v }))

  async function handleSave() {
    setSaving(true)
    try {
      await apiSaveSupplier({
        ...editForm,
        country:               editForm.country.toUpperCase().trim(),
        annual_spend_usd:      editForm.annual_spend_usd      ? parseFloat(editForm.annual_spend_usd)      : null,
        spend_percentage:      editForm.spend_percentage      ? parseFloat(editForm.spend_percentage)      : null,
        on_time_delivery_rate: editForm.on_time_delivery_rate ? parseFloat(editForm.on_time_delivery_rate) : null,
        years_in_relationship: editForm.years_in_relationship ? parseInt(editForm.years_in_relationship)   : null,
        tier_level:       editForm.tier_level       || null,
        financial_health: editForm.financial_health || null,
        contract_expiry:  editForm.contract_expiry  || null,
        notes:            editForm.notes?.trim()    || null,
        order_fill_rate:       editForm.order_fill_rate      ? parseFloat(editForm.order_fill_rate)      : null,
        audit_pass_rate:       editForm.audit_pass_rate      ? parseFloat(editForm.audit_pass_rate)      : null,
        improvement_index:     editForm.improvement_index    ? parseFloat(editForm.improvement_index)    : null,
        disruption_frequency:  editForm.disruption_frequency ? parseInt(editForm.disruption_frequency)   : null,
        lead_time_variability: editForm.lead_time_variability || null,
        cyber_posture:         editForm.cyber_posture        || null,
        inventory_buffer_days: editForm.inventory_buffer_days ? parseInt(editForm.inventory_buffer_days) : null,
        has_rto_defined:       editForm.has_rto_defined,
      })
      toast('Supplier updated successfully.', 'success')
      setEditing(false)
      onRefresh?.()
    } catch {
      toast('Update failed. Please try again.', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    await onDelete(s.id)
    setConfirm(false)
  }

  return (
    <div className="neu-card-sm overflow-hidden">

      {/* ── Collapsed header (always visible) ── */}
      <div className="p-4 flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Name + badges */}
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="font-semibold text-[0.95rem] text-neu-fg truncate">{s.name}</span>
            <span className={`text-[0.63rem] font-bold px-2 py-0.5 rounded-full ${colors.bg} ${colors.text} ${colors.ring}`}>
              {critKey}
            </span>
            {s.tier_level && (
              <span className="text-[0.62rem] font-semibold text-neu-muted shadow-neu-in-sm px-2 py-0.5 rounded-full">
                {s.tier_level}
              </span>
            )}
          </div>

          {/* Meta row — country · what they supply */}
          <p className="text-[0.78rem] text-neu-muted leading-relaxed truncate">
            {[s.country, s.what_they_supply].filter(Boolean).join(' · ')}
          </p>

          {/* Contract expiry warning */}
          {days !== null && days <= 90 && (
            <p className={`text-[0.72rem] font-semibold mt-1 ${days <= 30 ? 'text-neu-risk-hi' : 'text-neu-risk-md'}`}>
              ⚠ Contract expires in {days} day{days !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <NeuButton
            fullWidth={false} className="!w-24 !py-1.5 !text-[0.75rem]"
            onClick={() => onAnalyze(s)}
          >
            Analyze
          </NeuButton>
          <button
            onClick={() => { setOpen(v => !v); if (editing) setEditing(false) }}
            title={open ? 'Collapse' : 'Expand details'}
            className={`w-8 h-8 rounded-neu-sm flex items-center justify-center text-[0.72rem] font-bold
              text-neu-muted hover:text-neu-fg transition-all duration-200
              ${open ? 'shadow-neu-in' : 'shadow-neu-out-sm hover:shadow-neu-out'}`}
          >
            {open ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {/* ── Expanded: details view ── */}
      {open && !editing && (
        <div className="px-5 pb-5 border-t border-[rgba(163,177,198,0.15)] animate-fade-in">

          {/* Mini stat grid */}
          {(s.annual_spend_usd || s.spend_percentage || s.on_time_delivery_rate || s.years_in_relationship) && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mt-4 mb-3">
              {s.annual_spend_usd && (
                <div className="neu-well px-3 py-2 rounded-neu-sm text-center">
                  <p className="text-[0.6rem] text-neu-muted uppercase tracking-wide mb-0.5">Annual Spend</p>
                  <p className="text-[0.85rem] font-bold text-neu-fg">${Number(s.annual_spend_usd).toLocaleString()}</p>
                </div>
              )}
              {s.spend_percentage && (
                <div className="neu-well px-3 py-2 rounded-neu-sm text-center">
                  <p className="text-[0.6rem] text-neu-muted uppercase tracking-wide mb-0.5">Budget %</p>
                  <p className="text-[0.85rem] font-bold text-neu-fg">{Number(s.spend_percentage).toFixed(0)}%</p>
                </div>
              )}
              {s.on_time_delivery_rate && (
                <div className="neu-well px-3 py-2 rounded-neu-sm text-center">
                  <p className="text-[0.6rem] text-neu-muted uppercase tracking-wide mb-0.5">On-Time</p>
                  <p className={`text-[0.85rem] font-bold ${Number(s.on_time_delivery_rate) >= 90 ? 'text-neu-teal' : 'text-neu-risk-md'}`}>
                    {Number(s.on_time_delivery_rate).toFixed(0)}%
                  </p>
                </div>
              )}
              {s.years_in_relationship && (
                <div className="neu-well px-3 py-2 rounded-neu-sm text-center">
                  <p className="text-[0.6rem] text-neu-muted uppercase tracking-wide mb-0.5">Relationship</p>
                  <p className="text-[0.85rem] font-bold text-neu-fg">{s.years_in_relationship}yr</p>
                </div>
              )}
            </div>
          )}

          {/* Tags row */}
          <div className="flex flex-wrap gap-2 mb-3 text-[0.73rem]">
            {s.financial_health && (
              <span className="neu-well px-3 py-1 rounded-full text-neu-muted">
                Financial: <strong className={
                  s.financial_health === 'Good' ? 'text-neu-teal' :
                  s.financial_health === 'Poor' ? 'text-neu-risk-hi' : 'text-neu-risk-md'
                }>{s.financial_health}</strong>
              </span>
            )}
            {Boolean(s.sole_source) && (
              <span className="px-3 py-1 rounded-full text-[0.7rem] font-bold text-neu-risk-md"
                    style={{ background: '#F59E0B22', boxShadow: '0 0 0 1px #F59E0B' }}>
                Sole Source
              </span>
            )}
            {s.contract_expiry && (
              <span className="neu-well px-3 py-1 rounded-full text-neu-muted">
                Expires: <strong className="text-neu-fg">{s.contract_expiry}</strong>
              </span>
            )}
          </div>

          {/* Notes */}
          {s.notes && (
            <div className="neu-well px-4 py-3 rounded-neu-sm mb-4">
              <p className="text-[0.63rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-1">Notes</p>
              <p className="text-[0.78rem] text-neu-fg leading-relaxed">{s.notes}</p>
            </div>
          )}

          {/* Row actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={startEdit}
              className="text-[0.75rem] font-semibold px-4 py-1.5 rounded-neu-sm
                         shadow-neu-out-sm hover:shadow-neu-out text-neu-accent transition-all duration-200"
            >
              ✎ Edit
            </button>

            {confirm ? (
              <div className="flex items-center gap-2">
                <span className="text-[0.75rem] text-neu-risk-hi font-semibold">Remove {s.name}?</span>
                <button onClick={handleDelete}
                  className="text-[0.72rem] text-neu-risk-hi font-semibold px-3 py-1 rounded-lg shadow-neu-in hover:shadow-neu-out transition-all">
                  Yes
                </button>
                <button onClick={() => setConfirm(false)}
                  className="text-[0.72rem] text-neu-muted px-3 py-1 rounded-lg shadow-neu-in hover:shadow-neu-out transition-all">
                  Cancel
                </button>
              </div>
            ) : (
              <button onClick={() => setConfirm(true)}
                className="text-[0.75rem] text-neu-muted font-medium px-4 py-1.5 rounded-neu-sm
                           shadow-neu-out-sm hover:text-neu-risk-hi hover:shadow-neu-out transition-all duration-300">
                Remove
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── Expanded: edit mode ── */}
      {open && editing && editForm && (
        <div className="px-5 pb-5 border-t border-[rgba(163,177,198,0.15)] animate-fade-in">
          <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mt-4 mb-3">
            Edit Supplier
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
            {/* Name is read-only in edit mode — upsert matches by name */}
            <div className="mb-4 opacity-60">
              <label className="block mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.9px] text-neu-muted">
                Supplier Name (read-only)
              </label>
              <input className="neu-input" value={editForm.name} readOnly />
            </div>

            <SearchAutocomplete
              label="Country *"
              value={editForm.country}
              onChange={ef('country')}
              storageKey="ss-supplier-country-history"
              staticOptions={COUNTRIES}
              placeholder="e.g. BANGLADESH"
            />
            <NeuSelect label="Supply Category *"   value={editForm.category}         onChange={es('category')}         options={CATEGORIES} />
            <NeuSelect label="Criticality Level *"  value={editForm.criticality}      onChange={es('criticality')}      options={CRITICALITY} />
            <div className="md:col-span-2">
              <NeuInput label="What do they supply? *" value={editForm.what_they_supply} onChange={ef('what_they_supply')} placeholder="e.g. Raw cotton fabric" />
            </div>
            <NeuInput label="Annual Spend (USD)"    type="number"  value={editForm.annual_spend_usd}      onChange={ef('annual_spend_usd')}      placeholder="e.g. 500000" />
            <NeuInput label="Contract Expiry Date"  type="date"    value={editForm.contract_expiry}       onChange={ef('contract_expiry')} />
            <NeuSelect label="Tier Level"           value={editForm.tier_level}       onChange={es('tier_level')}       options={TIER_OPTIONS} placeholder="Select tier…" />
            <NeuSelect label="Financial Health"     value={editForm.financial_health} onChange={es('financial_health')} options={FIN_HEALTH}   placeholder="Select…" />
            <NeuInput label="On-Time Delivery (%)"  type="number" min="0" max="100"  value={editForm.on_time_delivery_rate} onChange={ef('on_time_delivery_rate')} placeholder="e.g. 95" />
            <NeuInput label="Years in Relationship" type="number" min="0"            value={editForm.years_in_relationship} onChange={ef('years_in_relationship')} placeholder="e.g. 5" />
          </div>

          {/* Sole source checkbox */}
          <label className="flex items-center gap-3 cursor-pointer mb-4">
            <div onClick={() => es('sole_source')(!editForm.sole_source)}
              className={`w-5 h-5 rounded-[6px] flex-shrink-0 flex items-center justify-center cursor-pointer transition-all duration-300
                ${editForm.sole_source ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}>
              {editForm.sole_source && <span className="text-white text-xs font-bold">✓</span>}
            </div>
            <span className="text-[0.85rem] text-neu-fg font-medium">Sole Source Supplier</span>
          </label>

          {/* Performance & Compliance */}
          <div className="mb-4 pt-3 border-t border-[rgba(163,177,198,0.2)]">
            <p className="text-[0.62rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-3">Performance &amp; Compliance</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
              <NeuInput label="Order Fill Rate (%)" type="number" min="0" max="100" value={editForm.order_fill_rate} onChange={ef('order_fill_rate')} placeholder="e.g. 92" />
              <NeuInput label="Audit Pass Rate (%)" type="number" min="0" max="100" value={editForm.audit_pass_rate} onChange={ef('audit_pass_rate')} placeholder="e.g. 85" />
              <NeuInput label="Improvement Index (%)" type="number" min="0" max="100" value={editForm.improvement_index} onChange={ef('improvement_index')} placeholder="e.g. 78" />
              <NeuInput label="Disruptions / Year" type="number" min="0" value={editForm.disruption_frequency} onChange={ef('disruption_frequency')} placeholder="e.g. 2" />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
              <NeuSelect label="LT Variability" value={editForm.lead_time_variability} onChange={es('lead_time_variability')} options={['Low','Medium','High']} placeholder="— select —" />
              <NeuSelect label="Cyber Posture" value={editForm.cyber_posture} onChange={es('cyber_posture')} options={['Good','Fair','Poor']} placeholder="— select —" />
              <NeuInput label="Inventory Buffer (days)" type="number" min="0" value={editForm.inventory_buffer_days} onChange={ef('inventory_buffer_days')} placeholder="e.g. 45" />
              <div className="flex items-center gap-2 pt-5">
                <div onClick={() => es('has_rto_defined')(!editForm.has_rto_defined)}
                  className={`w-5 h-5 rounded-[6px] flex-shrink-0 flex items-center justify-center cursor-pointer transition-all duration-300 ${editForm.has_rto_defined ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}>
                  {editForm.has_rto_defined && <span className="text-white text-xs font-bold">✓</span>}
                </div>
                <span className="text-[0.78rem] text-neu-fg">RTO Defined</span>
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="mb-4">
            <label className="block mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.9px] text-neu-muted">
              Additional Notes
            </label>
            <textarea
              value={editForm.notes}
              onChange={ef('notes')}
              rows={2}
              className="neu-input resize-none"
              placeholder="Any specific terms, dependencies…"
            />
          </div>

          <div className="flex gap-3">
            <NeuButton type="button" loading={saving} onClick={handleSave}>
              Save Changes
            </NeuButton>
            <NeuButton type="button" variant="secondary" onClick={() => setEditing(false)}>
              Cancel
            </NeuButton>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Add Supplier form ──────────────────────────────────────────────────────────
const EMPTY = {
  name: '', country: '', what_they_supply: '',
  criticality: CRITICALITY[0], category: CATEGORIES[0],
  annual_spend_usd: '', contract_expiry: '', tier_level: '',
  sole_source: false, on_time_delivery_rate: '', years_in_relationship: '',
  financial_health: '', notes: '',
}

function AddSupplierForm({ onSaved }) {
  const toast             = useToast()
  const [form, setForm]   = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState('')

  const set    = k => v => setForm(p => ({ ...p, [k]: v }))
  const setInp = k => e => setForm(p => ({ ...p, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name.trim())             { setError('Supplier name is required.'); return }
    if (!form.country.trim())          { setError('Country is required.'); return }
    if (!form.what_they_supply.trim()) { setError('What they supply is required.'); return }
    setSaving(true); setError('')
    try {
      await apiSaveSupplier({
        ...form,
        country:               form.country.toUpperCase().trim(),
        annual_spend_usd:      form.annual_spend_usd      ? parseFloat(form.annual_spend_usd)      : null,
        on_time_delivery_rate: form.on_time_delivery_rate ? parseFloat(form.on_time_delivery_rate) : null,
        years_in_relationship: form.years_in_relationship ? parseInt(form.years_in_relationship)   : null,
        tier_level:       form.tier_level       || null,
        financial_health: form.financial_health || null,
        contract_expiry:  form.contract_expiry  || null,
        notes:            form.notes.trim()     || null,
      })
      saveHistory('ss-supplier-name-history',    form.name.trim())
      if (form.country.trim()) saveHistory('ss-supplier-country-history', form.country.trim().toUpperCase())
      toast(`${form.name.trim()} added to your portfolio.`, 'success')
      setForm(EMPTY)
      onSaved()
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Save failed.')
      toast('Failed to add supplier.', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="neu-card p-6">
      <h3 className="font-display text-[1rem] font-bold text-neu-fg mb-4">Add New Supplier</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
        <SearchAutocomplete
          label="Supplier Name *"
          value={form.name}
          onChange={setInp('name')}
          storageKey="ss-supplier-name-history"
          placeholder="e.g. Dhaka Textile Mills"
        />
        <SearchAutocomplete
          label="Country *"
          value={form.country}
          onChange={setInp('country')}
          storageKey="ss-supplier-country-history"
          staticOptions={COUNTRIES}
          placeholder="e.g. BANGLADESH"
        />
        <NeuSelect label="Supply Category *"   value={form.category}         onChange={set('category')}         options={CATEGORIES} />
        <NeuSelect label="Criticality Level *"  value={form.criticality}      onChange={set('criticality')}      options={CRITICALITY} />
        <div className="md:col-span-2">
          <NeuInput label="What do they supply? *" value={form.what_they_supply} onChange={setInp('what_they_supply')} placeholder="e.g. Raw cotton fabric, 200 GSM" />
        </div>
        <NeuInput label="Annual Spend (USD)"    type="number"  value={form.annual_spend_usd}      onChange={setInp('annual_spend_usd')}      placeholder="e.g. 500000" />
        <NeuInput label="Contract Expiry Date"  type="date"    value={form.contract_expiry}        onChange={setInp('contract_expiry')} />
        <NeuSelect label="Tier Level"           value={form.tier_level}       onChange={set('tier_level')}       options={TIER_OPTIONS} placeholder="Select tier…" />
        <NeuSelect label="Financial Health"     value={form.financial_health} onChange={set('financial_health')} options={FIN_HEALTH}   placeholder="Select…" />
        <NeuInput label="On-Time Delivery Rate (%)" type="number" min="0" max="100" value={form.on_time_delivery_rate} onChange={setInp('on_time_delivery_rate')} placeholder="e.g. 95" />
        <NeuInput label="Years in Relationship" type="number" min="0"             value={form.years_in_relationship} onChange={setInp('years_in_relationship')} placeholder="e.g. 5" />
      </div>

      {/* Sole source checkbox */}
      <label className="flex items-center gap-3 cursor-pointer mb-4">
        <div onClick={() => set('sole_source')(!form.sole_source)}
          className={`w-5 h-5 rounded-[6px] flex-shrink-0 flex items-center justify-center transition-all duration-300 cursor-pointer
            ${form.sole_source ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}>
          {form.sole_source && <span className="text-white text-xs font-bold">✓</span>}
        </div>
        <span className="text-[0.85rem] text-neu-fg font-medium">Sole Source Supplier</span>
      </label>

      <div className="mb-4">
        <label className="block mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.9px] text-neu-muted">Additional Notes</label>
        <textarea
          value={form.notes}
          onChange={setInp('notes')}
          placeholder="Any specific terms, dependencies, or context…"
          rows={2}
          className="neu-input resize-none"
        />
      </div>

      {error && <p className="mb-3 text-[0.78rem] text-neu-risk-hi font-medium neu-well px-4 py-2.5">{error}</p>}

      <NeuButton type="submit" loading={saving}>Add Supplier</NeuButton>
    </form>
  )
}

// ── Scheduled Screener ─────────────────────────────────────────────────────────
function ScheduledScreener({ suppliers }) {
  const toast = useToast()
  const [sched,    setSched]    = useState(readSched)
  const [open,     setOpen]     = useState(false)
  const [running,  setRunning]  = useState(false)
  const [progress, setProgress] = useState({ done: 0, total: 0 })

  // Auto-trigger on mount when suppliers are loaded and schedule is due
  useEffect(() => {
    if (!sched.enabled || !suppliers.length || !sched.nextRun) return
    if (new Date() >= new Date(sched.nextRun)) {
      runScreening()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [suppliers.length])

  function save(updates) {
    const updated = { ...sched, ...updates }
    setSched(updated)
    writeSched(updated)
  }

  async function runScreening() {
    if (running || !suppliers.length) return
    setRunning(true)
    setProgress({ done: 0, total: suppliers.length })
    let done = 0
    for (const s of suppliers) {
      try {
        await apiAnalyze({
          company_name:            s.name,
          country:                 s.country || null,
          geo_concentration:       0.5,
          single_source:           Boolean(s.sole_source),
          lead_time_weeks:         parseFloat(s.lead_time_weeks) || 12,
          include_summary:         sched.includeSummary,
          include_recommendations: false,
        })
      } catch { /* silent per-supplier — don't abort whole batch */ }
      done++
      setProgress({ done, total: suppliers.length })
    }
    const now = new Date().toISOString()
    save({ lastRun: now, lastRunCount: suppliers.length, nextRun: addInterval(sched.interval) })
    setRunning(false)
    toast(`Scheduled screening complete — ${suppliers.length} suppliers analyzed. Check Audit Log for results.`, 'success', 6000)
  }

  function handleToggle() {
    const enabled = !sched.enabled
    save({ enabled, nextRun: enabled ? addInterval(sched.interval) : undefined })
  }

  return (
    <div className="neu-card-sm overflow-hidden mb-6">

      {/* Header */}
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full p-4 flex items-center justify-between hover:bg-[rgba(163,177,198,0.05)] transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-[1.05rem]">⏰</span>
          <div>
            <span className="font-semibold text-[0.88rem] text-neu-fg">Scheduled Screening</span>
            {sched.enabled && sched.nextRun && !running && (
              <span className="text-[0.72rem] text-neu-muted ml-2">
                · Next in {timeUntil(sched.nextRun)} ({sched.interval})
              </span>
            )}
            {!sched.enabled && (
              <span className="text-[0.72rem] text-neu-muted ml-2">· Disabled</span>
            )}
            {running && (
              <span className="text-[0.72rem] text-neu-accent ml-2 animate-pulse">
                · Running… {progress.done}/{progress.total}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {sched.enabled && !running && suppliers.length > 0 && (
            <button
              onClick={e => { e.stopPropagation(); runScreening() }}
              className="text-[0.72rem] font-semibold text-neu-accent hover:underline px-2 py-1 rounded"
            >
              Run Now ↺
            </button>
          )}
          <span className="text-neu-muted text-[0.75rem]">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* Progress bar (shown when running, collapsed or expanded) */}
      {running && (
        <div className="px-5 pb-3">
          <div className="h-1.5 rounded-full shadow-neu-in overflow-hidden">
            <div
              className="h-full bg-neu-accent rounded-full transition-all duration-500"
              style={{ width: `${progress.total > 0 ? (progress.done / progress.total) * 100 : 0}%` }}
            />
          </div>
          <p className="text-[0.68rem] text-neu-muted mt-1 text-right">
            {progress.done} / {progress.total} suppliers
          </p>
        </div>
      )}

      {/* Config panel */}
      {open && (
        <div className="px-5 pb-5 border-t border-[rgba(163,177,198,0.15)] animate-fade-in">
          <div className="mt-4 space-y-4">

            {/* Enable toggle */}
            <label className="flex items-center gap-3 cursor-pointer">
              <div
                onClick={handleToggle}
                className={`w-5 h-5 rounded-[6px] flex-shrink-0 flex items-center justify-center cursor-pointer
                  transition-all duration-300 ${sched.enabled ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}
              >
                {sched.enabled && <span className="text-white text-xs font-bold">✓</span>}
              </div>
              <span className="text-[0.85rem] text-neu-fg font-medium">Enable automatic screening</span>
            </label>

            {/* Interval selector */}
            <div>
              <p className="text-[0.63rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">
                Screening Interval
              </p>
              <div className="flex gap-2">
                {['daily', 'weekly', 'monthly'].map(iv => (
                  <button
                    key={iv}
                    onClick={() => save({
                      interval: iv,
                      nextRun: sched.enabled ? addInterval(iv) : sched.nextRun,
                    })}
                    className={`px-3 py-1.5 text-[0.75rem] font-semibold rounded-neu-sm capitalize transition-all duration-200
                      ${sched.interval === iv
                        ? 'shadow-neu-in text-neu-accent'
                        : 'shadow-neu-out-sm text-neu-muted hover:shadow-neu-out hover:text-neu-fg'}`}
                  >
                    {iv.charAt(0).toUpperCase() + iv.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Include summary toggle */}
            <label className="flex items-center gap-3 cursor-pointer">
              <div
                onClick={() => save({ includeSummary: !sched.includeSummary })}
                className={`w-5 h-5 rounded-[6px] flex-shrink-0 flex items-center justify-center cursor-pointer
                  transition-all duration-300 ${sched.includeSummary ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}
              >
                {sched.includeSummary && <span className="text-white text-xs font-bold">✓</span>}
              </div>
              <span className="text-[0.82rem] text-neu-fg">Include AI Summary (adds ~10s per supplier)</span>
            </label>

            {/* Status info */}
            <div className="neu-well px-4 py-3 rounded-neu-sm space-y-1.5 text-[0.78rem]">
              {sched.lastRun ? (
                <p className="text-neu-muted">
                  Last run: <strong className="text-neu-fg">{new Date(sched.lastRun).toLocaleString()}</strong>
                  {sched.lastRunCount && <span> — {sched.lastRunCount} suppliers</span>}
                </p>
              ) : (
                <p className="text-neu-muted">No screening runs yet.</p>
              )}
              {sched.enabled && sched.nextRun && (
                <p className="text-neu-muted">
                  Next run: <strong className="text-neu-fg">{new Date(sched.nextRun).toLocaleString()}</strong>
                  <span className="text-neu-accent ml-1">({timeUntil(sched.nextRun)})</span>
                </p>
              )}
              {!sched.enabled && (
                <p className="text-neu-muted">Enable above to schedule automatic batch analysis of all onboarded suppliers.</p>
              )}
            </div>

          </div>
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function MySuppliers() {
  const navigate = useNavigate()
  const toast    = useToast()
  const [suppliers, setSuppliers] = useState([])
  const [loading,   setLoading]   = useState(true)
  const [showForm,  setShowForm]  = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')

  const load = useCallback(async () => {
    try {
      const res = await apiGetSuppliers()
      setSuppliers(res.data)
    } catch { /* silent */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    const s = suppliers.find(x => x.id === id)
    await apiDeleteSupplier(id)
    toast(s ? `${s.name} removed.` : 'Supplier removed.', 'info')
    load()
  }

  const handleAnalyze = (s) => {
    navigate('/analysis', {
      state: {
        prefill: {
          company_name:          s.name,
          country:               s.country,
          single_source:         Boolean(s.sole_source),
          lead_time:             s.lead_time || 12,
          order_fill_rate:       s.order_fill_rate       ?? '',
          audit_pass_rate:       s.audit_pass_rate       ?? '',
          improvement_index:     s.improvement_index     ?? '',
          disruption_frequency:  s.disruption_frequency  ?? '',
          lead_time_variability: s.lead_time_variability ?? '',
          cyber_posture:         s.cyber_posture         ?? '',
          inventory_buffer_days: s.inventory_buffer_days ?? '',
          has_rto_defined:       Boolean(s.has_rto_defined),
          financial_health:      s.financial_health      ?? '',
          on_time_delivery_rate: s.on_time_delivery_rate ?? '',
          contract_expiry:       s.contract_expiry       ?? '',
        },
      },
    })
  }

  const handleExcelUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true); setUploadMsg('')
    try {
      const res = await apiExcelUpload(file)
      const d = res.data
      const msg = `${d.saved} supplier${d.saved !== 1 ? 's' : ''} imported.${d.errors?.length ? ` ${d.errors.length} row(s) had errors.` : ''}`
      setUploadMsg(msg)
      toast(msg, d.errors?.length ? 'warn' : 'success')
      load()
    } catch (err) {
      const msg = err.response?.data?.detail ?? 'Upload failed.'
      setUploadMsg(msg)
      toast(msg, 'error')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  // Derived stats
  const total    = suppliers.length
  const critical = suppliers.filter(s => s.criticality?.startsWith('Critical')).length
  const expiring = suppliers.filter(s => { const d = daysUntil(s.contract_expiry); return d !== null && d <= 90 }).length

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="neu-card p-8 text-neu-muted text-sm animate-pulse">Loading suppliers…</div>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Page header */}
      <div className="mb-6">
        <h1 className="font-display text-2xl font-extrabold text-neu-fg tracking-tight mb-1">My Suppliers</h1>
        <p className="text-[0.85rem] text-neu-muted">Manage your portfolio — onboarded suppliers get personalised risk scoring.</p>
      </div>

      {/* Stats row */}
      {total > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <StatCard value={total}    label="Total Suppliers" />
          <StatCard value={critical} label="Critical Suppliers" color="text-neu-risk-hi" />
          <StatCard value={expiring} label="Contracts Expiring (90d)" color={expiring > 0 ? 'text-neu-risk-md' : 'text-neu-teal'} />
        </div>
      )}

      {/* Action bar */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <NeuButton fullWidth={false} className="!w-auto !px-5"
          onClick={() => setShowForm(v => !v)}>
          {showForm ? '− Hide Form' : '+ Add Supplier'}
        </NeuButton>

        <label className="neu-btn-secondary !w-auto !px-5 !py-2.5 cursor-pointer text-[0.9rem]">
          {uploading ? 'Uploading…' : 'Import Excel'}
          <input type="file" accept=".xlsx" className="hidden" onChange={handleExcelUpload} disabled={uploading} />
        </label>

        <a
          href={getTemplateUrl()}
          download
          className="text-[0.78rem] text-neu-accent font-semibold underline underline-offset-2 hover:text-neu-accent-lt transition-colors"
        >
          Download Template
        </a>

        {uploadMsg && (
          <span className={`text-[0.78rem] font-medium ${uploadMsg.includes('failed') ? 'text-neu-risk-hi' : 'text-neu-teal'}`}>
            {uploadMsg}
          </span>
        )}
      </div>

      {/* Scheduled Screener — top, above supplier list */}
      <ScheduledScreener suppliers={suppliers} />

      {/* Add supplier form */}
      {showForm && (
        <div className="mb-6 mt-6">
          <AddSupplierForm onSaved={() => { setShowForm(false); load() }} />
        </div>
      )}

      {/* Supplier list */}
      {suppliers.length === 0 ? (
        <div className="neu-card p-12 text-center">
          <p className="text-neu-muted text-[0.9rem]">No suppliers added yet.</p>
          <p className="text-[0.78rem] text-[#A0AEC0] mt-1">Use the form above or import an Excel file.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {suppliers.map(s => (
            <SupplierCard
              key={s.id}
              s={s}
              onAnalyze={handleAnalyze}
              onDelete={handleDelete}
              onRefresh={load}
            />
          ))}
        </div>
      )}

    </div>
  )
}
