import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSupplierAuthStore } from '../stores/supplierAuthStore'
import {
  apiGetMyNotifications,
  apiMarkNotifRead,
  apiUploadDocument,
} from '../api/supplier'

const RISK_COLORS = {
  HIGH:   { badge: 'bg-red-500/15 text-red-400 border border-red-500/30',   dot: 'bg-red-400' },
  MEDIUM: { badge: 'bg-amber-500/15 text-amber-400 border border-amber-500/30', dot: 'bg-amber-400' },
  LOW:    { badge: 'bg-green-500/15 text-green-400 border border-green-500/30',  dot: 'bg-green-400' },
}

function RiskBadge({ level }) {
  const c = RISK_COLORS[level] ?? RISK_COLORS.MEDIUM
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[0.7rem] font-bold uppercase tracking-wider ${c.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {level} RISK
    </span>
  )
}

function UploadSection({ notificationId, existingDocs, onUploaded }) {
  const [file, setFile]       = useState(null)
  const [note, setNote]       = useState('')
  const [busy, setBusy]       = useState(false)
  const [error, setError]     = useState('')

  const handleUpload = async () => {
    if (!file) return
    setBusy(true); setError('')
    try {
      await apiUploadDocument(notificationId, file, note)
      setFile(null); setNote('')
      onUploaded()
    } catch (e) {
      setError(e.response?.data?.detail ?? 'Upload failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mt-4 pt-4 border-t border-[rgba(0,0,0,0.07)] dark:border-[rgba(255,255,255,0.07)]">
      <p className="text-[0.72rem] font-bold uppercase tracking-wider text-neu-muted mb-3">
        Submit Documents
      </p>

      {existingDocs.length > 0 && (
        <ul className="mb-3 space-y-1.5">
          {existingDocs.map(doc => (
            <li key={doc.id} className="flex items-center gap-2 text-[0.76rem] text-neu-muted">
              <svg className="w-3.5 h-3.5 shrink-0 text-neu-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414A1 1 0 0119 9.414V19a2 2 0 01-2 2z" />
              </svg>
              <span className="font-medium text-neu-fg">{doc.filename}</span>
              {doc.note && <span className="text-neu-muted">— {doc.note}</span>}
              <span className="ml-auto text-[0.68rem]">{new Date(doc.uploaded_at).toLocaleDateString()}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-col gap-2">
        <label className="neu-well px-3 py-2 cursor-pointer flex items-center gap-2 text-[0.78rem] text-neu-muted hover:text-neu-fg transition-colors">
          <svg className="w-4 h-4 text-neu-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          {file ? file.name : 'Choose a file…'}
          <input type="file" className="hidden" onChange={e => setFile(e.target.files[0] ?? null)} />
        </label>
        <input
          type="text"
          placeholder="Optional note (e.g. Q1 compliance certificate)"
          value={note}
          onChange={e => setNote(e.target.value)}
          className="neu-input text-[0.78rem]"
        />
        {error && <p className="text-[0.74rem] text-neu-risk-hi">{error}</p>}
        <button
          onClick={handleUpload}
          disabled={!file || busy}
          className="self-start neu-btn text-[0.78rem] px-4 py-2 disabled:opacity-40"
        >
          {busy ? 'Uploading…' : 'Upload'}
        </button>
      </div>
    </div>
  )
}

function NotificationCard({ notif, onRead, onDocUploaded }) {
  const [open, setOpen] = useState(false)

  const toggle = () => {
    setOpen(v => {
      const next = !v
      if (next && !notif.is_read) onRead(notif.id)
      return next
    })
  }

  const immediateItems = notif.immediate_actions
    ? (Array.isArray(notif.immediate_actions) ? notif.immediate_actions : JSON.parse(notif.immediate_actions))
    : []

  return (
    <div className={`neu-card p-0 overflow-hidden transition-all ${!notif.is_read ? 'ring-1 ring-neu-accent/40' : ''}`}>
      {/* Header row */}
      <button
        onClick={toggle}
        className="w-full flex items-center gap-3 px-5 py-4 text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <RiskBadge level={notif.risk_category} />
            {!notif.is_read && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[0.65rem] font-bold uppercase tracking-wider bg-neu-accent/15 text-neu-accent border border-neu-accent/30">
                New
              </span>
            )}
          </div>
          <p className="text-[0.85rem] font-semibold text-neu-fg truncate">
            {notif.message}
          </p>
          <p className="text-[0.7rem] text-neu-muted mt-0.5">
            {new Date(notif.sent_at).toLocaleString()}
          </p>
        </div>
        <svg
          className={`w-4 h-4 text-neu-muted shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded body */}
      {open && (
        <div className="px-5 pb-5 border-t border-[rgba(0,0,0,0.06)] dark:border-[rgba(255,255,255,0.06)]">
          {notif.message && (
            <p className="mt-4 text-[0.82rem] text-neu-fg leading-relaxed">
              {notif.message}
            </p>
          )}

          {immediateItems.length > 0 && (
            <div className="mt-4">
              <p className="text-[0.72rem] font-bold uppercase tracking-wider text-red-400 mb-2">
                Immediate Actions Required
              </p>
              <ul className="space-y-1.5">
                {immediateItems.map((item, i) => (
                  <li key={i} className="flex items-start gap-2 text-[0.8rem] text-neu-fg">
                    <span className="mt-1 w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                    {typeof item === 'string' ? item : (item.action ?? JSON.stringify(item))}
                  </li>
                ))}
              </ul>
            </div>
          )}


          <UploadSection
            notificationId={notif.id}
            existingDocs={notif.documents ?? []}
            onUploaded={() => onDocUploaded(notif.id)}
          />
        </div>
      )}
    </div>
  )
}

export default function SupplierPortal() {
  const { supplierName, contactName, logout } = useSupplierAuthStore()
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading]             = useState(true)
  const [error, setError]                 = useState('')

  const fetchNotifications = async () => {
    try {
      const { data } = await apiGetMyNotifications()
      setNotifications(data)
    } catch (e) {
      setError('Could not load notifications.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchNotifications() }, [])

  const handleRead = async (id) => {
    await apiMarkNotifRead(id).catch(() => {})
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, is_read: 1 } : n)
    )
  }

  const handleDocUploaded = (notifId) => {
    fetchNotifications()
  }

  const handleLogout = () => {
    logout()
    navigate('/supplier-login', { replace: true })
  }

  const unreadCount = notifications.filter(n => !n.is_read).length

  return (
    <div className="min-h-screen bg-neu-base px-4 py-8">
      {/* Top bar */}
      <div className="max-w-2xl mx-auto mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-[1.7rem] font-extrabold text-neu-fg tracking-[-1px] leading-none mb-1">
            Supply<span className="text-neu-accent">Shield</span>
          </h1>
          <p className="text-[0.65rem] font-bold uppercase tracking-[3px] text-neu-accent">
            Supplier Portal
          </p>
          <p className="mt-2 text-[0.83rem] text-neu-muted">
            {contactName
              ? <span>Hello, <span className="font-semibold text-neu-fg">{contactName}</span> · {supplierName}</span>
              : <span className="font-semibold text-neu-fg">{supplierName}</span>
            }
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="mt-1 neu-btn text-[0.78rem] px-4 py-2"
        >
          Sign Out
        </button>
      </div>

      <div className="max-w-2xl mx-auto">
        {/* Section header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-display text-[1.05rem] font-bold text-neu-fg tracking-tight">
              Action Alerts
            </h2>
            <p className="text-[0.74rem] text-neu-muted mt-0.5">
              Notifications from your procurement team
            </p>
          </div>
          {unreadCount > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.7rem] font-bold bg-neu-accent/15 text-neu-accent border border-neu-accent/30">
              {unreadCount} unread
            </span>
          )}
        </div>

        {loading && (
          <div className="neu-card p-8 text-center text-neu-muted text-[0.85rem]">
            Loading…
          </div>
        )}

        {error && (
          <div className="neu-card p-5 text-center text-neu-risk-hi text-[0.85rem]">
            {error}
          </div>
        )}

        {!loading && !error && notifications.length === 0 && (
          <div className="neu-card p-10 text-center">
            <svg className="w-10 h-10 mx-auto mb-3 text-neu-muted/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="font-semibold text-neu-fg text-[0.9rem]">All clear</p>
            <p className="text-neu-muted text-[0.78rem] mt-1">No action alerts at this time.</p>
          </div>
        )}

        {!loading && !error && notifications.length > 0 && (
          <div className="space-y-3">
            {notifications.map(notif => (
              <NotificationCard
                key={notif.id}
                notif={notif}
                onRead={handleRead}
                onDocUploaded={handleDocUploaded}
              />
            ))}
          </div>
        )}

        <p className="mt-10 text-center text-[0.65rem] text-[#A0AEC0] tracking-[0.5px]">
          SupplyShield &nbsp;·&nbsp; Supplier Portal
        </p>
      </div>
    </div>
  )
}
