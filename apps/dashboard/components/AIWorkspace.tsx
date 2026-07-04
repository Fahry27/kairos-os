"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  createDecisionPlan,
  getAIProviderRoute,
  getAIProviderRouterModels,
  type AIProviderRouteResponse,
  type AIProviderRouterModelsResponse,
  type ApiResult,
  type DecisionPath,
  type DecisionPlan,
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
  providerRoute,
  models,
}: {
  providerRoute: ApiResult<AIProviderRouteResponse> | null;
  models: ApiResult<AIProviderRouterModelsResponse> | null;
}) {
  if (!providerRoute) {
    return <p className="stateText">Loading provider router...</p>;
  }

  if (!providerRoute.ok) {
    return <p className="errorText">{providerRoute.error}</p>;
  }

  const route = providerRoute.data;
  const selected = route.selected_provider;
  const modelCount = models?.ok ? models.data.model_count : "-";

  return (
    <dl className="statGrid workspaceRuntimeGrid">
      <div>
        <dt>Provider</dt>
        <dd>{selected?.name ?? "None"}</dd>
      </div>
      <div>
        <dt>Models</dt>
        <dd>{modelCount}</dd>
      </div>
      <div>
        <dt>Dispatch</dt>
        <dd>{route.dispatch_enabled ? "enabled" : "disabled"}</dd>
      </div>
      <div>
        <dt>Policy</dt>
        <dd>{route.policy.mode}</dd>
      </div>
    </dl>
  );
}

function EmptyList({ label }: { label: string }) {
  return <p className="stateText">{label}</p>;
}

