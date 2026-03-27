/**
 * NeuButton — neumorphic button.
 *
 * Props:
 *   variant  "primary" (violet, extruded) | "secondary" (grey surface)
 *   loading  true → show spinner, disable click
 *   fullWidth  true → w-full (default true)
 */
export default function NeuButton({
  children,
  variant = 'primary',
  loading = false,
  fullWidth = true,
  className = '',
  disabled,
  ...props
}) {
  const base = variant === 'primary' ? 'neu-btn-primary' : 'neu-btn-secondary'
  const widthClass = fullWidth ? 'w-full' : ''
  const isDisabled = disabled || loading

  return (
    <button
      className={`${base} ${widthClass} ${isDisabled ? 'opacity-60 pointer-events-none' : ''} ${className}`}
      disabled={isDisabled}
      {...props}
    >
      {loading ? (
        <span className="inline-flex items-center justify-center gap-2">
          <svg
            className="animate-spin h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12" cy="12" r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          {children}
        </span>
      ) : (
        children
      )}
    </button>
  )
}
