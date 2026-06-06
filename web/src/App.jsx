import React, { useState } from 'react';
import Sidebar from './components/layout/Sidebar.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Products from './pages/Products.jsx';
import Knowledge from './pages/Knowledge.jsx';
import Quotes from './pages/Quotes.jsx';
import Logs from './pages/Logs.jsx';
import Sessions from './pages/Sessions.jsx';

const PAGES = {
  dashboard: Dashboard,
  products: Products,
  knowledge: Knowledge,
  quotes: Quotes,
  logs: Logs,
  sessions: Sessions,
};

export default function App() {
  const [page, setPage] = useState('dashboard');
  const ActivePage = PAGES[page] || Dashboard;

  return (
    <div className="app-shell">
      <Sidebar activePage={page} onNavigate={setPage} />
      <main className="main">
        <ActivePage />
      </main>
    </div>
  );
}
