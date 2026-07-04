"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getProjects, getTasks, type Project, type Task } from "../lib/api";

export function ContinueHero() {
  const [mission, setMission] = useState<Project | null>(null);
  const [decision, setDecision] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function loadData() {
      try {
        const [projRes, taskRes] = await Promise.all([getProjects(), getTasks()]);
        
        if (!mounted) return;

        let activeMission = null;
        let activeDecision = null;

        if (projRes.ok && projRes.data.length > 0) {
          activeMission = projRes.data.filter(p => p.status !== "done")[0] || projRes.data[0];
        }

        if (taskRes.ok && taskRes.data.length > 0) {
          const pending = taskRes.data.filter(t => t.status === "pending" || t.status === "open");
          if (activeMission) {
             activeDecision = pending.find(t => t.project_id === activeMission?.id) || pending[0];
          } else {
             activeDecision = pending[0];
          }
        }

        setMission(activeMission);
        setDecision(activeDecision);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadData();
    return () => { mounted = false; };
  }, []);

  if (loading) {
    return (
      <section className="card" style={{ background: "var(--accent)", color: "white" }}>
        <p>Loading your workspace...</p>
      </section>
    );
  }

  const title = mission ? mission.name : "System Initialization";
  const decisionText = decision ? decision.title : "No active decision";
  const status = mission ? (mission.status === "running" ? "In Progress" : "Standing By") : "Online";
  const estimatedStep = decision ? "Awaiting human authorization" : "Select a mission to begin";
  
  const targetUrl = decision 
    ? `/workspace?goal=${encodeURIComponent(decision.title)}&mission_id=${encodeURIComponent(mission?.id || '')}`
    : mission 
      ? `/workspace?project_id=${encodeURIComponent(mission.id)}`
      : `/workspace`;

  return (
    <section className="card" style={{ 
      background: "linear-gradient(135deg, var(--accent) 0%, #1e3a5f 100%)", 
      color: "white",
      padding: "32px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      border: "none",
      boxShadow: "0 8px 24px rgba(0,0,0,0.12)"
    }}>
      <div>
        <p className="eyebrow" style={{ color: "rgba(255,255,255,0.7)" }}>Current Focus</p>
        <h2 style={{ fontSize: "2rem", marginBottom: "8px", color: "white" }}>{title}</h2>
        
        <div style={{ display: "flex", gap: "24px", marginTop: "16px", fontSize: "0.95rem" }}>
          <div>
            <span style={{ color: "rgba(255,255,255,0.7)", display: "block", fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "4px" }}>Current Decision</span>
            <strong>{decisionText}</strong>
          </div>
          <div>
            <span style={{ color: "rgba(255,255,255,0.7)", display: "block", fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "4px" }}>Status</span>
            <span className="pill" style={{ background: "rgba(255,255,255,0.2)", color: "white", borderColor: "transparent" }}>{status}</span>
          </div>
          <div>
            <span style={{ color: "rgba(255,255,255,0.7)", display: "block", fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "4px" }}>Next Step</span>
            <span>{estimatedStep}</span>
          </div>
        </div>
      </div>
      
      <div>
        <Link 
          href={targetUrl} 
          className="btnSave"
          style={{ 
            background: "white", 
            color: "var(--accent)", 
            padding: "16px 32px", 
            fontSize: "1.1rem",
            textDecoration: "none",
            borderRadius: "8px",
            fontWeight: 600,
            display: "inline-block",
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
          }}
        >
          Continue
        </Link>
      </div>
    </section>
  );
}
