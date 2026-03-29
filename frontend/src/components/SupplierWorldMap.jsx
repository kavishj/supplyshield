import { useRef, useEffect, useState } from 'react'
import {
  ComposableMap, Geographies, Geography,
  Graticule, Sphere, Marker, Line,
} from 'react-simple-maps'
import { useThemeStore } from '../stores/themeStore'

const GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

const HIGH = 0.65, MED = 0.40
const riskColor = (s) => s >= HIGH ? '#EF4444' : s >= MED ? '#F59E0B' : '#22C55E'

// Country centroids [longitude, latitude]
const COORDS = {
  // Asia-Pacific
  CHINA:           [104.2, 35.9],
  INDIA:           [78.9, 20.6],
  JAPAN:           [138.3, 36.2],
  'SOUTH KOREA':   [127.8, 35.9],
  INDONESIA:       [113.9, -0.8],
  VIETNAM:         [108.3, 14.1],
  THAILAND:        [100.9, 15.9],
  MALAYSIA:        [109.7, 4.2],
  PHILIPPINES:     [121.8, 12.9],
  BANGLADESH:      [90.4, 23.7],
  PAKISTAN:        [69.3, 30.4],
  'SRI LANKA':     [80.8, 7.9],
  NEPAL:           [84.1, 28.4],
  MYANMAR:         [95.9, 21.9],
  CAMBODIA:        [105.0, 12.6],
  SINGAPORE:       [103.8, 1.4],
  TAIWAN:          [120.9, 24.0],
  'HONG KONG':     [114.1, 22.4],
  AUSTRALIA:       [133.8, -25.3],
  'NEW ZEALAND':   [174.9, -41.0],
  KAZAKHSTAN:      [66.9, 48.0],
  UZBEKISTAN:      [64.6, 41.3],
  LAOS:            [103.0, 17.9],
  // Middle East
  'SAUDI ARABIA':  [45.1, 23.9],
  UAE:             [53.8, 23.4],
  'UNITED ARAB EMIRATES': [53.8, 23.4],
  TURKEY:          [35.2, 38.9],
  ISRAEL:          [34.9, 31.0],
  IRAN:            [53.7, 32.4],
  IRAQ:            [43.7, 33.2],
  QATAR:           [51.2, 25.4],
  KUWAIT:          [47.5, 29.3],
  OMAN:            [57.6, 21.5],
  JORDAN:          [36.2, 30.6],
  LEBANON:         [35.9, 33.9],
  // Europe
  GERMANY:         [10.5, 51.2],
  FRANCE:          [2.2, 46.2],
  'UNITED KINGDOM':[-3.4, 55.4],
  UK:              [-3.4, 55.4],
  ITALY:           [12.6, 41.9],
  SPAIN:           [-3.7, 40.5],
  NETHERLANDS:     [5.3, 52.1],
  BELGIUM:         [4.5, 50.5],
  SWITZERLAND:     [8.2, 46.8],
  POLAND:          [19.1, 51.9],
  SWEDEN:          [18.6, 60.1],
  NORWAY:          [8.5, 60.5],
  DENMARK:         [9.5, 56.3],
  FINLAND:         [25.7, 61.9],
  AUSTRIA:         [14.6, 47.5],
  'CZECH REPUBLIC':[15.5, 49.8],
  UKRAINE:         [31.2, 48.4],
  ROMANIA:         [24.9, 45.9],
  PORTUGAL:        [-8.2, 39.4],
  GREECE:          [21.8, 39.1],
  HUNGARY:         [19.5, 47.2],
  IRELAND:         [-8.2, 53.4],
  RUSSIA:          [105.3, 61.5],
  // Americas
  USA:             [-95.7, 37.1],
  'UNITED STATES': [-95.7, 37.1],
  CANADA:          [-106.3, 56.1],
  MEXICO:          [-102.6, 23.6],
  BRAZIL:          [-51.9, -14.2],
  ARGENTINA:       [-63.6, -38.4],
  CHILE:           [-71.5, -35.7],
  COLOMBIA:        [-74.3, 4.6],
  PERU:            [-75.0, -9.2],
  VENEZUELA:       [-66.6, 6.4],
  ECUADOR:         [-78.2, -1.8],
  BOLIVIA:         [-63.6, -16.3],
  // Africa
  'SOUTH AFRICA':  [22.9, -30.6],
  NIGERIA:         [8.7, 9.1],
  EGYPT:           [30.8, 26.8],
  KENYA:           [37.9, -0.0],
  ETHIOPIA:        [40.5, 9.1],
  GHANA:           [-1.0, 8.0],
  MOROCCO:         [-7.1, 31.8],
  ALGERIA:         [1.7, 28.0],
  TANZANIA:        [34.9, -6.4],
  MOZAMBIQUE:      [35.5, -18.7],
}

