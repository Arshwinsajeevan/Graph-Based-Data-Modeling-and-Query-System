import { useCallback, useRef, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d'

/**
 * GraphView — renders the force-directed graph using react-force-graph-2d.
 *
 * Props:
 *   graphData       {nodes, links} from the API
 *   onNodeClick     called with node object when user clicks a node
 *   highlightedIds  set of node IDs to highlight (from LLM query results)
 */
function GraphView({ graphData, onNodeClick, highlightedIds = new Set() }) {
  const fgRef = useRef()

  // Node type → color mapping
  const NODE_COLORS = {
    SalesOrder:      '#4f9cf9',
    Delivery:        '#f97b4f',
    BillingDocument: '#a78bfa',
    JournalEntry:    '#34d399',
  }

  // Auto-fit graph on load
  useEffect(() => {
    if (fgRef.current && graphData?.nodes?.length > 0) {
      setTimeout(() => fgRef.current.zoomToFit(400, 60), 500)
    }
  }, [graphData])

  const paintNode = useCallback((node, ctx, globalScale) => {
    const isHighlighted = highlightedIds.has(node.id)
    const color = NODE_COLORS[node.type] || '#999'
    const r = isHighlighted ? 8 : 5

    // Outer glow for highlighted nodes
    if (isHighlighted) {
      ctx.beginPath()
      ctx.arc(node.x, node.y, r + 4, 0, 2 * Math.PI)
      ctx.fillStyle = color + '44'
      ctx.fill()
    }

    // Node circle
    ctx.beginPath()
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
    ctx.fillStyle = isHighlighted ? color : color + 'cc'
    ctx.fill()

    if (isHighlighted) {
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 1.5 / globalScale
      ctx.stroke()
    }

    // Label (only at higher zoom levels)
    if (globalScale > 2 || isHighlighted) {
      const label = node.label || node.id
      const fontSize = 10 / globalScale
      ctx.font = `${fontSize}px Inter, sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillStyle = isHighlighted ? '#ffffff' : '#cccccc'
      ctx.fillText(label, node.x, node.y + r + 2)
    }
  }, [highlightedIds])

  if (!graphData?.nodes?.length) {
    return (
      <div className="graph-empty">
        <div className="spinner" />
        <p>Loading graph data...</p>
      </div>
    )
  }

  return (
    <ForceGraph2D
      ref={fgRef}
      graphData={graphData}
      nodeCanvasObject={paintNode}
      nodeCanvasObjectMode={() => 'replace'}
      linkColor={() => '#3a6fa8'}
      linkWidth={1}
      linkDirectionalArrowLength={4}
      linkDirectionalArrowRelPos={1}
      backgroundColor="#0d1117"
      onNodeClick={onNodeClick}
      nodePointerAreaPaint={(node, color, ctx) => {
        ctx.fillStyle = color
        ctx.beginPath()
        ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI)
        ctx.fill()
      }}
      cooldownTicks={100}
      d3AlphaDecay={0.02}
      d3VelocityDecay={0.3}
    />
  )
}

export default GraphView
