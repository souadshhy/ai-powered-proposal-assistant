import React from "react";
export default function Toolbar({ children, align = "start" }) {
  return (
    <div className={`toolbar ${align === "end" ? "toolbar-end" : ""}`}>
      {children}
    </div>
  );
}
