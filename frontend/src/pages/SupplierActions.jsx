import { useState, useEffect } from 'react'
import {
  apiGetSupplierActionLog,
  apiMarkActionLogSeen,
  getDocumentDownloadUrl,
} from '../api/bff'

const ACTION_META = {
  login:            { label: 'Logged in',            icon: '🔐', color: 'text-neu-accent' },
  notification_read: { label: 'Opened notification',  icon: '📬', color: 'text-blue-400' },
  document_uploaded: { label: 'Uploaded document',    icon: '📎', color: 'text-green-400' },
}

function ActionRow({ entry }) {
  const meta    = ACTION_META[entry.action_type] ?? { label: entry.action_type, icon: '•', color: 'text-neu-muted' }
  const details = (() => { try { return JSON.parse(entry.details || '{}') } catch { return {} } })()
  const docId   = details.doc_id   ?? null
  const filename = details.filename ?? null

  return (
    <div className={`flex items-start gap-3 px-5 py-3.5 border-b border-[rgba(0,0,0,0.05)] dark:border-[rgba(255,255,255,0.05)] last:border-0 ${!entry.admin_seen ? 'bg-neu-accent/5' : ''}`}>
      <span className="text-lg mt-0.5 shrink-0">{meta.icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-[0.78rem] font-bold ${meta.color}`}>{meta.label}</span>
          {!entry.admin_seen && (
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-neu-accent" />
          )}
        </div>
        <p className="text-[0.82rem] font-semibold text-neu-fg truncate">{entry.supplier_name}</p>
        {filename && (
          <p className="text-[0.74rem] text-neu-muted mt-0.5 truncate">{filename}</p>
        )}
      </div>
      <div className="flex flex-col items-end gap-1.5 shrink-0">
        <span className="text-[0.68rem] text-neu-muted whitespace-nowrap">
          {new Date(entry.created_at).toLocaleString()}
        </span>
        {docId && (
          <a
            href={getDocumentDownloadUrl(docId)}
            download={filename ?? true}
            className="inline-flex items-center gap-1 text-[0.72rem] text-neu-accent hover:underline font-medium"
          >
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download
          </a>
        )}
      </div>
    </div>
  )
}

export default function SupplierActions() {
  const [log,     setLog]     = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')
  const [marking, setMarking] = useState(false)

  const fetchLog = async () => {
    try {
      const { data } = await apiGetSupplierActionLog()
      setLog(data)
    } catch {
      setError('Could not load action log.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchLog() }, [])

  const unseenCount = log.filter(e => !e.admin_seen).length

  const handleMarkSeen = async () => {
    setMarking(true)
    try {
      await apiMarkActionLogSeen()
      setLog(prev => prev.map(e => ({ ...e, admin_seen: true })))
    } catch {
      // silent
    } finally {
      setMarking(false)
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <span className="neu-badge">Supplier Activity</span>
            {unseenCount > 0 && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[0.68rem] font-bold bg-neu-accent/15 text-neu-accent border border-neu-accent/30">
                {unseenCount} new
              </span>
            )}
          </div>
          <h1 className="font-display text-[1.5rem] font-extrabold text-neu-fg tracking-tight">
            Supplier Actions
          </h1>
          <p className="text-[0.79rem] text-neu-muted mt-0.5">
            Activity log for all supplier portal interactions.
          </p>
        </div>
        {unseenCount > 0 && (
          <button
            onClick={handleMarkSeen}
            disabled={marking}
            className="mt-1 neu-btn text-[0.78rem] px-4 py-2 disabled:opacity-50"
          >
            {marking ? 'Marking…' : 'Mark all seen'}
          </button>
        )}
      </div>

      {/* Card */}
      <div className="neu-card p-0 overflow-hidden">
        {loading && (
          <p className="p-8 text-center text-neu-muted text-[0.85rem]">Loading…</p>
        )}

        {error && (
          <p className="p-8 text-center text-neu-risk-hi text-[0.85rem]">{error}</p>
        )}

        {!loading && !error && log.length === 0 && (
          <div className="p-12 text-center">
            <svg className="w-10 h-10 mx-auto mb-3 text-neu-muted/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="font-semibold text-neu-fg text-[0.9rem]">No activity yet</p>
            <p className="text-neu-muted text-[0.78rem] mt-1">Supplier interactions will appear here.</p>
          </div>
        )}

        {!loading && !error && log.length > 0 && (
          <div>
            {log.map(entry => (
              <ActionRow key={entry.id} entry={entry} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
