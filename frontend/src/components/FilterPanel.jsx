import React from 'react'

const FILTER_LABELS = {
  make: 'Make',
  model: 'Model',
  year_min: 'From Year',
  year_max: 'To Year',
  price_min: 'Min Price',
  price_max: 'Max Price',
  mileage_max: 'Max Miles',
  color: 'Color',
  body_type: 'Body',
  condition: 'Condition',
  damage_type: 'Damage',
  location_state: 'State',
  transmission: 'Trans.',
  fuel_type: 'Fuel',
  semantic_query: 'Inspector Search',
  sort_by: 'Sort',
}


function formatValue(key, value) {
  if (key === 'price_min' || key === 'price_max') {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)
  }
  if (key === 'mileage_max') {
    return new Intl.NumberFormat('en-US').format(value) + ' mi'
  }
  if (Array.isArray(value)) {
    return value.map(v => v.replace(/_/g, ' ')).join(', ')
  }
  if (typeof value === 'string') {
    return value.replace(/_/g, ' ')
  }
  return String(value)
}

export default function FilterPanel({ filters }) {
  const entries = Object.entries(filters).filter(
    ([k, v]) => v !== null && v !== undefined && k !== 'clear_all' && k !== 'limit'
      && !(Array.isArray(v) && v.length === 0)
  )

  if (entries.length === 0) {
    return (
      <div className="filters-bar">
        <span className="no-filters-hint">No active filters — ask me anything to search</span>
      </div>
    )
  }

  return (
    <div className="filters-bar">
      {entries.map(([key, value]) => (
        <div key={key} className="filter-tag">
          <span className="filter-tag-label">{FILTER_LABELS[key] || key}:</span>
          <span className="filter-tag-value">{formatValue(key, value)}</span>
        </div>
      ))}
    </div>
  )
}
