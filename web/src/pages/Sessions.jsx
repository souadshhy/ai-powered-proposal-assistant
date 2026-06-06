import React from "react";
import { RefreshCw } from "lucide-react";
import Empty from "../components/ui/Empty.jsx";
import ErrorBox from "../components/ui/ErrorBox.jsx";
import PageHeader from "../components/layout/PageHeader.jsx";
import Pill from "../components/ui/Pill.jsx";
import Toolbar from "../components/ui/Toolbar.jsx";
import useLoad from "../hooks/useLoad.js";
import { api } from "../lib/api.js";

export default function Sessions() {
  const { data, loading, error, reload } = useLoad(api.sessions, []);
  const sessions = data?.sessions || [];

  return (
    <>
      <PageHeader
        title="Sohbet Oturumları"
        subtitle="Mobil chat oturumlarını admin tarafından salt-okunur görüntüleme."
      />
      <Toolbar align="end">
        <button onClick={reload}>
          <RefreshCw size={16} />
          Yenile
        </button>
      </Toolbar>
      <ErrorBox error={error} />
      {loading ? (
        <Empty text="Yükleniyor..." />
      ) : (
        <SessionsTable sessions={sessions} />
      )}
    </>
  );
}

function SessionsTable({ sessions }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Session</th>
            <th>Quote</th>
            <th>Customer</th>
            <th>Channel</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => (
            <tr key={session.session_id}>
              <td>
                <strong>{session.session_id}</strong>
              </td>
              <td>{session.quote_id}</td>
              <td>{session.customer_id}</td>
              <td>
                <Pill>{session.channel}</Pill>
              </td>
              <td>{session.created_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
