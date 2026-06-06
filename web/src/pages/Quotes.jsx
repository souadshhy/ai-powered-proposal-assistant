
import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import Card from '../components/ui/Card.jsx';
import Empty from '../components/ui/Empty.jsx';
import ErrorBox from '../components/ui/ErrorBox.jsx';
import PageHeader from '../components/layout/PageHeader.jsx';
import Pill from '../components/ui/Pill.jsx';
import Toolbar from '../components/ui/Toolbar.jsx';
import useLoad from '../hooks/useLoad.js';
import { api, formatTry } from '../lib/api.js';

export default function Quotes() {
  const { data, loading, error, reload } = useLoad(api.quotes, []);
  const [selected, setSelected] = useState('');
  const quotes = data?.quotes || [];

  useEffect(() => {
    if (!selected && quotes[0]) setSelected(quotes[0].quote_id);
  }, [quotes, selected]);

  return (
    <>
      <PageHeader title="Teklifler" subtitle="Web paneli ve mobil uygulama aynı quote_id için aynı kalıcı durumu okur." />
      <Toolbar align="end"><button onClick={reload}><RefreshCw size={16} />Yenile</button></Toolbar>
      <ErrorBox error={error} />
      <div className="grid quote-grid">
        <Card>
          <h2>Teklif Listesi</h2>
          {loading ? <Empty text="Yükleniyor..." /> : quotes.map((quote) => <QuoteRow key={quote.quote_id} quote={quote} selected={selected === quote.quote_id} onSelect={() => setSelected(quote.quote_id)} />)}
        </Card>
        {selected && <QuoteDetail quoteId={selected} />}
      </div>
    </>
  );
}

function QuoteRow({ quote, selected, onSelect }) {
  return (
    <button className={`quote-row ${selected ? 'selected' : ''}`} onClick={onSelect}>
      <strong>{quote.quote_id}</strong>
      <span>{quote.customer_id}</span>
      <Pill>{quote.status}</Pill>
    </button>
  );
}

function QuoteDetail({ quoteId }) {
  const { data, error, loading, reload } = useLoad(() => api.quote(quoteId), [quoteId]);
  if (loading) return <Card><Empty text="Teklif yükleniyor..." /></Card>;
  if (error) return <Card><ErrorBox error={error} /></Card>;

  const discounts = data.discounts || [];
  return (
    <Card className="quote-detail">
      <div className="row-between">
        <div><h2>{data.quote_id}</h2><small>{data.customer_name} · {data.customer_price_tier}</small></div>
        <button className="icon-button" onClick={reload} title="Teklifi yenile"><RefreshCw size={16} /></button>
      </div>
      <p className="readonly-note">Admin paneli teklifleri salt-okunur gösterir. Teklif mutasyonları mobil asistan tool-call akışı üzerinden yapılır.</p>
      <div className="quote-items">
        {data.items.map((item) => <QuoteItem key={item.quote_item_id} item={item} />)}
      </div>
      <div className="totals">
        <span>Ara toplam / indirimsiz toplam</span><strong>{formatTry(data.subtotal_try)}</strong>
        {discounts.length ? discounts.map((discount) => <React.Fragment key={discount.rule_id}><span>{discount.description}</span><strong>-{formatTry(discount.amount_try)}</strong></React.Fragment>) : <React.Fragment><span>Uygulanan indirim</span><strong>{formatTry(0)}</strong></React.Fragment>}
        <span>Genel toplam</span><strong>{formatTry(data.total_try)}</strong>
      </div>
    </Card>
  );
}

function QuoteItem({ item }) {
  return (
    <div className="quote-item readonly">
      <div><strong>{item.name_tr}</strong><small>{item.product_id} · Birim fiyat: {formatTry(item.unit_price_try)}</small></div>
      <Pill>Adet: {item.quantity}</Pill>
      <div className="line-total"><small>Satır toplamı</small><strong>{formatTry(item.line_total_try)}</strong></div>
    </div>
  );
}
