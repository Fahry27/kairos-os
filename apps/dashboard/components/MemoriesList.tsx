"use client";

import { useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";
import {
  createMemory,
  deleteMemory,
  getMemories,
  updateMemory,
  type ApiResult,
  type Memory,
} from "../lib/api";

function MemoryItem({
  memory,
  onMutated,
}: {
  memory: Memory;
  onMutated: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const [editType, setEditType] = useState(memory.type);
  const [editContent, setEditContent] = useState(memory.content);
  const [editSource, setEditSource] = useState(memory.source ?? "");
  const [editTags, setEditTags] = useState(memory.tags?.join(", ") ?? "");
  const [editImportance, setEditImportance] = useState(memory.importance);

  function startEditing() {
    setEditType(memory.type);
    setEditContent(memory.content);
    setEditSource(memory.source ?? "");
    setEditTags(memory.tags?.join(", ") ?? "");
    setEditImportance(memory.importance);
    setActionError(null);
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
    setActionError(null);
  }

  async function handleSave() {
    const trimmed = editContent.trim();
    if (!trimmed) {
      setActionError("Content is required.");
      return;
    }

    const parsedTags = editTags
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    setIsSaving(true);
    const result = await updateMemory(memory.id, {
      type: editType,
      content: trimmed,
      source: editSource.trim() || null,
      tags: parsedTags.length ? parsedTags : null,
      importance: editImportance,
    });

    if (result.ok) {
      setEditing(false);
      onMutated();
    } else {
      setActionError(`Save failed: ${result.error}`);
    }
    setIsSaving(false);
  }

  async function handleDelete() {
    if (!window.confirm("Delete this memory? This cannot be undone.")) {
      return;
    }

    const result = await deleteMemory(memory.id);
    if (result.ok) {
      onMutated();
    } else {
      setActionError(`Delete failed: ${result.error}`);
    }
  }

  if (editing) {
    return (
      <article className="record" key={memory.id}>
        <div className="editForm">
          <div className="editFormFooter">
            <label>
              <span>Type</span>
              <select onChange={(e) => setEditType(e.target.value)} value={editType}>
                <option value="note">Note</option>
                <option value="technical_context">Technical Context</option>
                <option value="decision">Decision</option>
              </select>
            </label>
            <label>
              <span>Importance</span>
              <select onChange={(e) => setEditImportance(e.target.value)} value={editImportance}>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="low">Low</option>
              </select>
            </label>
          </div>
          <label>
            <span>Content</span>
            <textarea
              onChange={(e) => setEditContent(e.target.value)}
              rows={3}
              value={editContent}
            />
          </label>
          <div className="editFormFooter">
            <label>
              <span>Source</span>
              <input
                maxLength={255}
                onChange={(e) => setEditSource(e.target.value)}
                value={editSource}
              />
            </label>
            <label>
              <span>Tags</span>
              <input
                onChange={(e) => setEditTags(e.target.value)}
                placeholder="comma, separated"
                value={editTags}
              />
            </label>
            <button className="btnSmall btnSave" disabled={isSaving} onClick={handleSave} type="button">
              {isSaving ? "Saving..." : "Save"}
            </button>
            <button className="btnSmall btnOutline" disabled={isSaving} onClick={cancelEditing} type="button">
              Cancel
            </button>
          </div>
          {actionError && <p className="errorText">{actionError}</p>}
        </div>
      </article>
    );
  }

  return (
    <article className="record" key={memory.id}>
      <div className="recordHeader">
        <h3>{memory.type}</h3>
        <span className="pill">{memory.importance}</span>
      </div>
      <p>{memory.content}</p>
      <div className="metaRow">
        <span>Source: {memory.source ?? "-"}</span>
        <span>Tags: {memory.tags?.length ? memory.tags.join(", ") : "-"}</span>
      </div>
      <div className="recordActions">
        <button className="btnSmall btnOutline" onClick={startEditing} type="button" aria-label={`Edit memory ${memory.type}`}>
          Edit
        </button>
        <button className="btnSmall btnDanger" onClick={handleDelete} type="button" aria-label={`Delete memory ${memory.type}`}>
          Delete
        </button>
      </div>
      {actionError && <p className="errorText">{actionError}</p>}
    </article>
  );
}

export function MemoriesList() {
  const searchParams = useSearchParams();
  const focusedProjectId = searchParams.get("project_id");

  const [result, setResult] = useState<ApiResult<Memory[]> | null>(null);
  const [type, setType] = useState("note");
  const [content, setContent] = useState("");
  const [source, setSource] = useState("");
  const [tags, setTags] = useState("");
  const [importance, setImportance] = useState("normal");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterImportance, setFilterImportance] = useState("all");

  useEffect(() => {
    let mounted = true;

    loadMemories().then((nextResult) => {
      if (mounted) {
        setResult(nextResult);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  async function loadMemories() {
    return getMemories();
  }

  async function refresh() {
    setResult(await loadMemories());
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setSubmitError("Memory content is required.");
      return;
    }

    setIsSubmitting(true);
    const parsedTags = tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean);

    const created = await createMemory({
      type,
      content: trimmedContent,
      source: source.trim() || undefined,
      tags: parsedTags.length ? parsedTags : undefined,
      importance,
      project_id: focusedProjectId || undefined,
    });

    if (created.ok) {
      setType("note");
      setContent("");
      setSource("");
      setTags("");
      setImportance("normal");
      await refresh();
    } else {
      setSubmitError(`Unable to create memory: ${created.error}`);
    }

    setIsSubmitting(false);
  }

  const filteredMemories = result?.ok
    ? result.data.filter((m) => {
        if (focusedProjectId && m.project_id !== focusedProjectId) return false;
        const q = searchQuery.toLowerCase();
        const matchesSearch =
          m.content.toLowerCase().includes(q) ||
          (m.source?.toLowerCase() || "").includes(q) ||
          (m.tags?.join(" ").toLowerCase() || "").includes(q) ||
          m.type.toLowerCase().includes(q);
        const matchesType = filterType === "all" || m.type === filterType;
        const matchesImportance = filterImportance === "all" || m.importance === filterImportance;
        return matchesSearch && matchesType && matchesImportance;
      })
    : [];

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Memories</p>
          <h2>Knowledge</h2>
        </div>
      </div>
      <form className="resourceForm" onSubmit={handleSubmit}>
        <div className="formFooter">
          <label>
            <span>Type</span>
            <select onChange={(event) => setType(event.target.value)} value={type}>
              <option value="note">Note</option>
              <option value="technical_context">Technical Context</option>
              <option value="decision">Decision</option>
            </select>
          </label>
          <label>
            <span>Importance</span>
            <select onChange={(event) => setImportance(event.target.value)} value={importance}>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="low">Low</option>
            </select>
          </label>
        </div>
        <label>
          <span>Content</span>
          <textarea
            onChange={(event) => setContent(event.target.value)}
            placeholder="Capture useful context"
            rows={3}
            value={content}
          />
        </label>
        <div className="formFooter">
          <label>
            <span>Source</span>
            <input
              maxLength={255}
              onChange={(event) => setSource(event.target.value)}
              placeholder="Optional"
              value={source}
            />
          </label>
          <label>
            <span>Tags</span>
            <input
              onChange={(event) => setTags(event.target.value)}
              placeholder="comma, separated"
              value={tags}
            />
          </label>
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Creating..." : "Create Memory"}
          </button>
        </div>
        {submitError && <p className="errorText">{submitError}</p>}
      </form>
      {!result && <p className="stateText">Loading memories...</p>}
      {result && !result.ok && <p className="errorText">Unable to load memories: {result.error}</p>}
      {result?.ok && result.data.length === 0 && (
        <p className="stateText">No memories yet. Captured context will appear here.</p>
      )}
      {result?.ok && result.data.length > 0 && (
        <div className="filtersRow">
          <label>
            <span>Search Memories</span>
            <input
              placeholder="Search content, source, tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
          <label>
            <span>Type</span>
            <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
              <option value="all">All Types</option>
              <option value="note">Note</option>
              <option value="technical_context">Technical Context</option>
              <option value="decision">Decision</option>
            </select>
          </label>
          <label>
            <span>Importance</span>
            <select value={filterImportance} onChange={(e) => setFilterImportance(e.target.value)}>
              <option value="all">All Importances</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="low">Low</option>
            </select>
          </label>
        </div>
      )}
      {result?.ok && result.data.length > 0 && filteredMemories.length === 0 && (
        <p className="stateText">No memories found matching your criteria.</p>
      )}
      {result?.ok && filteredMemories.length > 0 && (
        <div className="stack">
          {filteredMemories.map((memory) => (
            <MemoryItem key={memory.id} memory={memory} onMutated={refresh} />
          ))}
        </div>
      )}
    </section>
  );
}
