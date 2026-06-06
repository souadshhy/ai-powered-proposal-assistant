import React from "react";
import { useState } from "react";
import { RefreshCw } from "lucide-react";
import Card from "../components/ui/Card.jsx";
import Empty from "../components/ui/Empty.jsx";
import ErrorBox from "../components/ui/ErrorBox.jsx";
import PageHeader from "../components/layout/PageHeader.jsx";
import Pill from "../components/ui/Pill.jsx";
import Toolbar from "../components/ui/Toolbar.jsx";
import useLoad from "../hooks/useLoad.js";
import { api } from "../lib/api.js";

export default function Logs() {
  const { data, loading, error, reload } = useLoad(api.toolLogs, []);
  const logs = data?.logs || [];
  const quoteIds = Array.from(
    new Set(logs.map((log) => log.quote_id).filter(Boolean)),
  );
  const [quoteFilter, setQuoteFilter] = useState("");
  const visibleLogs = quoteFilter
    ? logs.filter((log) => log.quote_id === quoteFilter)
    : logs;

  return (
    <>
      <PageHeader
        title="Tool Call Logları"
        subtitle="Varsayılan görünüm en son tool-call kayıtlarını zamana göre gösterir; istersen quote_id ile filtreleyebilirsin."
      />
      <Toolbar>
        <select
          value={quoteFilter}
          onChange={(e) => setQuoteFilter(e.target.value)}
        >
          <option value="">Tüm quote logları</option>
          {quoteIds.map((id) => (
            <option key={id} value={id}>
              {id}
            </option>
          ))}
        </select>
        <button onClick={reload}>
          <RefreshCw size={16} />
          Yenile
        </button>
      </Toolbar>
      <ErrorBox error={error} />
      {loading ? (
        <Empty text="Yükleniyor..." />
      ) : (
        <LogTimeline logs={visibleLogs} />
      )}
    </>
  );
}

function LogTimeline({ logs }) {
  return (
    <div className="timeline">
      {logs.map((log) => (
        <Card key={log.id} className="log-card">
          <div className="row-between">
            <div>
              <h2>
                #{log.sequence} {log.tool_name}
              </h2>
              <small>
                {log.session_id} · {log.quote_id}
              </small>
            </div>
            <Pill tone={log.success ? "success" : "danger"}>
              {log.success ? "success" : "error"}
            </Pill>
          </div>
          <details>
            <summary>Payload</summary>
            <pre>
              {JSON.stringify(
                {
                  input: log.input_payload,
                  output: log.output_payload,
                  delta: log.quote_delta,
                },
                null,
                2,
              )}
            </pre>
          </details>
        </Card>
      ))}
    </div>
  );
}
