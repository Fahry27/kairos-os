"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  createAIPlan,
  createPromptDryRun,
  dispatchOllama,
  getAICapabilities,
  getAIModels,
  parseAIPlan,
  type AICapabilities,
  type AIParsedPlan,
  type AIPlanResponse,
  type AIPromptDryRunResponse,
  type AIOllamaDispatchResponse,
  type ApiResult,
  type AIProviderModelsResponse,
} from "../lib/api";

function buildContext(rawContext: string): ApiResult<Record<string, unknown>> {
  const trimmed = rawContext.trim();
  if (!trimmed) {
    return { ok: true, data: {} };
  }

  if (trimmed.startsWith("{")) {
    try {
      const parsed = JSON.parse(trimmed) as unknown;
      if (typeof parsed === "object" && parsed !== null && !Array.isArray(parsed)) {
        return { ok: true, data: parsed as Record<string, unknown> };
      }
      return { ok: false, error: "Context JSON must be an object." };
    } catch {
      return { ok: false, error: "Context JSON is invalid." };
    }
  }

  return { ok: true, data: { notes: trimmed } };
}

function planToParseSource(plan: AIPlanResponse) {
  return JSON.stringify(
    {
      summary: plan.summary,
      steps: plan.suggested_steps.map((step) => ({
        title: step.action,
        description: step.rationale,
      })),
      commands: plan.suggested_commands.map((command) => ({
        command_id: command.command_id,
        reason: command.description || command.command_name,
      })),
    },
    null,
    2,
  );
}

function formatModelSize(value?: number | null) {
  if (!value) return null;
  const gib = value / 1024 / 1024 / 1024;
  return `${gib.toFixed(gib >= 10 ? 0 : 1)} GB`;
}

function ResultBadge({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span className={`approvalBadge ${ok ? "approvalBadge-approved" : "approvalBadge-expired"}`}>
      {label}
    </span>
  );
}

function RuntimeSummary({
  capabilities,
  models,
}: {
  capabilities: ApiResult<AICapabilities> | null;
  models: ApiResult<AIProviderModelsResponse> | null;
}) {
  if (!capabilities) {
    return <p className="stateText">Loading runtime...</p>;
  }

  if (!capabilities.ok) {
    return <p className="errorText">{capabilities.error}</p>;
  }

  const caps = capabilities.data;
  const modelCount = models?.ok ? models.data.model_count : caps.model_count;

  return (
    <dl className="statGrid workspaceRuntimeGrid">
      <div>
        <dt>Provider</dt>
        <dd>{caps.provider}</dd>
      </div>
      <div>
        <dt>Models</dt>
        <dd>{modelCount ?? "-"}</dd>
      </div>
      <div>
        <dt>Dispatch</dt>
        <dd>{caps.ollama_dispatch_enabled ? "enabled" : "disabled"}</dd>
      </div>
      <div>
        <dt>Execution</dt>
        <dd>{caps.execution_enabled ? "enabled" : "locked"}</dd>
      </div>
    </dl>
  );
}

