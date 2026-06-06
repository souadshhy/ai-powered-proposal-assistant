from sqlalchemy.orm import Session
from app.models.entities import KnowledgeEntry
from app.orchestrators.text_utils import cosine_rank

def knowledge_to_dict(k: KnowledgeEntry, score: float | None = None):
    d = {
        "knowledge_id": k.knowledge_id,
        "topic": k.topic,
        "locale": k.locale,
        "title": k.title,
        "body": k.body,
        "source": k.source,
        "applies_to": k.applies_to,
        "effective_from": k.effective_from,
    }
    if score is not None:
        d["match_score"] = score
    return d

def knowledge_text(k: KnowledgeEntry):
    return " ".join([k.topic, k.title, k.body, " ".join(k.applies_to or []), k.source])

def get_knowledge_entries(db: Session, query: str = "", topic: str | None = None, applies_to: str | None = None, limit: int = 3):
    q = db.query(KnowledgeEntry).filter(KnowledgeEntry.locale == "tr")
    if topic:
        q = q.filter(KnowledgeEntry.topic == topic)
    rows = q.all()
    if applies_to:
        rows = [k for k in rows if applies_to in (k.applies_to or [])]
    if query:
        ranked = cosine_rank(query, [knowledge_text(k) for k in rows])
        out = [(rows[i], s) for i, s in ranked if s > 0]
        if not out:
            out = [(k, 0.0) for k in rows]
    else:
        out = [(k, 0.0) for k in rows]
    return [knowledge_to_dict(k, s) for k, s in out[:limit]]
