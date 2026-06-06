import React from "react";
export default function Input({
  label,
  value,
  onChange,
  type = "text",
  error,
}) {
  return (
    <label>
      {label}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
      {error && <small className="field-error">{error}</small>}
    </label>
  );
}
