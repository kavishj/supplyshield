import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiSupplierLogin } from '../api/supplier'
import { useSupplierAuthStore } from '../stores/supplierAuthStore'
import NeuButton from '../components/ui/NeuButton'
import NeuInput  from '../components/ui/NeuInput'

export default function SupplierLogin() {
  const { login }    = useSupplierAuthStore()
  const navigate     = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(''); setLoading(true)
    try {
      const { data } = await apiSupplierLogin(username, password)
      login(data)
      navigate('/supplier-portal', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-neu-base flex flex-col items-center justify-center px-4">

      {/* Brand */}
      <div className="mb-8 text-center">
        <h1 className="font-display text-[1.9rem] font-extrabold text-neu-fg tracking-[-1.5px] leading-none mb-1">
          Supply<span className="text-neu-accent">Shield</span>
        </h1>
        <p className="text-[0.65rem] font-bold uppercase tracking-[3px] text-neu-accent">
          Supplier Portal
        </p>
      </div>

      {/* Card */}
      <div className="neu-card p-8 w-full max-w-sm animate-fade-in">
        <div className="mb-5">
          <span className="neu-badge mb-3">Supplier Access</span>
          <h2 className="font-display text-[1.2rem] font-bold text-neu-fg tracking-tight mb-1">
            Sign In
          </h2>
          <p className="text-[0.79rem] text-neu-muted leading-[1.55]">
            Use the credentials provided by your procurement team.
          </p>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <NeuInput
            label="Username"
            type="text"
            placeholder="Enter your username"
            autoComplete="username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
          />
          <NeuInput
            label="Password"
            type="password"
            placeholder="Enter your password"
            autoComplete="current-password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />

          {error && (
            <p className="mb-3 text-[0.78rem] text-neu-risk-hi font-medium neu-well px-4 py-2.5">
              {error}
            </p>
          )}

          <NeuButton type="submit" loading={loading}>
            Sign In →
          </NeuButton>
        </form>
      </div>

      {/* Footer */}
      <p className="mt-8 text-[0.65rem] text-[#A0AEC0] tracking-[0.5px]">
        SupplyShield &nbsp;·&nbsp; Supplier Portal
      </p>
    </div>
  )
}
