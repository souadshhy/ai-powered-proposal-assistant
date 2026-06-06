import React from "react";
import { Search } from "lucide-react";

export default function SearchBox({ value, onChange, placeholder }) {
  return (
    <label className="search">
      <Search size={16} />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}