function Tooltip({ data }) {
  return (
    <div
      className="absolute neu-card-sm px-3.5 py-2.5 pointer-events-none z-20"
      style={{ left: data.x, top: data.y, minWidth: 150, transform: 'translate(14px, -50%)' }}
    >
      <p className="font-bold text-[0.8rem] text-neu-fg leading-tight">{data.label}</p>
      {data.country && data.country !== data.label && (
        <p className="text-[0.7rem] text-neu-muted">{data.country}</p>
      )}
      {data.score != null && (
        <p className="text-[0.72rem] font-semibold mt-0.5 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full shrink-0" style={{ background: data.color }} />
          <span style={{ color: data.color }}>{data.risk}</span>
          <span className="text-neu-muted">· {data.score.toFixed(3)}</span>
        </p>
      )}
    </div>
  )
}

export default function SupplierWorldMap({ suppliers = [], homeCountry = '' }) {
  const dark       = useThemeStore(s => s.dark)
  const sectionRef = useRef(null)
  const wrapperRef = useRef(null)
  const [blurPx,  setBlurPx]  = useState(0)
  const [tooltip, setTooltip] = useState(null)

  // ── Scroll: blur increases as user scrolls past the map ──────────────────────
  useEffect(() => {
    const onScroll = () => {
      if (!sectionRef.current) return
      const rect        = sectionRef.current.getBoundingClientRect()
      const scrolledPast = -rect.top
      const mapH        = sectionRef.current.offsetHeight || 460
      const blurStart   = mapH * 0.18
      const blurEnd     = mapH * 0.68
      if (scrolledPast <= blurStart) { setBlurPx(0);  return }
      if (scrolledPast >= blurEnd)   { setBlurPx(14); return }
      const t = (scrolledPast - blurStart) / (blurEnd - blurStart)
      setBlurPx(+(t * 14).toFixed(1))
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // ── Data prep ─────────────────────────────────────────────────────────────────
  const homeKey    = homeCountry?.toUpperCase().trim() ?? ''
  const homeCoords = COORDS[homeKey] ?? COORDS['INDIA']

  const byCountry = {}
  suppliers.forEach(s => {
    const key = (s.country ?? '').toUpperCase().trim()
    if (!COORDS[key]) return
    const prev = byCountry[key]
    if (!prev || (s.score ?? 0) > (prev.score ?? 0)) byCountry[key] = s
  })
  const mapPoints = Object.entries(byCountry)
    .filter(([key]) => key !== homeKey)
    .map(([key, s]) => ({ ...s, key, coords: COORDS[key] }))

  // ── Theme: sphere + geo colours blend into the page surface ──────────────────
  // Sphere matches neu-base exactly so it's invisible
  const sphereColor  = dark ? '#1E293B' : '#E0E5EC'
  // Countries: lightened from background so landmasses are visible
  const geoFill      = dark ? '#2C4060' : '#D4DCE6'
  const geoBorder    = dark ? '#3A5278' : '#C2CADA'
  const graticuleC   = dark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.03)'

  // ── Tooltip helpers ───────────────────────────────────────────────────────────
  const showTip = (e, label, country, score) => {
    if (!wrapperRef.current) return
    const rect = wrapperRef.current.getBoundingClientRect()
    const sc   = score ?? 0
    setTooltip({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      label,
      country,
      score,
      color: riskColor(sc),
      risk:  sc >= HIGH ? 'HIGH' : sc >= MED ? 'MEDIUM' : 'LOW',
    })
  }
  const moveTip = (e) => {
    if (!tooltip || !wrapperRef.current) return
    const rect = wrapperRef.current.getBoundingClientRect()
    setTooltip(p => p ? { ...p, x: e.clientX - rect.left, y: e.clientY - rect.top } : null)
  }

  return (
    <div
      ref={sectionRef}
      style={{
        position:   'sticky',
        top:        64,
        zIndex:     0,
        filter:     `blur(${blurPx}px)`,
        transition: 'filter 0.15s linear',
        pointerEvents: blurPx > 6 ? 'none' : 'auto',
      }}
    >
      <div ref={wrapperRef} className="relative overflow-hidden" onMouseMove={moveTip} onMouseLeave={() => setTooltip(null)}>
        <ComposableMap
          projection="geoEqualEarth"
          projectionConfig={{ scale: 158, center: [20, 5] }}
          width={900}
          height={440}
          style={{ width: '100%', height: 'auto', display: 'block' }}
        >
          <defs>
            {[['arr-r','#EF4444'],['arr-y','#F59E0B'],['arr-g','#22C55E']].map(([id, fill]) => (
              <marker key={id} id={id} markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                <path d="M0,0 L6,3 L0,6 Z" fill={fill} opacity="0.85" />
              </marker>
            ))}
          </defs>

          {/* Background sphere — same colour as page, so it disappears */}
          <Sphere id="rsm-sphere" stroke={sphereColor} strokeWidth={0} style={{ fill: sphereColor }} />

          {/* Faint grid */}
          <Graticule stroke={graticuleC} strokeWidth={0.5} />

          {/* Countries */}
          <Geographies geography={GEO_URL}>
            {({ geographies }) =>
              geographies.map(geo => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={geoFill}
                  stroke={geoBorder}
                  strokeWidth={0.35}
                  style={{
                    default: { outline: 'none' },
                    hover:   { outline: 'none', fill: dark ? '#3D5A80' : '#C0CDD8' },
                    pressed: { outline: 'none' },
                  }}
                />
              ))
            }
          </Geographies>

          {/* Geodesic supply chain arcs */}
          {mapPoints.map((pt, i) => {
            const color    = riskColor(pt.score ?? 0)
            const markerId = color === '#EF4444' ? 'arr-r' : color === '#F59E0B' ? 'arr-y' : 'arr-g'
            return (
              <Line
                key={`arc-${i}`}
                from={pt.coords}
                to={homeCoords}
                stroke={color}
                strokeWidth={1.3}
                strokeOpacity={0.55}
                fill="none"
                markerEnd={`url(#${markerId})`}
              />
            )
          })}

          {/* Supplier dots */}
          {mapPoints.map((pt, i) => {
            const color = riskColor(pt.score ?? 0)
            return (
              <Marker
                key={`dot-${i}`}
                coordinates={pt.coords}
                onMouseEnter={e => showTip(e, pt.supplier_name || pt.key, pt.key, pt.score)}
              >
                <circle
                  r={5.5}
                  fill={color}
                  stroke="white"
                  strokeWidth={1.5}
                  style={{ cursor: 'pointer', filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.3))' }}
                />
              </Marker>
            )
          })}

          {/* Home company marker */}
          <Marker
            coordinates={homeCoords}
            onMouseEnter={e => showTip(e, homeCountry || 'Your Company', homeCountry, null)}
          >
            <circle r={18} fill="#6C63FF" fillOpacity={0.12} />
            <circle r={11} fill="#6C63FF" fillOpacity={0.25} />
            <circle
              r={7}
              fill="#6C63FF"
              stroke="white"
              strokeWidth={2}
              style={{ filter: 'drop-shadow(0 2px 5px rgba(108,99,255,0.55))', cursor: 'pointer' }}
            />
          </Marker>
        </ComposableMap>

        {tooltip && <Tooltip data={tooltip} />}
      </div>
    </div>
  )
}