function DecisionPathBlock({ label, path }: { label: string; path: DecisionPath }) {
  return (
    <div className="workspaceResultBlock">
      <div className="workspaceResultHeader">
        <h3>{label}</h3>
        <ResultBadge label={`${path.steps.length} steps`} ok />
      </div>
      <h4>{path.title}</h4>
      <p>{path.summary}</p>
      <ol className="workspaceStepList">
        {path.steps.map((step, index) => (
          <li key={`${path.title}-${index}`}>
            <strong>{`Step ${index + 1}`}</strong>
            <span>{step}</span>
          </li>
        ))}
      </ol>
      {path.capability_refs.length > 0 && (
        <div className="workspaceCommandList">
          {path.capability_refs.map((ref) => (
            <div key={`${ref.type}-${ref.id}`}>
              <strong>{ref.id}</strong>
              <span>{ref.type}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DecisionPlanResult({ decisionPlan }: { decisionPlan: DecisionPlan }) {
  return (
    <>
      <div className="workspaceResultHeader">
        <div>
          <p className="eyebrow">DecisionPlan</p>
          <h3>{decisionPlan.goal}</h3>
        </div>
        <div className="approvalBadgeRow">
          <ResultBadge label={decisionPlan.status} ok />
          <ResultBadge label={`${Math.round(decisionPlan.confidence * 100)}% confidence`} ok />
        </div>
      </div>

      <DecisionPathBlock label="Primary Path" path={decisionPlan.primary_path} />

      <div className="workspaceResultBlock">
        <div className="workspaceResultHeader">
          <h3>Alternatives</h3>
          <ResultBadge label={`${decisionPlan.alternatives.length} options`} ok />
        </div>
        {decisionPlan.alternatives.length > 0 ? (
          decisionPlan.alternatives.map((path) => (
            <DecisionPathBlock key={`${path.title}-${path.summary}`} label={path.title} path={path} />
          ))
        ) : (
          <EmptyList label="No alternatives returned." />
        )}
      </div>

      <div className="workspaceResultBlock">
        <h3>Rationale</h3>
        <p>{decisionPlan.rationale}</p>
      </div>

      <div className="workspaceResultBlock">
        <h3>Evidence</h3>
        {decisionPlan.evidence.length > 0 ? (
          <ul className="workspacePlainList">
            {decisionPlan.evidence.map((item) => (
              <li key={`${item.source}-${item.summary}`}>
                <strong>{item.source}</strong>
                <span>{item.summary}</span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyList label="No evidence returned." />
        )}
      </div>

      <div className="workspaceResultBlock">
        <h3>Assumptions</h3>
        {decisionPlan.assumptions.length > 0 ? (
          <ul className="workspacePlainList">
            {decisionPlan.assumptions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <EmptyList label="No assumptions returned." />
        )}
      </div>

      <div className="workspaceResultBlock">
        <h3>Risks</h3>
        {decisionPlan.risks.length > 0 ? (
          <ul className="workspacePlainList">
            {decisionPlan.risks.map((risk) => (
              <li key={`${risk.severity}-${risk.description}`}>
                <strong>{risk.severity}</strong>
                <span>{risk.mitigation ? `${risk.description} Mitigation: ${risk.mitigation}` : risk.description}</span>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyList label="No risks returned." />
        )}
      </div>

      <div className="workspaceResultBlock">
        <h3>Constraints</h3>
        {decisionPlan.constraints.length > 0 ? (
          <ul className="workspacePlainList">
            {decisionPlan.constraints.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <EmptyList label="No constraints returned." />
        )}
      </div>

      <div className="workspaceResultBlock">
        <h3>Success Definition</h3>
        <p>{decisionPlan.success_definition}</p>
      </div>
    </>
  );
}

import { useSearchParams } from "next/navigation";

export function AIWorkspace() {
  const searchParams = useSearchParams();
  
  const [providerRoute, setProviderRoute] = useState<ApiResult<AIProviderRouteResponse> | null>(null);
  const [models, setModels] = useState<ApiResult<AIProviderRouterModelsResponse> | null>(null);
  const [selectedProvider, setSelectedProvider] = useState("auto");
  const [goal, setGoal] = useState("");
  const [contextText, setContextText] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [decisionPlan, setDecisionPlan] = useState<DecisionPlan | null>(null);

  // Initialize and persist workspace context
  useEffect(() => {
    const queryGoal = searchParams.get("goal");
    const queryContext = searchParams.get("context");
    const queryMissionId = searchParams.get("mission_id");
    
    let initialGoal = goal;
    let initialContext = contextText;

    if (queryGoal !== null) {
      initialGoal = queryGoal;
    } else if (!goal) {
      initialGoal = localStorage.getItem("kairos:workspace:goal") || "";
    }
    
    if (queryContext !== null) {
      initialContext = queryContext;
    } else if (queryMissionId !== null) {
      initialContext = JSON.stringify({ mission_id: queryMissionId }, null, 2);
    } else if (!contextText) {
      initialContext = localStorage.getItem("kairos:workspace:context") || "";
    }

    setGoal(initialGoal);
    setContextText(initialContext);
  }, [searchParams]);

  useEffect(() => {
    if (goal || goal === "") localStorage.setItem("kairos:workspace:goal", goal);
    if (contextText || contextText === "") localStorage.setItem("kairos:workspace:context", contextText);
  }, [goal, contextText]);

  useEffect(() => {
    let mounted = true;
    Promise.all([
      getAIProviderRoute(selectedProvider),
      getAIProviderRouterModels(selectedProvider),
    ]).then(([nextRoute, nextModels]) => {
      if (mounted) {
        setProviderRoute(nextRoute);
        setModels(nextModels);
      }
    });
    return () => {
      mounted = false;
    };
  }, [selectedProvider]);

  const modelOptions = useMemo(() => {
    const discovered = models?.ok
      ? models.data.models.map((model) => model.model || model.name).filter(Boolean)
      : [];
    const configured =
      providerRoute?.ok && providerRoute.data.selected_provider?.configured_model
        ? [providerRoute.data.selected_provider.configured_model]
        : [];
    return [...new Set([...discovered, ...configured])];
  }, [models, providerRoute]);

  const providerOptions = useMemo(
    () => (providerRoute?.ok ? providerRoute.data.providers : []),
    [providerRoute],
  );

  useEffect(() => {
    if (modelOptions.length === 0 && selectedModel) {
      setSelectedModel("");
    } else if (modelOptions.length > 0 && !modelOptions.includes(selectedModel)) {
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
    setDecisionPlan(null);

    try {
      const nextDecisionPlan = await createDecisionPlan({
        goal: trimmedGoal,
        context: contextResult.data,
        provider_id: selectedProvider === "auto" ? null : selectedProvider,
        model: selectedModel || null,
      });
      if (nextDecisionPlan.ok) {
        setDecisionPlan(nextDecisionPlan.data);
        setSuccess("DecisionPlan generated.");
      } else {
        setError(`DecisionPlan generation failed: ${nextDecisionPlan.error}`);
      }
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <section className="card cardWide workspaceShell">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">AI Workspace</p>
          <h2>Decision Planner</h2>
        </div>
        <div className="approvalBadgeRow">
          <ResultBadge label="read-only" ok />
          <ResultBadge label="no execution" ok />
        </div>
      </div>

      <RuntimeSummary providerRoute={providerRoute} models={models} />

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
            <span>Provider</span>
            <select
              onChange={(event) => {
                setSelectedProvider(event.target.value);
                setSelectedModel("");
              }}
              value={selectedProvider}
            >
              <option value="auto">Auto provider</option>
              {providerOptions.map((provider) => (
                <option key={provider.id} value={provider.id}>
                  {provider.name} ({provider.status})
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Model</span>
            {modelOptions.length > 0 ? (
              <select
                onChange={(event) => setSelectedModel(event.target.value)}
                value={selectedModel}
              >
                {modelOptions.map((modelName) => {
                  const manifest = models?.ok
                    ? models.data.models.find(
                        (model) => model.model === modelName || model.name === modelName,
                      )
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
                placeholder="No model discovered"
                value={selectedModel}
              />
            )}
          </label>

          <div className="recordActions">
            <button className="btnSmall btnSave" disabled={isGenerating} type="submit">
              {isGenerating ? "Generating..." : "Generate DecisionPlan"}
            </button>
          </div>

          {success && <p className="successText">{success}</p>}
          {error && <p className="errorText">{error}</p>}
        </form>

        <div className="workspaceResults">
          {isGenerating ? (
            <div className="approvalDetails approvalDetailsEmpty">
              <p className="eyebrow">DecisionPlan</p>
              <h3>Generating DecisionPlan...</h3>
            </div>
          ) : !decisionPlan ? (
            <div className="approvalDetails approvalDetailsEmpty">
              <p className="eyebrow">DecisionPlan</p>
              <h3>No DecisionPlan generated</h3>
            </div>
          ) : (
            <DecisionPlanResult decisionPlan={decisionPlan} />
          )}
        </div>
      </div>
    </section>
  );
}
