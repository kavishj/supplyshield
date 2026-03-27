import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiLogin, apiVerifyOtp, getQrCodeUrl } from '../api/auth'
import { useAuthStore } from '../stores/authStore'
import NeuButton from '../components/ui/NeuButton'
import NeuInput  from '../components/ui/NeuInput'

// ── Sub-components ────────────────────────────────────────────────────────────

function StatCard({ value, label }) {
  return (
    <div className="neu-card-sm p-3.5 transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-neu-out cursor-default">
      <div className="font-display text-[1.45rem] font-extrabold text-neu-accent leading-none mb-1 tracking-tight">
        {value}
      </div>
      <div className="text-[0.67rem] text-neu-muted leading-[1.45]">{label}</div>
    </div>
  )
}

function ValueProp({ icon, title, body }) {
  return (
    <div className="neu-card-sm p-3.5 transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-neu-out cursor-default">
      {/* Icon well — inset circle */}
      <div className="w-8 h-8 rounded-full shadow-neu-in flex items-center justify-center mb-2.5 text-[0.9rem]">
        {icon}
      </div>
      <p className="text-[0.73rem] font-bold text-neu-fg leading-[1.3] mb-1">{title}</p>
      <p className="text-[0.68rem] text-neu-muted leading-[1.5]">{body}</p>
    </div>
  )
}

function CoverageDot() {
  return (
    <span className="w-5 h-5 rounded-full shadow-neu-in flex-shrink-0 flex items-center justify-center">
      <span className="w-[7px] h-[7px] rounded-full bg-neu-accent block" />
    </span>
  )
}

// ── Hero (left column) ────────────────────────────────────────────────────────

function HeroPanel() {
  return (
    <div className="neu-card p-9 animate-fade-in">

      {/* Brand */}
      <h1 className="font-display text-[1.9rem] font-extrabold text-neu-fg tracking-[-1.5px] leading-none mb-1">
        Supply<span className="text-neu-accent">Shield</span>
      </h1>
      <p className="text-[0.63rem] font-bold uppercase tracking-[3px] text-neu-accent mb-4">
        Real-Time Supply Chain Risk Intelligence
      </p>

      {/* Gradient divider */}
      <div
        className="w-11 h-[3px] rounded-full mb-4"
        style={{ background: 'linear-gradient(90deg, #6C63FF, #38B2AC)' }}
      />

      {/* Headline + sub */}
      <h2 className="font-display text-[1.3rem] font-bold text-neu-fg tracking-[-0.4px] leading-[1.42] mb-2.5">
        Know your supplier risk<br />before it becomes your crisis.
      </h2>
      <p className="text-[0.86rem] text-neu-muted leading-[1.72] mb-7">
        A multi-agent AI system that screens every supplier against OFAC sanctions,
        geopolitical risk, and adverse news — delivering a complete risk verdict
        in under 10 seconds.
      </p>

      {/* 2 × 2 stat grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <StatCard value="$210B"  label="Lost in the 2021 semiconductor supply shock" />
        <StatCard value="85%"    label="Fortune 500 with no real-time Tier-2 visibility" />
        <StatCard value="$1–3M"  label="Avg. OFAC fine for one missed sanctions update" />
        <StatCard value="<10s"   label="Full 5-agent risk verdict, start to finish" />
      </div>

      {/* 2 × 2 value props */}
      <div className="grid grid-cols-2 gap-3">
        <ValueProp
          icon="🎯"
          title="Zero-hallucination risk scores"
          body="Deterministic algorithm only — no LLM touches the numbers. Full mathematical traceability on every score."
        />
        <ValueProp
          icon="🛡️"
          title="18,708 OFAC entities, fuzzy-matched"
          body="Catches aliases and transliterations that exact-match tools miss — before a single PO is placed."
        />
        <ValueProp
          icon="🤖"
          title="AI mitigation with live web search"
          body="AI + Serper generates context-aware mitigation actions with cited sources, within 30 days and 18 months."
        />
        <ValueProp
          icon="📊"
          title="Portfolio-level visibility"
          body="Track score trends, detect deteriorating suppliers, and export audit-ready PDF reports."
        />
      </div>
    </div>
  )
}

// ── Step 1 — Credentials ──────────────────────────────────────────────────────

