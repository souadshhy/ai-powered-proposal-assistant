from sqlalchemy.orm import Session
from app.models.entities import ToolCallLog

class ToolLogger:
    def __init__(self, db: Session, session_id: str | None, quote_id: str | None):
        self.db = db
        self.session_id = session_id
        self.quote_id = quote_id
        self.sequence = 0
        self.events = []

    def log(self, tool_name: str, input_payload: dict, success: bool, output_payload: dict, quote_delta: dict | None = None):
        self.sequence += 1
        self.events.append({"type": "tool_start", "data": {"sequence": self.sequence + 1, "tool": tool_name, "input_summary": str(input_payload)[:300]}})
        row = ToolCallLog(
            session_id=self.session_id,
            quote_id=self.quote_id,
            sequence=self.sequence,
            tool_name=tool_name,
            input_summary=str(input_payload)[:500],
            input_payload=input_payload,
            success=success,
            output_payload=output_payload,
            quote_delta=quote_delta,
        )
        self.db.add(row)
        self.db.commit()
        self.events.append({"type": "tool_result", "data": {"sequence": self.sequence, "tool": tool_name, "success": success, "quote_delta": quote_delta, "sources": _extract_sources(output_payload)}})
        return row

def _extract_sources(payload):
    sources=[]
    def walk(x):
        if isinstance(x, dict):
            for k,v in x.items():
                if k in {"product_id", "knowledge_id"}: sources.append(v)
                walk(v)
        elif isinstance(x, list):
            for y in x: walk(y)
    walk(payload)
    return sorted(set(str(s) for s in sources))
