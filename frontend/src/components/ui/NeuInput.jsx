/**
 * NeuInput — inset neumorphic form field.
 *
 * Props: label, error, and all native <input> props.
 */
export default function NeuInput({ label, error, className = '', ...props }) {
  return (
    <div className="mb-4">
      {label && (
        <label className="block mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.9px] text-neu-muted">
          {label}
        </label>
      )}
      <input className={`neu-input ${className}`} {...props} />
      {error && (
        <p className="mt-1.5 text-[0.72rem] text-neu-risk-hi font-medium">{error}</p>
      )}
    </div>
  )
}
