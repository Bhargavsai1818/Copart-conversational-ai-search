import React, { useState, useCallback } from 'react'
import ChatInterface from './components/ChatInterface'
import VehicleCard from './components/VehicleCard'
import FilterPanel from './components/FilterPanel'
import './index.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://copart-conversational-ai-search.onrender.com";

const WELCOME_QUERIES = [
  'Show me Toyota SUVs easy to fix with no airbag damage',
  'Find cars with light hail damage for paintless repair (PDR)',
  'Run-and-drive Honda Civics in Texas under $15k',
  'What is the difference between Salvage Title and Clean Title?',
  'What does Enhanced Vehicle mean at Copart?',
]


function CopartLogo() {
  return (
    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="16" cy="16" r="14" fill="url(#logoGrad)" opacity="0.9" />
      <path d="M9 16a7 7 0 1 1 7 7" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="16" cy="16" r="3" fill="white" />
      <defs>
        <linearGradient id="logoGrad" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop stopColor="#3b82f6" />
          <stop offset="1" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>
    </svg>
  )
}

function SkeletonCard() {
  return <div className="skeleton skeleton-card" />
}

export default function App() {
  const [vehicles, setVehicles] = useState([])
  const [totalMatches, setTotalMatches] = useState(0)
  const [activeFilters, setActiveFilters] = useState({})
  const [hasSearched, setHasSearched] = useState(false)
  const [exampleQuery, setExampleQuery] = useState(null)

  const handleResults = useCallback((newVehicles, total) => {
    setVehicles(newVehicles)
    setTotalMatches(total)
    setHasSearched(true)
  }, [])

  const handleFiltersChange = useCallback((filters) => {
    setActiveFilters(filters)
  }, [])

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-logo">
          <CopartLogo />
          <span className="header-logo-text">Copart AI Search</span>
          <span className="header-badge">Beta</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--c-text-3)' }}>
            {hasSearched ? `${totalMatches.toLocaleString()} vehicles matched` : '500 vehicles in inventory'}
          </span>
        </div>
      </header>

      {/* Main layout */}
      <div className="main-layout">
        {/* Left: Chat panel */}
        <ChatInterface
          onResults={handleResults}
          onFiltersChange={handleFiltersChange}
          exampleQuery={exampleQuery}
          onExampleQueryConsumed={() => setExampleQuery(null)}
        />

        {/* Right: Results */}
        <main className="results-panel" aria-label="Vehicle search results">
          {/* Results header */}
          <div className="results-header">
            <h1 className="results-title">
              {hasSearched ? 'Search Results' : 'Vehicle Inventory'}
            </h1>
            {hasSearched && (
              <span className="results-count">
                Showing {vehicles.length} of {totalMatches.toLocaleString()} vehicles
              </span>
            )}
          </div>

          {/* Active filters */}
          <FilterPanel filters={activeFilters} />

          {/* Content area */}
          {!hasSearched ? (
            /* Welcome state */
            <div className="welcome-state">
              <div className="welcome-icon">🚗</div>
              <div className="welcome-title">Find Your Vehicle</div>
              <p className="welcome-subtitle">
                Use the chat to search our inventory in plain English. Refine your search across multiple turns.
              </p>
              <div className="welcome-examples">
                {WELCOME_QUERIES.map((q, i) => (
                  <button
                    key={i}
                    id={`welcome-example-${i}`}
                    className="example-query"
                    onClick={() => setExampleQuery(q)}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : vehicles.length === 0 ? (
            /* No results */
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <div className="empty-title">No vehicles found</div>
              <p className="empty-subtitle">
                Try relaxing some filters — ask me to expand the price range, remove a condition requirement, or search in more states.
              </p>
            </div>
          ) : (
            /* Vehicle grid */
            <div className="vehicle-grid">
              {vehicles.map(vehicle => (
                <VehicleCard key={vehicle.id} vehicle={vehicle} />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