function PlanResult({ plan }: { plan: AIPlanResponse }) {
  return (
    <div className="workspaceResultBlock">
      <div className="workspaceResultHeader">
        <h3>Runtime Plan</h3>
        <ResultBadge label="advisory" ok={!plan.execution_enabled} />
      </div>
      <p>{plan.summary}</p>
      <ol className="workspaceStepList">
        {plan.suggested_steps.map((step) => (
          <li key={step.step}>
            <strong>{step.action}</strong>
            <span>{step.rationale}</span>
          </li>
        ))}
      </ol>
      {plan.suggested_commands.length > 0 && (
        <div className="workspaceCommandList">
          {plan.suggested_commands.map((command) => (
            <div key={command.command_id}>
              <strong>{command.command_id}</strong>
              <span>{command.dangerous ? "high risk" : command.category}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DryRunResult({ dryRun }: { dryRun: AIPromptDryRunResponse }) {
  return (
    <div className="workspaceResultBlock">
      <div className="workspaceResultHeader">
        <h3>Prompt Dry-Run</h3>
        <ResultBadge label={`${dryRun.estimated_context_items} items`} ok />
      </div>
      <p>{dryRun.context_summary}</p>
      {dryRun.warnings.length > 0 && (
        <ul className="workspacePlainList">
          {dryRun.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function DispatchResult({ dispatch }: { dispatch: AIOllamaDispatchResponse }) {
  const error = typeof dispatch.raw_response_metadata.error === "string"
    ? dispatch.raw_response_metadata.error
    : null;

  return (
    <div className="workspaceResultBlock">
      <div className="workspaceResultHeader">
        <h3>Local Model Result</h3>
        <ResultBadge label={`${dispatch.latency_ms} ms`} ok={!error} />
      </div>
      {error ? (
        <p className="errorText">{error}</p>
      ) : (
        <pre className="workspaceResponseText">{dispatch.response_text || "No response text."}</pre>
      )}
    </div>
  );
}

function ParsedPlanResult({ parsedPlan }: { parsedPlan: AIParsedPlan }) {
  return (
    <div className="workspaceResultBlock">
      <div className="workspaceResultHeader">
        <h3>Parsed Plan</h3>
        <ResultBadge label={`${parsedPlan.command_suggestions.length} commands`} ok />
      </div>
      <p>{parsedPlan.summary}</p>
      <ol className="workspaceStepList">
        {parsedPlan.steps.map((step) => (
          <li key={`${step.index}-${step.title}`}>
            <strong>{step.title}</strong>
            <span>{step.description || "No description."}</span>
          </li>
        ))}
      </ol>
      {parsedPlan.command_suggestions.length > 0 && (
        <div className="workspaceCommandList">
          {parsedPlan.command_suggestions.map((command) => (
            <div key={command.command_id}>
              <strong>{command.command_id}</strong>
              <span>{command.dangerous ? "high risk" : "approval required"}</span>
            </div>
          ))}
        </div>
      )}
      {parsedPlan.parser_warnings.length > 0 && (
        <ul className="workspacePlainList">
          {parsedPlan.parser_warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function AIWorkspace() {
  const [capabilities, setCapabilities] = useState<ApiResult<AICapabilities> | null>(null);
  const [models, setModels] = useState<ApiResult<AIProviderModelsResponse> | null>(null);
  const [goal, setGoal] = useState("");
  const [contextText, setContextText] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCreatingApprovals, setIsCreatingApprovals] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [plan, setPlan] = useState<AIPlanResponse | null>(null);
  const [dryRun, setDryRun] = useState<AIPromptDryRunResponse | null>(null);
  const [dispatch, setDispatch] = useState<AIOllamaDispatchResponse | null>(null);
  const [parsedPlan, setParsedPlan] = useState<AIParsedPlan | null>(null);
  const [parseSourceText, setParseSourceText] = useState("");

  useEffect(() => {
    let mounted = true;
    Promise.all([getAICapabilities(), getAIModels()]).then(([nextCaps, nextModels]) => {
      if (mounted) {
        setCapabilities(nextCaps);
        setModels(nextModels);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  const modelOptions = useMemo(() => {
    const discovered = models?.ok
      ? models.data.models.map((model) => model.model || model.name).filter(Boolean)
      : [];
    const configured = capabilities?.ok && capabilities.data.model ? [capabilities.data.model] : [];
    return [...new Set([...discovered, ...configured])];
  }, [capabilities, models]);

  useEffect(() => {
    if (!selectedModel && modelOptions.length > 0) {
      setSelectedModel(modelOptions[0]);
    }
  }, [modelOptions, selectedModel]);

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedGoal = goal.trim();
    if (!trimmedGoal) {
      setError("Goal is required.");
      return;
    }

    const contextResult = buildContext(contextText);
    if (!contextResult.ok) {
      setError(contextResult.error);
      return;
    }

    setIsGenerating(true);
    setError(null);
    setSuccess(null);
    setPlan(null);
    setDryRun(null);
    setDispatch(null);
    setParsedPlan(null);
    setParseSourceText("");

    const errors: string[] = [];

    try {
      const nextPlan = await createAIPlan(trimmedGoal, contextResult.data);
      if (nextPlan.ok) {
        setPlan(nextPlan.data);
      } else {
        errors.push(`Runtime plan failed: ${nextPlan.error}`);
      }

      const nextDryRun = await createPromptDryRun({
        user_goal: trimmedGoal,
        context: contextResult.data,
        preferred_model: selectedModel || null,
      });
      if (nextDryRun.ok) {
        setDryRun(nextDryRun.data);
      } else {
        errors.push(`Prompt dry-run failed: ${nextDryRun.error}`);
      }

      let sourceText = "";
      if (capabilities?.ok && capabilities.data.ollama_dispatch_enabled && selectedModel) {
        const nextDispatch = await dispatchOllama({
          user_goal: trimmedGoal,
          context: contextResult.data,
          model: selectedModel,
          parse_response: false,
          create_approval_requests: false,
        });
        if (nextDispatch.ok) {
          setDispatch(nextDispatch.data);
          sourceText = nextDispatch.data.response_text.trim();
        } else {
          errors.push(`Local dispatch failed: ${nextDispatch.error}`);
        }
      }

      if (!sourceText && nextPlan.ok) {
        sourceText = planToParseSource(nextPlan.data);
      }

      if (sourceText) {
        const parsed = await parseAIPlan({
          user_goal: trimmedGoal,
          model: selectedModel || null,
          response_text: sourceText,
          create_approval_requests: false,
        });
        if (parsed.ok) {
          setParsedPlan(parsed.data);
          setParseSourceText(sourceText);
        } else {
          errors.push(`Parse plan failed: ${parsed.error}`);
        }
      }

      if (errors.length > 0) {
        setError(errors.join(" "));
      } else {
        setSuccess("Plan generated.");
      }
    } finally {
      setIsGenerating(false);
    }
  }

  async function handleCreateApprovals() {
    if (!parseSourceText || !parsedPlan) return;
    setIsCreatingApprovals(true);
    setError(null);
    setSuccess(null);

    try {
      const created = await parseAIPlan({
        user_goal: goal.trim(),
        model: selectedModel || null,
        response_text: parseSourceText,
        create_approval_requests: true,
      });
      if (created.ok) {
        setParsedPlan(created.data);
        const count = created.data.approval_requests.length;
        setSuccess(`${count} approval request${count === 1 ? "" : "s"} created.`);
      } else {
        setError(`Create approvals failed: ${created.error}`);
      }
    } finally {
      setIsCreatingApprovals(false);
    }
  }

  return (
    <section className="card cardWide workspaceShell">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">AI Workspace</p>
          <h2>Workspace</h2>
        </div>
        <div className="approvalBadgeRow">
          <ResultBadge label="no agents" ok />
          <ResultBadge label="no execution" ok />
        </div>
      </div>

      <RuntimeSummary capabilities={capabilities} models={models} />

      <div className="workspaceLayout">
        <form className="workspaceForm" onSubmit={handleGenerate}>
          <label>
            <span>Goal</span>
            <textarea
              onChange={(event) => setGoal(event.target.value)}
              placeholder="Back up Kairos data and confirm health"
              rows={4}
              value={goal}
            />
          </label>

          <label>
            <span>Context</span>
            <textarea
              onChange={(event) => setContextText(event.target.value)}
              placeholder="Plain notes or a JSON object"
              rows={5}
              value={contextText}
            />
          </label>

          <label>
            <span>Local model</span>
            {modelOptions.length > 0 ? (
              <select
                onChange={(event) => setSelectedModel(event.target.value)}
                value={selectedModel}
              >
                {modelOptions.map((modelName) => {
                  const manifest = models?.ok
                    ? models.data.models.find((model) => model.model === modelName || model.name === modelName)
                    : undefined;
                  const size = formatModelSize(manifest?.size);
                  return (
                    <option key={modelName} value={modelName}>
                      {size ? `${modelName} (${size})` : modelName}
                    </option>
                  );
                })}
              </select>
            ) : (
              <input
                onChange={(event) => setSelectedModel(event.target.value)}
                placeholder="No local model discovered"
                value={selectedModel}
              />
            )}
          </label>

          <div className="recordActions">
            <button className="btnSmall btnSave" disabled={isGenerating} type="submit">
              {isGenerating ? "Generating..." : "Generate plan"}
            </button>
            {parsedPlan && parsedPlan.command_suggestions.length > 0 && (
              <button
                className="btnSmall btnOutline"
                disabled={isCreatingApprovals}
                onClick={handleCreateApprovals}
                type="button"
              >
                {isCreatingApprovals ? "Creating..." : "Create approval requests"}
              </button>
            )}
          </div>

          {success && <p className="successText">{success}</p>}
          {error && <p className="errorText">{error}</p>}
        </form>

        <div className="workspaceResults">
          {!plan && !dryRun && !dispatch && !parsedPlan ? (
            <div className="approvalDetails approvalDetailsEmpty">
              <p className="eyebrow">Plan</p>
              <h3>No plan generated</h3>
            </div>
          ) : (
            <>
              {plan && <PlanResult plan={plan} />}
              {dryRun && <DryRunResult dryRun={dryRun} />}
              {dispatch && <DispatchResult dispatch={dispatch} />}
              {parsedPlan && <ParsedPlanResult parsedPlan={parsedPlan} />}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
