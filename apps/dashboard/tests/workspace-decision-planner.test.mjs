import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const workspaceSource = readFileSync(new URL("../components/AIWorkspace.tsx", import.meta.url), "utf8");
const apiSource = readFileSync(new URL("../lib/api.ts", import.meta.url), "utf8");

test("Workspace generates DecisionPlans through the REST API", () => {
  assert.match(apiSource, /export function createDecisionPlan/);
  assert.match(apiSource, /"\/api\/v1\/decision-plans"/);
  assert.match(workspaceSource, /createDecisionPlan\(/);
  assert.match(workspaceSource, /Generate DecisionPlan/);
});

test("Workspace renders successful DecisionPlan fields", () => {
  for (const label of [
    "Primary Path",
    "Alternatives",
    "Rationale",
    "Evidence",
    "Assumptions",
    "Risks",
    "Constraints",
    "Success Definition",
  ]) {
    assert.match(workspaceSource, new RegExp(label));
  }
});

test("Workspace includes loading and empty states", () => {
  assert.match(workspaceSource, /Generating DecisionPlan\.\.\./);
  assert.match(workspaceSource, /No DecisionPlan generated/);
});

test("Workspace exposes API error state for planner and validation failures", () => {
  assert.match(workspaceSource, /DecisionPlan generation failed:/);
  assert.match(workspaceSource, /setError/);
});

test("Workspace remains read-only in Phase 5A", () => {
  assert.doesNotMatch(workspaceSource, /Create approval requests/);
  assert.doesNotMatch(workspaceSource, /triggerN8nApproval/);
  assert.doesNotMatch(workspaceSource, /approveApproval/);
  assert.doesNotMatch(workspaceSource, /rejectApproval/);
  assert.doesNotMatch(workspaceSource, /create_approval_requests:\s*true/);
  assert.match(workspaceSource, /read-only/);
  assert.match(workspaceSource, /no execution/);
});
