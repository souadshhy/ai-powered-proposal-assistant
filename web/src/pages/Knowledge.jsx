import React from "react";
import { useMemo, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import Card from "../components/ui/Card.jsx";
import Empty from "../components/ui/Empty.jsx";
import ErrorBox from "../components/ui/ErrorBox.jsx";
import Input from "../components/forms/Input.jsx";
import PageHeader from "../components/layout/PageHeader.jsx";
import Pill from "../components/ui/Pill.jsx";
import ReadOnlyInput from "../components/forms/ReadOnlyInput.jsx";
import SearchBox from "../components/ui/SearchBox.jsx";
import TagList from "../components/ui/TagList.jsx";
import Toolbar from "../components/ui/Toolbar.jsx";
import { KNOWLEDGE_TOPIC_LABELS } from "../constants/knowledge.js";
import useLoad from "../hooks/useLoad.js";
import { api } from "../lib/api.js";
import {
  generateKnowledgeId,
  generateKnowledgePath,
} from "../utils/generators.js";

export default function Knowledge() {
  const [q, setQ] = useState("");
  const [topic, setTopic] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const { data, loading, error, reload } = useLoad(
    () => api.knowledge({ q, topic }),
    [q, topic],
  );
  const entries = data?.entries || [];
  const topics = useMemo(
    () =>
      [...new Set(entries.map((entry) => entry.topic).filter(Boolean))].sort(),
    [entries],
  );
  const appliesToValues = useMemo(
    () =>
      [...new Set(entries.flatMap((entry) => entry.applies_to || []))].sort(),
    [entries],
  );

  return (
    <>
      <PageHeader
        title="Bilgi Kayıtları"
        subtitle="Politika, teslimat, garanti, uyumluluk ve fallback kaynaklarını yönetin."
        action={
          <button
            className="primary"
            onClick={() => setShowCreate(!showCreate)}
          >
            <Plus size={16} />
            Yeni Kayıt
          </button>
        }
      />
      <Toolbar>
        <SearchBox
          value={q}
          onChange={setQ}
          placeholder="Politika veya kaynak ara"
        />
        <select value={topic} onChange={(e) => setTopic(e.target.value)}>
          <option value="">Tüm konular</option>
          {topics.map((topicValue) => (
            <option key={topicValue} value={topicValue}>
              {KNOWLEDGE_TOPIC_LABELS[topicValue] || topicValue}
            </option>
          ))}
        </select>
        <button onClick={reload}>
          <RefreshCw size={16} />
          Yenile
        </button>
      </Toolbar>
      {showCreate && (
        <KnowledgeForm
          existingTopics={topics}
          appliesToValues={appliesToValues}
          onCreated={() => {
            setShowCreate(false);
            reload();
          }}
        />
      )}
      <ErrorBox error={error} />
      {loading ? (
        <Empty text="Yükleniyor..." />
      ) : (
        <KnowledgeList entries={entries} />
      )}
    </>
  );
}

function KnowledgeList({ entries }) {
  return (
    <div className="knowledge-list">
      {entries.map((entry) => (
        <Card key={entry.knowledge_id}>
          <div className="row-between">
            <div>
              <h2>{entry.title}</h2>
              <small>
                {entry.knowledge_id} · {entry.source}
              </small>
            </div>
            <Pill>{entry.topic}</Pill>
          </div>
          <p>{entry.body}</p>
          <TagList tags={entry.applies_to} />
        </Card>
      ))}
    </div>
  );
}

function KnowledgeForm({
  existingTopics = [],
  appliesToValues = [],
  onCreated,
}) {
  const allTopics = existingTopics.length
    ? existingTopics
    : Object.keys(KNOWLEDGE_TOPIC_LABELS);
  const defaultTopic = allTopics.includes("fallback")
    ? "fallback"
    : allTopics[0];
  const [err, setErr] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [form, setForm] = useState(() =>
    makeKnowledgeDraft(defaultTopic, new Date().toISOString().slice(0, 10)),
  );

  const updateTopic = (topic) =>
    setForm((current) =>
      makeKnowledgeDraft(topic, current.effective_from, current),
    );
  const updateDate = (date) =>
    setForm((current) => makeKnowledgeDraft(current.topic, date, current));
  const toggleAppliesTo = (value) =>
    setForm({
      ...form,
      applies_to: form.applies_to.includes(value)
        ? form.applies_to.filter((item) => item !== value)
        : [...form.applies_to, value],
    });

  const validate = () => {
    const errors = {};
    if (!form.knowledge_id)
      errors.knowledge_id = "Knowledge ID sistem tarafından üretilmelidir.";
    if (!form.title.trim()) errors.title = "Başlık zorunludur.";
    if (!form.topic) errors.topic = "Konu seçilmelidir.";
    if (!form.body.trim()) errors.body = "İçerik zorunludur.";
    if (!form.source) errors.source = "Path sistem tarafından üretilmelidir.";
    if (!form.effective_from)
      errors.effective_from = "Geçerlilik tarihi zorunludur.";
    if (!form.applies_to.length)
      errors.applies_to = "En az bir applies_to değeri seçilmelidir.";
    return errors;
  };

  const submit = async (event) => {
    event.preventDefault();
    setErr("");
    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length) {
      setErr("Lütfen zorunlu alanları düzeltin.");
      return;
    }
    try {
      await api.createKnowledge(form);
      onCreated();
    } catch (error) {
      setErr(error.message);
    }
  };

  return (
    <Card>
      <h2>Yeni Bilgi Kaydı</h2>
      <p className="form-help">
        Bu form mevcut bilgi kaydı yapısını takip eder: knowledge_id, topic,
        locale, title, body, source/path, applies_to ve effective_from. ID ve
        path otomatik üretilir.
      </p>
      <form className="form-grid" onSubmit={submit} noValidate>
        <ReadOnlyInput
          label="Knowledge ID *"
          value={form.knowledge_id}
          error={fieldErrors.knowledge_id}
        />
        <ReadOnlyInput
          label="Path / Source *"
          value={form.source}
          error={fieldErrors.source}
        />
        <Input
          label="Başlık *"
          value={form.title}
          onChange={(value) => setForm({ ...form, title: value })}
          error={fieldErrors.title}
        />
        <label>
          Konu *
          <select
            value={form.topic}
            onChange={(event) => updateTopic(event.target.value)}
          >
            {allTopics.map((topicValue) => (
              <option key={topicValue} value={topicValue}>
                {KNOWLEDGE_TOPIC_LABELS[topicValue] || topicValue}
              </option>
            ))}
          </select>
          {fieldErrors.topic && (
            <small className="field-error">{fieldErrors.topic}</small>
          )}
        </label>
        <Input
          label="Geçerlilik Başlangıcı *"
          type="date"
          value={form.effective_from}
          onChange={updateDate}
          error={fieldErrors.effective_from}
        />
        <ReadOnlyInput label="Locale" value={form.locale} />
        <div className="span2 field-block">
          <label>Applies To *</label>
          <div className="selectable-grid">
            {appliesToValues.map((value) => (
              <button
                type="button"
                key={value}
                className={`select-chip ${form.applies_to.includes(value) ? "selected" : ""}`}
                onClick={() => toggleAppliesTo(value)}
              >
                {value}
              </button>
            ))}
          </div>
          {fieldErrors.applies_to && (
            <small className="field-error">{fieldErrors.applies_to}</small>
          )}
        </div>
        <label className="span2">
          İçerik *
          <textarea
            value={form.body}
            onChange={(event) => setForm({ ...form, body: event.target.value })}
          />
          {fieldErrors.body && (
            <small className="field-error">{fieldErrors.body}</small>
          )}
        </label>
        <button className="primary">Kaydet</button>
      </form>
      <ErrorBox error={err} />
    </Card>
  );
}

function makeKnowledgeDraft(topic, effectiveFrom, previous = {}) {
  const knowledge_id =
    previous.knowledge_id && previous.topic === topic
      ? previous.knowledge_id
      : generateKnowledgeId(topic);
  return {
    knowledge_id,
    topic,
    locale: "tr",
    title: previous.title || "",
    body: previous.body || "",
    source: generateKnowledgePath(topic, effectiveFrom),
    applies_to: previous.applies_to || [],
    effective_from: effectiveFrom,
  };
}