function StepCredentials({ onSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await apiLogin(username, password)
      onSuccess(data.requires_setup)
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      {/* Panel header */}
      <div className="mb-5">
        <span className="neu-badge mb-3">Step 1 of 2</span>
        <h3 className="font-display text-[1.25rem] font-bold text-neu-fg tracking-tight mb-1">
          Sign In
        </h3>
        <p className="text-[0.79rem] text-neu-muted leading-[1.55]">
          Enter your credentials to access the platform.
        </p>
      </div>

      <NeuInput
        label="Username"
        type="text"
        placeholder="Enter username"
        autoComplete="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      <NeuInput
        label="Password"
        type="password"
        placeholder="Enter password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />

      {error && (
        <p className="mb-3 text-[0.78rem] text-neu-risk-hi font-medium neu-well px-4 py-2.5">
          {error}
        </p>
      )}

      <NeuButton type="submit" loading={loading}>
        Continue →
      </NeuButton>

      {/* Coverage */}
      <div className="mt-5 pt-4 border-t border-[rgba(163,177,198,0.3)]">
        <p className="text-[0.6rem] font-bold uppercase tracking-[1.5px] text-neu-muted mb-2.5">
          Platform coverage
        </p>
        {[
          'OFAC SDN list — 18,708 entities, fuzzy-matched',
          '60+ countries with calibrated geopolitical risk scores',
          'Live adverse news — 13 risk terms monitored',
          '8-factor scoring model for onboarded suppliers',
        ].map((item) => (
          <div key={item} className="flex items-center gap-2.5 mb-2">
            <CoverageDot />
            <span className="text-[0.74rem] text-neu-muted leading-[1.4]">{item}</span>
          </div>
        ))}
      </div>
    </form>
  )
}

// ── Step 2 — OTP ──────────────────────────────────────────────────────────────

function StepOTP({ requiresSetup, onBack }) {
  const [code,    setCode]    = useState('')
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate  = useNavigate()

  const handleVerify = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await apiVerifyOtp(code)
      login(data.token)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Invalid code. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleVerify} noValidate>
      {/* Panel header */}
      <div className="mb-5">
        <span className="neu-badge mb-3">
          {requiresSetup ? 'Step 2 of 2 — First Time Setup' : 'Step 2 of 2'}
        </span>
        <h3 className="font-display text-[1.25rem] font-bold text-neu-fg tracking-tight mb-1">
          {requiresSetup ? 'Set Up Authenticator' : 'Two-Factor Authentication'}
        </h3>
        <p className="text-[0.79rem] text-neu-muted leading-[1.55]">
          {requiresSetup
            ? 'Scan the QR code with Google Authenticator or any TOTP app. You only do this once.'
            : 'Enter the 6-digit code from your authenticator app.'}
        </p>
      </div>

      {/* QR code — only shown on first-time setup */}
      {requiresSetup && (
        <div className="flex justify-center mb-4">
          <div className="neu-card-sm p-3 inline-block">
            <img
              src={getQrCodeUrl()}
              alt="TOTP QR code — scan with Google Authenticator"
              width={180}
              height={180}
              className="rounded-xl block"
            />
          </div>
        </div>
      )}

      {/* Instruction block */}
      <div className="neu-well px-4 py-3.5 mb-4 text-[0.79rem] text-neu-muted leading-[1.85]">
        1. Open Google Authenticator<br />
        2. Tap <strong className="text-neu-fg font-semibold">+</strong> → Scan QR code <em>(first time only)</em><br />
        3. Enter the 6-digit code shown in the app
      </div>

      <NeuInput
        label="Authentication Code"
        type="text"
        inputMode="numeric"
        pattern="[0-9]{6}"
        placeholder="000000"
        maxLength={6}
        autoComplete="one-time-code"
        value={code}
        onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
        required
      />

      {error && (
        <p className="mb-3 text-[0.78rem] text-neu-risk-hi font-medium neu-well px-4 py-2.5">
          {error}
        </p>
      )}

      <div className="grid grid-cols-2 gap-3">
        <NeuButton type="button" variant="secondary" onClick={onBack}>
          ← Back
        </NeuButton>
        <NeuButton type="submit" loading={loading}>
          Verify →
        </NeuButton>
      </div>
    </form>
  )
}

// ── Login page ────────────────────────────────────────────────────────────────

export default function Login() {
  const [step,         setStep]         = useState(1)
  const [requiresSetup, setRequiresSetup] = useState(false)

  const handleCredentialsSuccess = (setup) => {
    setRequiresSetup(setup)
    setStep(2)
  }

  const handleBack = () => {
    setStep(1)
    setRequiresSetup(false)
  }

  return (
    <div className="min-h-screen bg-neu-base flex flex-col">
      <main className="flex-1 flex items-center">
        <div className="w-full max-w-[1040px] mx-auto px-6 py-12">

          {/* Two-column grid: hero (wider) | form */}
          <div className="grid grid-cols-1 lg:grid-cols-[11fr_8fr] gap-8 items-start">

            {/* Left — Hero */}
            <HeroPanel />

            {/* Right — Form card (entire card, not just header) */}
            <div
              className="neu-card p-8 animate-fade-in"
              style={{ animationDelay: '80ms' }}
            >
              {step === 1 ? (
                <StepCredentials onSuccess={handleCredentialsSuccess} />
              ) : (
                <StepOTP requiresSetup={requiresSetup} onBack={handleBack} />
              )}
            </div>
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="text-center pb-6 text-[0.67rem] text-[#A0AEC0] tracking-[0.5px]">
        SupplyShield &nbsp;&middot;&nbsp; Microsoft AI Unlocked Hackathon
        &nbsp;&middot;&nbsp; IIT Roorkee &nbsp;&middot;&nbsp; Track 4
      </footer>
    </div>
  )
}
