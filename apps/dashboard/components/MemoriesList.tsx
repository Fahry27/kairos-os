"use client";

import { type FormEvent, useEffect, useState } from "react";
import { createMemory, getMemories, type ApiResult, type Memory } from "../lib/api";

export function MemoriesList() {
  const [result, setResult] = useState<ApiResult<Memory[]> | null>(null);
  const [type, setType] = useState("note");
  const [content, setContent] = useState("");
  const [source, setSource] = useState("");
  const [tags, setTags] = useState("");
  const [importance, setImportance] = useState("normal");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
    });

    if (created.ok) {
      setType("note");
      setContent("");
      setSource("");
      setTags("");
      setImportance("normal");
      setResult(await loadMemories());
    } else {
      setSubmitError(`Unable to create memory: ${created.error}`);
    }

    setIsSubmitting(false);
  }

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
        <div className="stack">
          {result.data.map((memory) => (
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
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
