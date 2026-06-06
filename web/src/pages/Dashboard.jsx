import React from "react";
import { Activity, Boxes, ClipboardList, TerminalSquare } from "lucide-react";
import Card from "../components/ui/Card.jsx";
import PageHeader from "../components/layout/PageHeader.jsx";
import useLoad from "../hooks/useLoad.js";
import { api } from "../lib/api.js";

export default function Dashboard() {
  const { data: products } = useLoad(
    () => api.products({ in_stock_only: false }),
    [],
  );
  const { data: quotes } = useLoad(() => api.quotes(), []);
  const { data: logs } = useLoad(() => api.toolLogs(), []);
  const { data: sessions } = useLoad(() => api.sessions(), []);

  const stats = [
    ["Ürün", products?.products?.length ?? "—", Boxes],
    ["Teklif", quotes?.quotes?.length ?? "—", ClipboardList],
    ["Tool Log", logs?.logs?.length ?? "—", TerminalSquare],
    ["Oturum", sessions?.sessions?.length ?? "—", Activity],
  ];

  return (
    <>
      <PageHeader
        title="Admin Dashboard"
        subtitle="Ürün, bilgi kaydı, teklif ve tool-call izleme paneli."
      />
      <div className="stats-grid">
        {stats.map(([label, value, Icon]) => (
          <Card key={label} className="stat">
            <Icon />
            <span>{label}</span>
            <strong>{value}</strong>
          </Card>
        ))}
      </div>
    </>
  );
}
