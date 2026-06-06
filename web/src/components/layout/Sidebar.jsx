import React from "react";
import { NAV_ITEMS } from "../../constants/navigation.js";

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">BR</div>
        <div>
          <strong>The Blue Red</strong>
          <span>Admin Panel</span>
        </div>
      </div>

      <nav>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            className={activePage === item.id ? "active" : ""}
            onClick={() => onNavigate(item.id)}
          >
            <item.icon size={18} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="side-note">
        Mobil uygulamada yapılan teklif mutasyonları burada aynı kalıcı durumdan
        okunur.
      </div>
    </aside>
  );
}
