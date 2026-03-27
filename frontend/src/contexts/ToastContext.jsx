/**
 * Toast notification system.
 *
 * Usage:
 *   const toast = useToast()
 *   toast('Supplier saved!')                    // success (default)
 *   toast('Something went wrong', 'error')
 *   toast('PDF downloading…', 'info')
 *   toast('Contract expiring soon', 'warn')
 */
import { createContext, useContext, useState, useCallback } from 'react'

const ToastCtx = createContext(null)
export const useToast = () => useContext(ToastCtx)

let _uid = 0

const TYPE_CFG = {
  success: { icon: '✓', color: '#10B981' },
  error:   { icon: '✕', color: '#EF4444' },
  info:    { icon: 'ℹ', color: '#6C63FF' },
  warn:    { icon: '⚠', color: '#F59E0B' },
}

function Toast({ id, message, type, onRemove }) {
  const cfg = TYPE_CFG[type] ?? TYPE_CFG.info
  return (
    <div
      className="flex items-start gap-3 px-4 py-3 rounded-[14px] animate-fade-in max-w-sm w-full"
      style={{
        background: 'var(--neu-bg, #E0E5EC)',
        boxShadow: `6px 6px 14px rgba(0,0,0,0.18), -4px -4px 10px rgba(255,255,255,0.08), 0 0 0 1px ${cfg.color}33`,
      }}
    >
      {/* Icon dot */}
      <span
        className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[0.65rem] font-bold flex-shrink-0 mt-0.5"
        style={{ background: cfg.color }}
      >
        {cfg.icon}
      </span>

      {/* Message */}
      <p className="text-[0.82rem] flex-1 leading-[1.45]" style={{ color: 'var(--neu-fg, #3D4852)' }}>
        {message}
      </p>

      {/* Dismiss */}
      <button
        onClick={() => onRemove(id)}
        className="text-[1rem] leading-none flex-shrink-0 opacity-40 hover:opacity-80 transition-opacity"
        style={{ color: 'var(--neu-fg, #3D4852)' }}
      >
        ×
      </button>
    </div>
  )
}

function ToastContainer({ toasts, onRemove }) {
  if (!toasts.length) return null
  return (
    <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2.5 items-end pointer-events-none">
      {toasts.map(t => (
        <div key={t.id} className="pointer-events-auto">
          <Toast {...t} onRemove={onRemove} />
        </div>
      ))}
    </div>
  )
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const addToast = useCallback((message, type = 'success', duration = 3500) => {
    const id = ++_uid
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => removeToast(id), duration)
  }, [removeToast])

  return (
    <ToastCtx.Provider value={addToast}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastCtx.Provider>
  )
}
