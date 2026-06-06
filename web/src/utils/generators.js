export function generateProductId(category) {
  const prefixMap = {
    barcode_scanner: 'BC',
    pos_terminal: 'POS',
    receipt_printer: 'RP',
    label_printer: 'LP',
    software: 'SW',
    software_license: 'SW',
    service: 'SRV',
    accessory: 'ACC',
    bundle: 'BND',
  };
  const prefix = prefixMap[category] || 'PRD';
  return `PRD-${prefix}-${Date.now().toString().slice(-6)}`;
}

export function generateKnowledgeId(topic) {
  const map = {
    return_policy: 'RET',
    delivery_policy: 'DEL',
    warranty: 'WAR',
    compatibility: 'COM',
    service_policy: 'SRV',
    discount_policy: 'DIS',
    quote_validity: 'QUOTE',
    quote_idempotency: 'IDEM',
    stock_rule: 'STK',
    price_ceiling: 'PRICE',
    fallback: 'FB',
  };
  return `KNE-${map[topic] || 'GEN'}-${Date.now().toString().slice(-6)}`;
}

export function generateKnowledgePath(topic, effectiveFrom) {
  const map = {
    return_policy: 'returns',
    delivery_policy: 'delivery',
    warranty: 'warranty',
    compatibility: 'compatibility',
    service_policy: 'service',
    discount_policy: 'discounts',
    quote_validity: 'quotes',
    quote_idempotency: 'quotes',
    stock_rule: 'stock',
    price_ceiling: 'pricing',
    fallback: 'fallback',
  };
  const date = effectiveFrom || new Date().toISOString().slice(0, 10);
  const ym = date.slice(0, 7);
  return `policy/${map[topic] || topic}/v${ym}`;
}
