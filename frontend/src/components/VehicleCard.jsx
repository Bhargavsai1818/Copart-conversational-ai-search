import React from 'react'

const CONDITION_LABELS = {
  run_and_drive: 'Run & Drive',
  enhanced_vehicle: 'Enhanced',
  stationary: 'Stationary',
  parts_only: 'Parts Only',
}

const FUEL_ICONS = { gasoline: '⛽', diesel: '🛢', hybrid: '🔋', electric: '⚡' }
const TRANS_ICONS = { automatic: '⚙️', manual: '🔧' }

function formatPrice(price) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(price)
}

function formatMileage(miles) {
  return new Intl.NumberFormat('en-US').format(miles) + ' mi'
}

function formatDamage(damage) {
  return damage.replace(/_/g, ' ')
}

export default function VehicleCard({ vehicle }) {
  const [imgError, setImgError] = React.useState(false)

  return (
    <article className="vehicle-card" id={`vehicle-${vehicle.id}`}>
      {/* Image */}
      <div className="vehicle-img-wrap">
        {!imgError ? (
          <img
            className="vehicle-img"
            src={vehicle.image_url}
            alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
            loading="lazy"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="vehicle-img-placeholder">🚗</div>
        )}
        <span className={`vehicle-condition-badge condition-${vehicle.condition}`}>
          {CONDITION_LABELS[vehicle.condition] || vehicle.condition}
        </span>
      </div>

      {/* Body */}
      <div className="vehicle-body">
        <div className="vehicle-year-make">
          {vehicle.year} · {vehicle.make}
        </div>
        <div className="vehicle-model" title={`${vehicle.model} ${vehicle.trim || ''}`}>
          {vehicle.model} {vehicle.trim}
        </div>

        {/* Meta chips */}
        <div className="vehicle-meta">
          <span className="meta-chip">📍 {vehicle.location_city}, {vehicle.location_state}</span>
          <span className="meta-chip">🛣 {formatMileage(vehicle.mileage)}</span>
          <span className="meta-chip">{FUEL_ICONS[vehicle.fuel_type] || '⛽'} {vehicle.fuel_type}</span>
          <span className="meta-chip">{TRANS_ICONS[vehicle.transmission] || '⚙️'} {vehicle.transmission}</span>
          <span className="meta-chip">🎨 {vehicle.color}</span>
        </div>

        {/* Inspector Notes Excerpt (Hybrid Search / RAG feature) */}
        {vehicle.inspector_notes && (
          <div className="inspector-notes-box">
            <span className="inspector-icon">🔍 <b>Inspector Note:</b></span> {vehicle.inspector_notes}
          </div>
        )}

        {/* Footer */}
        <div className="vehicle-footer">
          <div>
            <div className="vehicle-price">{formatPrice(vehicle.price)}</div>
            <div className="vehicle-lot">Lot #{vehicle.lot_number}</div>
          </div>
          <span className="vehicle-damage">{formatDamage(vehicle.damage_type)}</span>
        </div>
      </div>
    </article>
  )
}
