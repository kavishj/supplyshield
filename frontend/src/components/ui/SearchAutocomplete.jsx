/**
 * SearchAutocomplete
 *
 * Drop-in replacement for NeuInput on text fields that benefit from
 * "recently used" suggestions, like the browser address bar.
 *
 * Props
 * ─────────────────────────────────────────────────────────────
 * value          string    – controlled value
 * onChange       fn        – called with a synthetic { target: { value } } event
 * storageKey     string    – localStorage key used to persist history
 * staticOptions  string[]  – fixed suggestions (e.g. country list) shown when
 *                            the query matches, distinct from user history
 * label          string    – field label (same as NeuInput)
 * error          string    – validation error (same as NeuInput)
 * placeholder    string
 * className      string
 * saveOnBlur     bool      – save the current value on blur (default false);
 *                            set true for search-filter inputs with no submit btn
 *
 * Utility export
 * ─────────────────────────────────────────────────────────────
 * saveHistory(key, value)  – call from a parent's submit handler to persist
 *                            the submitted value into the field's history
 */

import { useState, useEffect, useRef } from 'react'

const MAX_HISTORY = 10

// ── localStorage helpers ──────────────────────────────────────
function readHistory(key) {
  try { return JSON.parse(localStorage.getItem(key) || '[]') }
  catch { return [] }
}

export function saveHistory(key, value) {
  if (!value?.trim()) return
  const v       = value.trim()
  const current = readHistory(key)
  const updated = [v, ...current.filter(h => h.toLowerCase() !== v.toLowerCase())]
    .slice(0, MAX_HISTORY)
  localStorage.setItem(key, JSON.stringify(updated))
}

// ── Component ─────────────────────────────────────────────────
export default function SearchAutocomplete({
  value = '',
  onChange,
  storageKey,
  staticOptions = [],
  label,
  error,
  placeholder = '',
  className = '',
  saveOnBlur = false,
  ...rest
}) {
  const [history,   setHistory]   = useState([])
  const [open,      setOpen]      = useState(false)
  const [activeIdx, setActiveIdx] = useState(-1)
  const wrapRef = useRef(null)

  // Load history from localStorage when key changes
  useEffect(() => {
    if (storageKey) setHistory(readHistory(storageKey))
  }, [storageKey])

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // ── Build suggestion list ──────────────────────────────────
  const query = (value || '').trim().toLowerCase()

  const historyMatches = history.filter(h =>
    !query || h.toLowerCase().includes(query)
  )

  const staticMatches = staticOptions
    .filter(o =>
      query &&
      o.toLowerCase().includes(query) &&
      !history.find(h => h.toLowerCase() === o.toLowerCase())
    )
    .slice(0, 6)

  const suggestions = [...historyMatches, ...staticMatches]

  // ── Helpers ────────────────────────────────────────────────
  function persist(val) {
    if (!storageKey || !val?.trim()) return
    const updated = saveHistory(storageKey, val) // side-effect only
    setHistory(readHistory(storageKey))          // sync state
  }

  function select(val) {
    onChange({ target: { value: val } })
    if (storageKey) {
      saveHistory(storageKey, val)
      setHistory(readHistory(storageKey))
    }
    setOpen(false)
    setActiveIdx(-1)
  }

  function removeItem(e, item) {
    e.stopPropagation()
    const updated = history.filter(h => h !== item)
    setHistory(updated)
    if (storageKey) localStorage.setItem(storageKey, JSON.stringify(updated))
  }

  // ── Keyboard navigation ────────────────────────────────────
  function handleKeyDown(e) {
    if (!open || suggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIdx(i => Math.min(i + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIdx(i => Math.max(i - 1, -1))
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      e.preventDefault()
      select(suggestions[activeIdx])
    } else if (e.key === 'Escape') {
      setOpen(false)
      setActiveIdx(-1)
    }
  }

  function handleBlur() {
    if (saveOnBlur) persist(value)
  }

  const showDropdown = open && suggestions.length > 0

  return (
    <div className={`mb-4 relative ${className}`} ref={wrapRef}>
      {label && (
        <label className="block mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.9px] text-neu-muted">
          {label}
        </label>
      )}

      <input
        className="neu-input w-full"
        value={value}
        onChange={onChange}
        onFocus={() => setOpen(true)}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoComplete="off"
        {...rest}
      />

      {error && (
        <p className="mt-1.5 text-[0.72rem] text-neu-risk-hi font-medium">{error}</p>
      )}

      {/* ── Dropdown ──────────────────────────────────────── */}
      {showDropdown && (
        <ul
          className="absolute z-50 left-0 right-0 top-full mt-1 rounded-[10px] overflow-hidden"
          style={{
            background: 'var(--dropdown-bg, #D4D9E2)',
            border: '1px solid rgba(128,128,128,0.15)',
            boxShadow: 'var(--shadow-out-sm)',
          }}
        >
          {/* History section header */}
          {historyMatches.length > 0 && (
            <li className="px-3 pt-2 pb-1 text-[0.62rem] font-semibold uppercase tracking-[1.2px] select-none"
                style={{ color: 'var(--neu-muted)' }}>
              Recent
            </li>
          )}

          {historyMatches.map((item, i) => (
            <li
              key={`h-${item}`}
              onMouseDown={() => select(item)}
              className={`flex items-center gap-2.5 px-3 py-[9px] cursor-pointer text-[0.82rem] transition-colors
                ${activeIdx === i ? 'bg-neu-accent/20' : 'hover:bg-white/5'}`}
            >
              {/* Clock icon */}
              <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                   style={{ color: 'var(--neu-muted)' }}>
                <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
              </svg>
              <span className="flex-1 truncate" style={{ color: 'var(--neu-fg)' }}>{item}</span>
              {/* Remove button */}
              <button
                onMouseDown={e => removeItem(e, item)}
                className="flex-shrink-0 w-4 h-4 flex items-center justify-center rounded-full
                           text-neu-muted hover:text-neu-risk-hi hover:bg-neu-risk-hi/10 transition-colors text-[0.7rem]"
                tabIndex={-1}
              >
                ×
              </button>
            </li>
          ))}

          {/* Static suggestions divider */}
          {staticMatches.length > 0 && historyMatches.length > 0 && (
            <li className="mx-3 border-t border-white/5 my-1" />
          )}
          {staticMatches.length > 0 && (
            <li className="px-3 pt-1 pb-1 text-[0.62rem] font-semibold uppercase tracking-[1.2px] select-none"
                style={{ color: 'var(--neu-muted)' }}>
              Suggestions
            </li>
          )}

          {staticMatches.map((item, i) => {
            const idx = historyMatches.length + i
            return (
              <li
                key={`s-${item}`}
                onMouseDown={() => select(item)}
                className={`flex items-center gap-2.5 px-3 py-[9px] cursor-pointer text-[0.82rem] transition-colors
                  ${activeIdx === idx ? 'bg-neu-accent/20' : 'hover:bg-white/5'}`}
              >
                {/* Search icon */}
                <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                     style={{ color: 'var(--neu-muted)' }}>
                  <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                <span className="flex-1 truncate" style={{ color: 'var(--neu-fg)' }}>{item}</span>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
