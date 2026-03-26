import { useState, useEffect, useMemo } from 'react'
import GraphView from './components/GraphView.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import NodeDetail from './components/NodeDetail.jsx'
import { fetchGraph } from './api.js'

function App() {
  const [graphData, setGraphData]         = useState({ nodes: [], links: [] })
  const [selectedNode, setSelectedNode]   = useState(null)
  const [highlightedIds, setHighlightedIds] = useState(new Set())
  const [graphError, setGraphError]       = useState(null)
  const [showOverlay, setShowOverlay]     = useState(true)

  // Legend data
  const LEGEND = [
    { type: 'SalesOrder',      color: '#4f9cf9' },
    { type: 'Delivery',        color: '#f97b4f' },
    { type: 'BillingDocument', color: '#a78bfa' },
    { type: 'JournalEntry',    color: '#34d399' },
  ]

  useEffect(() => {
    fetchGraph()
      .then(data => {
        // Annotate nodes with connection count for NodeDetail
        const linkMap = {}
        data.links.forEach(l => {
          if (!l.source || !l.target) return
          const s = typeof l.source === 'object' ? l.source.id : l.source
          const t = typeof l.target === 'object' ? l.target.id : l.target
          if (s) linkMap[s] = (linkMap[s] || 0) + 1
          if (t) linkMap[t] = (linkMap[t] || 0) + 1
        })
        data.nodes.forEach(n => { n.__linkedNodes = linkMap[n.id] || 0 })
        setGraphData(data)
      })
      .catch(err => setGraphError(err.message))
  }, [])

  const handleNodeClick = (node) => {
    setSelectedNode(node)
  }

  const handleHighlight = (ids) => {
    setHighlightedIds(new Set(ids))
    // Auto-clear highlight after 8 seconds
    setTimeout(() => setHighlightedIds(new Set()), 8000)
  }

  const highlightSet = useMemo(() => highlightedIds, [highlightedIds])

  return (
    <div className="app-root">
      {/* Top navigation bar */}
      <header className="topbar">
        <div className="topbar-left">
          <button className="topbar-icon-btn" aria-label="Toggle sidebar">☰</button>
          <nav className="breadcrumb">
            <span className="breadcrumb-item">Mapping</span>
            <span className="breadcrumb-sep">/</span>
            <span className="breadcrumb-item active">Order to Cash</span>
          </nav>
        </div>
        <div className="topbar-right">
          <span className="node-count-badge">{graphData.nodes.length} nodes</span>
          <span className="node-count-badge">{graphData.links.length} edges</span>
        </div>
      </header>

      <div className="main-layout">
        {/* Graph panel */}
        <div className="graph-panel">
          {/* Controls overlay */}
          <div className="graph-controls">
            <button
              className="ctrl-btn"
              onClick={() => setHighlightedIds(new Set())}
            >
              ✦ Minimize
            </button>
            <button
              className="ctrl-btn"
              onClick={() => setShowOverlay(v => !v)}
            >
              ⊞ {showOverlay ? 'Hide' : 'Show'} Legend
            </button>
          </div>

          {/* Legend */}
          {showOverlay && (
            <div className="graph-legend">
              {LEGEND.map(l => (
                <div key={l.type} className="legend-item">
                  <span className="legend-dot" style={{ background: l.color }} />
                  <span className="legend-label">{l.type}</span>
                </div>
              ))}
            </div>
          )}

          {/* Highlighted count banner */}
          {highlightedIds.size > 0 && (
            <div className="highlight-banner">
              ✦ {highlightedIds.size} nodes highlighted from query
              <button onClick={() => setHighlightedIds(new Set())}>Clear</button>
            </div>
          )}

          {graphError ? (
            <div className="graph-error">
              <p>⚠️ Could not load graph: {graphError}</p>
              <p>Make sure the backend is accessible at <code>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</code></p>
            </div>
          ) : (
            <GraphView
              graphData={graphData}
              onNodeClick={handleNodeClick}
              highlightedIds={highlightSet}
            />
          )}

          {/* Node detail popup */}
          {selectedNode && (
            <NodeDetail
              node={selectedNode}
              onClose={() => setSelectedNode(null)}
            />
          )}
        </div>

        {/* Chat panel */}
        <ChatPanel onHighlight={handleHighlight} />
      </div>
    </div>
  )
}

export default App
