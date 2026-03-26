/**
 * NodeDetail — floating popup showing metadata of the clicked graph node.
 * Appears over the graph panel.
 */
function NodeDetail({ node, onClose }) {
  if (!node) return null

  // Fields to always show first (in order)
  const PRIORITY_FIELDS = ['id', 'type', 'customer', 'material', 'quantity', 'amount', 'status']

  // Collect remaining fields (flattened node properties)
  const allFields = Object.entries(node).filter(
    ([k]) => !['x', 'y', 'vx', 'vy', 'fx', 'fy', 'index', 'color', '__indexColor', '__threeObj'].includes(k)
  )

  // Sort: priority fields first, then rest alphabetically
  const prioritized = PRIORITY_FIELDS.flatMap(k => {
    const entry = allFields.find(([key]) => key === k)
    return entry ? [entry] : []
  })
  const rest = allFields.filter(([k]) => !PRIORITY_FIELDS.includes(k))

  const fields = [...prioritized, ...rest]
  const MAX_VISIBLE = 10
  const visible = fields.slice(0, MAX_VISIBLE)
  const hidden = fields.length - MAX_VISIBLE

  // Type badge colors
  const TYPE_COLORS = {
    SalesOrder:      '#4f9cf9',
    Delivery:        '#f97b4f',
    BillingDocument: '#a78bfa',
    JournalEntry:    '#34d399',
  }
  const badgeColor = TYPE_COLORS[node.type] || '#777'

  return (
    <div className="node-detail">
      <button className="node-detail-close" onClick={onClose} aria-label="Close">✕</button>

      <div className="node-detail-header">
        <span className="node-type-badge" style={{ background: badgeColor + '22', color: badgeColor, borderColor: badgeColor + '55' }}>
          {node.type}
        </span>
        <h3>{node.label || node.id}</h3>
      </div>

      <div className="node-detail-fields">
        {visible.map(([key, value]) => (
          <div key={key} className="field-row">
            <span className="field-key">{formatKey(key)}</span>
            <span className="field-value">{String(value ?? '—')}</span>
          </div>
        ))}
        {hidden > 0 && (
          <p className="field-hidden">+{hidden} more fields hidden for readability</p>
        )}
      </div>

      <div className="node-connections">
        Connections: <strong>{node.__linkedNodes || '—'}</strong>
      </div>
    </div>
  )
}

function formatKey(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .trim()
    .replace(/\b\w/g, c => c.toUpperCase())
}

export default NodeDetail
