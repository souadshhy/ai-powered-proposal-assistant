import React from "react";
export default function ErrorBox({ error }) {
  return error ? <div className="error">{error}</div> : null;
}
