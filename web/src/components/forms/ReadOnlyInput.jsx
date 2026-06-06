import React from "react";
export default function ReadOnlyInput({ label, value, error }) {
  return (
    <label>
      {label}
      <input className="readonly-input" value={value} readOnly />
      {error && <small className="field-error">{error}</small>}
    </label>
  );
}
