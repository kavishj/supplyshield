/**
 * NeuCard — extruded neumorphic surface.
 *
 * Props:
 *   size   "md" (default, 32px radius) | "sm" (16px radius, lighter shadow)
 *   hover  true → lift + deepen shadow on hover
 *   as     HTML tag to render (default "div")
 */
export default function NeuCard({
  children,
  className = '',
  size = 'md',
  hover = false,
  as: Tag = 'div',
  ...props
}) {
  const base = size === 'sm' ? 'neu-card-sm' : 'neu-card'
  const hoverClass = hover
    ? 'transition-all duration-300 ease-out hover:-translate-y-0.5 hover:shadow-neu-out-lg cursor-pointer'
    : ''

  return (
    <Tag className={`${base} ${hoverClass} ${className}`} {...props}>
      {children}
    </Tag>
  )
}
