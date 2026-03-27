import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiGetProfile, apiSaveProfile } from '../api/bff'
import { useAppStore } from '../stores/appStore'
import NeuInput  from '../components/ui/NeuInput'
import NeuButton from '../components/ui/NeuButton'

const INDUSTRIES = [
  'Automotive', 'Aerospace & Defense', 'Chemicals', 'Consumer Electronics',
  'Energy & Utilities', 'Financial Services', 'Food & Beverage',
  'Healthcare & Pharma', 'Industrial Machinery', 'Information Technology',
  'Logistics & Shipping', 'Medical Devices', 'Mining & Metals', 'Oil & Gas',
  'Retail & E-commerce', 'Semiconductors', 'Telecommunications',
  'Textiles & Apparel', 'Other',
]

const SP_RATINGS = [
  'Not Rated', 'AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-',
  'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-',
  'CCC', 'CC', 'C', 'D',
]

const STEPS = ['Company Identity', 'Business Details', 'Compliance & Risk']

function StepIndicator({ current }) {
  return (
    <div className="flex items-center gap-0 mb-8">
      {STEPS.map((label, i) => {
        const done    = i < current
        const active  = i === current
        return (
          <div key={label} className="flex items-center">
            <div className="flex items-center gap-2">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[0.78rem] font-bold transition-all duration-300
                ${active ? 'bg-neu-accent text-white shadow-neu-out-sm'
                  : done  ? 'shadow-neu-in text-neu-teal'
                  : 'shadow-neu-in text-[#A0AEC0]'}`}>
                {done ? '✓' : i + 1}
              </div>
              <span className={`text-[0.68rem] font-semibold uppercase tracking-[0.8px] hidden sm:block
                ${active ? 'text-neu-fg' : done ? 'text-neu-teal' : 'text-[#A0AEC0]'}`}>
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`w-8 h-px mx-2 transition-colors duration-300
                ${done ? 'bg-neu-teal' : 'bg-[rgba(163,177,198,0.4)]'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

function NeuSelect({ label, value, onChange, options, placeholder }) {
  return (
    <div className="mb-4">
      {label && (
        <label className="block mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.9px] text-neu-muted">
          {label}
        </label>
      )}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="neu-input appearance-none cursor-pointer"
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  )
}

function NeuCheckbox({ label, checked, onChange, helpText }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer group mb-3">
      <div
        onClick={() => onChange(!checked)}
        className={`w-5 h-5 rounded-[6px] flex-shrink-0 mt-0.5 flex items-center justify-center
                    transition-all duration-300 cursor-pointer
                    ${checked ? 'bg-neu-accent shadow-neu-btn-active' : 'shadow-neu-in'}`}
      >
        {checked && <span className="text-white text-xs font-bold">✓</span>}
      </div>
      <div>
        <span className="text-[0.85rem] font-medium text-neu-fg">{label}</span>
        {helpText && <p className="text-[0.72rem] text-neu-muted mt-0.5">{helpText}</p>}
      </div>
    </label>
  )
}

export default function Onboarding() {
  const navigate   = useNavigate()
  const setProfile = useAppStore(s => s.setProfile)
  const [step, setStep]     = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving,  setSaving]  = useState(false)
  const [error,   setError]   = useState('')

  const [form, setForm] = useState({
    business_name: '', country: '', industry: '', contact_email: '',
    tax_id: '', annual_revenue: '', lead_time_weeks: '', num_employees: '',
    iso_certifications: '', anti_bribery_policy: false, labor_law_compliance: false,
    sp_rating: 'Not Rated', products_services: '', address: '',
  })

  useEffect(() => {
    apiGetProfile()
      .then(res => {
        if (res.data && res.data.business_name) {
          setForm(prev => ({ ...prev, ...res.data }))
        }
      })
      .finally(() => setLoading(false))
  }, [])

  const set = (key) => (val) => setForm(prev => ({ ...prev, [key]: val }))
  const setInput = (key) => (e) => setForm(prev => ({ ...prev, [key]: e.target.value }))

  const validateStep = () => {
    if (step === 0) {
      if (!form.business_name.trim()) return 'Company name is required.'
      if (!form.country.trim())       return 'Country is required.'
      if (!form.industry)             return 'Industry is required.'
      if (!form.contact_email.trim()) return 'Contact email is required.'
    }
    return ''
  }

  const handleNext = () => {
    const err = validateStep()
    if (err) { setError(err); return }
    setError('')
    setStep(s => s + 1)
  }

  const handleSubmit = async () => {
    setSaving(true)
    setError('')
    try {
      const payload = {
        ...form,
        annual_revenue:   form.annual_revenue   ? parseFloat(form.annual_revenue)   : null,
        lead_time_weeks:  form.lead_time_weeks  ? parseInt(form.lead_time_weeks)    : null,
        num_employees:    form.num_employees    ? parseInt(form.num_employees)      : null,
      }
      await apiSaveProfile(payload)
      setProfile(payload)
      navigate('/suppliers', { replace: true })
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Failed to save profile.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-neu-base flex items-center justify-center">
        <div className="neu-card p-8 text-neu-muted text-sm animate-pulse">Loading profile…</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neu-base flex flex-col">
      <div className="flex-1 max-w-[860px] mx-auto w-full px-6 py-12">

        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-[1.9rem] font-extrabold text-neu-fg tracking-tight leading-none mb-1">
            Supply<span className="text-neu-accent">Shield</span>
          </h1>
          <p className="text-[0.63rem] font-bold uppercase tracking-[3px] text-neu-accent">
            Company Setup
          </p>
        </div>

        <StepIndicator current={step} />

        <div className="neu-card p-8 animate-fade-in">

          {/* ── Step 0: Company Identity ── */}
          {step === 0 && (
            <div>
              <h2 className="font-display text-xl font-bold text-neu-fg mb-1">Company Identity</h2>
              <p className="text-[0.82rem] text-neu-muted mb-6">Basic information about your organisation.</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
                <NeuInput label="Company Name *" value={form.business_name} onChange={setInput('business_name')} placeholder="e.g. Acme Manufacturing Ltd" />
                <NeuInput label="Country *" value={form.country} onChange={setInput('country')} placeholder="e.g. UNITED STATES" />
                <div className="md:col-span-2">
                  <NeuSelect label="Industry *" value={form.industry} onChange={set('industry')} options={INDUSTRIES} placeholder="Select industry…" />
                </div>
                <NeuInput label="Contact Email *" type="email" value={form.contact_email} onChange={setInput('contact_email')} placeholder="procurement@company.com" />
                <NeuInput label="Tax ID / Registration Number" value={form.tax_id} onChange={setInput('tax_id')} placeholder="Optional" />
                <div className="md:col-span-2">
                  <NeuInput label="Registered Address" value={form.address} onChange={setInput('address')} placeholder="Street, City, Country" />
                </div>
              </div>
            </div>
          )}

          {/* ── Step 1: Business Details ── */}
          {step === 1 && (
            <div>
              <h2 className="font-display text-xl font-bold text-neu-fg mb-1">Business Details</h2>
              <p className="text-[0.82rem] text-neu-muted mb-6">Operational context used to personalise risk scoring.</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
                <NeuInput label="Annual Revenue (USD)" type="number" value={form.annual_revenue} onChange={setInput('annual_revenue')} placeholder="e.g. 50000000" />
                <NeuInput label="Number of Employees" type="number" value={form.num_employees} onChange={setInput('num_employees')} placeholder="e.g. 250" />
                <NeuInput label="Default Lead Time (weeks)" type="number" value={form.lead_time_weeks} onChange={setInput('lead_time_weeks')} placeholder="e.g. 12" />
                <NeuSelect label="S&P Credit Rating" value={form.sp_rating} onChange={set('sp_rating')} options={SP_RATINGS} />
                <div className="md:col-span-2">
                  <NeuInput label="Products / Services Offered" value={form.products_services} onChange={setInput('products_services')} placeholder="Brief description of what your company makes or does" />
                </div>
              </div>
            </div>
          )}

          {/* ── Step 2: Compliance ── */}
          {step === 2 && (
            <div>
              <h2 className="font-display text-xl font-bold text-neu-fg mb-1">Compliance & Risk Profile</h2>
              <p className="text-[0.82rem] text-neu-muted mb-6">Used to contextualise your risk posture and generate accurate recommendations.</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 mb-4">
                <NeuInput
                  label="ISO / Quality Certifications"
                  value={form.iso_certifications}
                  onChange={setInput('iso_certifications')}
                  placeholder="e.g. ISO 9001, ISO 27001, IATF 16949"
                />
              </div>

              <div className="neu-well p-5 rounded-neu-sm mb-4">
                <p className="text-[0.68rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-3">
                  Compliance Policies
                </p>
                <NeuCheckbox
                  label="Anti-Bribery & Corruption Policy"
                  checked={form.anti_bribery_policy}
                  onChange={set('anti_bribery_policy')}
                  helpText="Your organisation has a documented anti-bribery policy in place."
                />
                <NeuCheckbox
                  label="Labour Law Compliance Programme"
                  checked={form.labor_law_compliance}
                  onChange={set('labor_law_compliance')}
                  helpText="Active monitoring of supplier labour practices against local and international law."
                />
              </div>

              {/* Summary preview */}
              {form.business_name && (
                <div className="neu-card-sm p-4 mt-4">
                  <p className="text-[0.65rem] font-bold uppercase tracking-[1.2px] text-neu-muted mb-2">Summary</p>
                  <p className="text-[0.82rem] text-neu-fg font-medium">{form.business_name}</p>
                  <p className="text-[0.76rem] text-neu-muted">{form.industry} · {form.country}</p>
                  {form.contact_email && <p className="text-[0.72rem] text-neu-muted mt-1">{form.contact_email}</p>}
                </div>
              )}
            </div>
          )}

          {/* Error */}
          {error && (
            <p className="mt-4 text-[0.78rem] text-neu-risk-hi font-medium neu-well px-4 py-2.5">
              {error}
            </p>
          )}

          {/* Nav buttons */}
          <div className={`mt-6 flex gap-3 ${step > 0 ? 'justify-between' : 'justify-end'}`}>
            {step > 0 && (
              <NeuButton variant="secondary" fullWidth={false} className="w-32"
                onClick={() => { setError(''); setStep(s => s - 1) }}>
                ← Back
              </NeuButton>
            )}
            {step < STEPS.length - 1 ? (
              <NeuButton fullWidth={false} className="w-40" onClick={handleNext}>
                Next →
              </NeuButton>
            ) : (
              <NeuButton fullWidth={false} className="w-48" loading={saving} onClick={handleSubmit}>
                Save & Continue →
              </NeuButton>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
