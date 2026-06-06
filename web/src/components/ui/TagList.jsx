import React from "react";
export default function TagList({ tags = [] }) {
  return (
    <div className="tags">
      {(tags || []).slice(0, 4).map((tag) => (
        <span key={tag}>{tag}</span>
      ))}
    </div>
  );
}
