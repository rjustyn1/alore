import { useState, useEffect } from "react";

const SECTORS = {
  food:      { color: "#E85550", label: "Food Security" },
  energy:    { color: "#F0A020", label: "Energy" },
  water:     { color: "#3090E8", label: "Water Supply" },
  trade:     { color: "#18A87A", label: "Trade" },
  diplomacy: { color: "#9B59D0", label: "Diplomacy" },
  singapore: { color: "#2D3A52", label: "Singapore" },
};

const FLAGS = {
  MY: "🇲🇾", ID: "🇮🇩", TH: "🇹🇭", CN: "🇨🇳", AU: "🇦🇺",
  US: "🇺🇸", JP: "🇯🇵", SA: "🇸🇦", QA: "🇶🇦", IN: "🇮🇳",
  BR: "🇧🇷", DE: "🇩🇪",
};

const POSITION_META = {
  proceed:     { label: "Proceed",     color: "#18A87A", bg: "rgba(24,168,122,0.1)",  icon: "✓" },
  conditional: { label: "Conditional", color: "#F0A020", bg: "rgba(240,160,32,0.1)",  icon: "⚡" },
  monitor:     { label: "Monitor",     color: "#3090E8", bg: "rgba(48,144,232,0.1)",  icon: "◉" },
  hold:        { label: "Hold",        color: "#E85550", bg: "rgba(232,85,80,0.08)",  icon: "⏸" },
  abort:       { label: "Abort",       color: "#E85550", bg: "rgba(232,85,80,0.12)",  icon: "✕" },
};

const GOAL_META = {
  cost:        { label: "Minimise Cost",       icon: "💰" },
  risk:        { label: "Minimise Risk",        icon: "🛡" },
  resilience:  { label: "Maximise Resilience",  icon: "🔄" },
};

const URGENCY_COLOR = { low: "#18A87A", medium: "#F0A020", high: "#E85550" };
const SCENARIO_SEVERITY = {
  stable: { color: "#18A87A", bg: "rgba(24,168,122,0.1)", label: "Low Impact" },
  mild: { color: "#F0A020", bg: "rgba(240,160,32,0.1)", label: "Moderate" },
  urgent: { color: "#E85550", bg: "rgba(232,85,80,0.1)", label: "High Impact" },
};

function relativeTime(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days === 1) return "yesterday";
  return `${days}d ago`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleString("en-SG", {
    day: "numeric", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function DebateCard({ entry, expanded, onToggle, onGoHome }) {
  const sc = SECTORS[entry.route.sector]?.color || "#2D3A52";
  const pos = POSITION_META[entry.synthesis?.final_position] || POSITION_META.conditional;
  const goal = GOAL_META[entry.goal] || { label: entry.goal, icon: "🎯" };
  const score = Math.max(0, Math.min(1, entry.synthesis?.viability_score || 0));
  const urgency = entry.synthesis?.urgency || "medium";
  const urgencyColor = URGENCY_COLOR[urgency] || sc;
  const isDisrupted = entry.route.status === "disrupted";
  const isMild = entry.route.status === "mild";
  const statusColor = isDisrupted ? "#E85550" : isMild ? "#F0A020" : "#18A87A";

  return (
    <div
      style={{
        background: "#FDFCFA",
        border: `1px solid ${expanded ? sc + "44" : "rgba(45,58,82,0.09)"}`,
        borderLeft: `3px solid ${sc}`,
        borderRadius: "0 12px 12px 0",
        overflow: "hidden",
        transition: "border-color 0.2s, box-shadow 0.2s",
        boxShadow: expanded ? `0 4px 20px ${sc}14` : "none",
        animation: "panelIn 0.3s ease both",
      }}
    >
      <button
        onClick={onToggle}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: 0,
          padding: "14px 16px", background: "transparent", border: "none",
          cursor: "pointer", fontFamily: "'Inter',sans-serif", textAlign: "left",
        }}
      >
        <span style={{ fontSize: 24, lineHeight: 1, marginRight: 12, flexShrink: 0 }}>
          {FLAGS[entry.route.code] || "🌐"}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 4 }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: "#2D3A52" }}>{entry.route.country}</span>
            <span style={{ fontSize: 9, fontWeight: 700, color: sc, background: sc + "18", borderRadius: 5, padding: "1px 6px" }}>
              {SECTORS[entry.route.sector]?.label}
            </span>
            <span style={{ fontSize: 9, fontWeight: 700, color: statusColor, background: statusColor + "15", borderRadius: 5, padding: "1px 6px" }}>
              {entry.route.status}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 11, color: "rgba(45,58,82,0.45)" }}>{goal.icon} {goal.label}</span>
            <span style={{ fontSize: 10, color: "rgba(45,58,82,0.25)" }}>·</span>
            <span style={{ fontSize: 10, color: "rgba(45,58,82,0.38)" }}>{relativeTime(entry.timestamp)}</span>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5, flexShrink: 0, marginLeft: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "3px 9px", borderRadius: 20, background: pos.bg, border: `1px solid ${pos.color}44` }}>
            <span style={{ fontSize: 10, color: pos.color, fontWeight: 800 }}>{pos.icon}</span>
            <span style={{ fontSize: 10, fontWeight: 800, color: pos.color, textTransform: "uppercase", letterSpacing: "0.06em" }}>{pos.label}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 54, height: 3, background: "rgba(45,58,82,0.1)", borderRadius: 2, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${score * 100}%`, background: pos.color, borderRadius: 2 }} />
            </div>
            <span style={{ fontSize: 10, fontWeight: 700, color: pos.color }}>{Math.round(score * 100)}%</span>
          </div>
        </div>
        <span style={{ fontSize: 11, color: "rgba(45,58,82,0.3)", marginLeft: 10, transition: "transform 0.2s", transform: expanded ? "rotate(180deg)" : "rotate(0deg)", flexShrink: 0 }}>▼</span>
      </button>

      {!expanded && entry.synthesis?.recommended_action && (
        <div style={{ padding: "0 16px 12px", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 11, color: pos.color, fontWeight: 600 }}>→</span>
          <span style={{ fontSize: 11, color: "rgba(45,58,82,0.52)", lineHeight: 1.4 }}>{entry.synthesis.recommended_action}</span>
        </div>
      )}

      {expanded && entry.synthesis && (
        <div style={{ borderTop: "1px solid rgba(45,58,82,0.07)", padding: "16px 16px 18px", animation: "panelIn 0.22s ease both" }}>
          <div style={{ display: "flex", gap: 7, marginBottom: 14 }}>
            <span style={{ fontSize: 9.5, fontWeight: 700, color: urgencyColor, background: urgencyColor + "15", border: `1px solid ${urgencyColor}33`, borderRadius: 20, padding: "2px 9px", textTransform: "uppercase", letterSpacing: "0.08em" }}>{urgency} urgency</span>
            <span style={{ fontSize: 9.5, color: "rgba(45,58,82,0.38)", background: "rgba(45,58,82,0.06)", borderRadius: 20, padding: "2px 9px" }}>{entry.selectedNewsCount} signal{entry.selectedNewsCount !== 1 ? "s" : ""} analysed</span>
            <span style={{ fontSize: 9.5, color: "rgba(45,58,82,0.32)", marginLeft: "auto" }}>{formatDate(entry.timestamp)}</span>
          </div>

          <div style={{ marginBottom: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
              <span style={{ fontSize: 9, fontWeight: 800, color: "rgba(45,58,82,0.3)", textTransform: "uppercase", letterSpacing: "0.1em" }}>Viability Score</span>
              <span style={{ fontSize: 13, fontWeight: 800, color: pos.color }}>{Math.round(score * 100)}%</span>
            </div>
            <div style={{ height: 6, background: "rgba(45,58,82,0.08)", borderRadius: 3, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${score * 100}%`, background: `linear-gradient(to right, ${pos.color}99, ${pos.color})`, borderRadius: 3 }} />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 9, marginBottom: 12 }}>
            <div style={{ padding: "10px 12px", background: "rgba(24,168,122,0.06)", border: "1px solid rgba(24,168,122,0.15)", borderRadius: 9 }}>
              <div style={{ fontSize: 8.5, fontWeight: 800, color: "#18A87A", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 7 }}>Pros</div>
              {entry.synthesis.pros?.map((p, i) => (
                <div key={i} style={{ display: "flex", gap: 6, marginBottom: 5 }}>
                  <span style={{ fontSize: 9.5, color: "#18A87A", fontWeight: 700, flexShrink: 0 }}>✓</span>
                  <span style={{ fontSize: 10.5, color: "rgba(45,58,82,0.72)", lineHeight: 1.45 }}>{p}</span>
                </div>
              ))}
            </div>
            <div style={{ padding: "10px 12px", background: "rgba(232,85,80,0.05)", border: "1px solid rgba(232,85,80,0.14)", borderRadius: 9 }}>
              <div style={{ fontSize: 8.5, fontWeight: 800, color: "#E85550", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 7 }}>Cons</div>
              {entry.synthesis.cons?.map((c, i) => (
                <div key={i} style={{ display: "flex", gap: 6, marginBottom: 5 }}>
                  <span style={{ fontSize: 9.5, color: "#E85550", fontWeight: 700, flexShrink: 0 }}>✕</span>
                  <span style={{ fontSize: 10.5, color: "rgba(45,58,82,0.72)", lineHeight: 1.45 }}>{c}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ padding: "11px 13px", background: "rgba(45,58,82,0.04)", border: "1px solid rgba(45,58,82,0.08)", borderRadius: 9, marginBottom: 10 }}>
            <div style={{ fontSize: 8.5, fontWeight: 800, color: "rgba(45,58,82,0.28)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 5 }}>Consensus Rationale</div>
            <div style={{ fontSize: 12, color: "rgba(45,58,82,0.7)", lineHeight: 1.6, fontStyle: "italic" }}>"{entry.synthesis.rationale}"</div>
          </div>

          {entry.synthesis.recommended_action && (
            <div style={{ padding: "11px 13px", marginBottom: 12, background: pos.color + "0e", border: `1.5px solid ${pos.color}33`, borderRadius: 9, display: "flex", alignItems: "center", gap: 9 }}>
              <span style={{ fontSize: 16, color: pos.color, flexShrink: 0 }}>→</span>
              <div>
                <div style={{ fontSize: 8.5, fontWeight: 800, color: pos.color, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 3 }}>Recommended Action</div>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: "rgba(45,58,82,0.82)" }}>{entry.synthesis.recommended_action}</div>
              </div>
            </div>
          )}

          <button
            onClick={() => onGoHome()}
            style={{ fontSize: 11, fontWeight: 600, color: sc, background: sc + "10", border: `1px solid ${sc}33`, borderRadius: 7, padding: "6px 13px", cursor: "pointer", fontFamily: "'Inter',sans-serif" }}
          >
            ↩ Re-run on Home →
          </button>
        </div>
      )}
    </div>
  );
}

function ScenarioCard({ entry, expanded, onToggle }) {
  const sev = SCENARIO_SEVERITY[entry.severity] || SCENARIO_SEVERITY.mild;
  const sectors = [...new Set((entry.chain || []).map((step) => step.sector).filter(Boolean))].slice(0, 5);

  return (
    <div
      style={{
        background: "#FDFCFA",
        border: `1px solid ${expanded ? sev.color + "44" : "rgba(45,58,82,0.09)"}`,
        borderLeft: `3px solid ${sev.color}`,
        borderRadius: "0 12px 12px 0",
        overflow: "hidden",
        transition: "border-color 0.2s, box-shadow 0.2s",
        boxShadow: expanded ? `0 4px 20px ${sev.color}14` : "none",
        animation: "panelIn 0.3s ease both",
      }}
    >
      <button
        onClick={onToggle}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: 0,
          padding: "14px 16px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          fontFamily: "'Inter',sans-serif",
          textAlign: "left",
        }}
      >
        <span style={{ fontSize: 22, lineHeight: 1, marginRight: 12, flexShrink: 0 }}>🧪</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 4, flexWrap: "wrap" }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: "#2D3A52" }}>{entry.scenario || "Scenario Simulation"}</span>
            <span style={{ fontSize: 9, fontWeight: 700, color: sev.color, background: sev.bg, borderRadius: 5, padding: "1px 6px", border: `1px solid ${sev.color}33` }}>
              {sev.label}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <span style={{ fontSize: 11, color: "rgba(45,58,82,0.45)" }}>{relativeTime(entry.timestamp)}</span>
            <span style={{ fontSize: 10, color: "rgba(45,58,82,0.25)" }}>·</span>
            <span style={{ fontSize: 11, color: "rgba(45,58,82,0.45)" }}>{(entry.chain || []).length} chain step{(entry.chain || []).length !== 1 ? "s" : ""}</span>
            <span style={{ fontSize: 10, color: "rgba(45,58,82,0.25)" }}>·</span>
            <span style={{ fontSize: 11, color: "rgba(45,58,82,0.45)" }}>{(entry.mitigations || []).length} mitigation{(entry.mitigations || []).length !== 1 ? "s" : ""}</span>
          </div>
        </div>
        <span style={{ fontSize: 11, color: "rgba(45,58,82,0.3)", marginLeft: 10, transition: "transform 0.2s", transform: expanded ? "rotate(180deg)" : "rotate(0deg)", flexShrink: 0 }}>▼</span>
      </button>

      {!expanded && entry.summary && (
        <div style={{ padding: "0 16px 12px", fontSize: 11, color: "rgba(45,58,82,0.52)", lineHeight: 1.45 }}>
          {entry.summary}
        </div>
      )}

      {expanded && (
        <div style={{ borderTop: "1px solid rgba(45,58,82,0.07)", padding: "16px 16px 18px", animation: "panelIn 0.22s ease both" }}>
          <div style={{ fontSize: 9.5, color: "rgba(45,58,82,0.32)", marginBottom: 10 }}>{formatDate(entry.timestamp)}</div>

          {entry.prompt && (
            <div style={{ padding: "10px 12px", background: "rgba(45,58,82,0.04)", border: "1px solid rgba(45,58,82,0.08)", borderRadius: 9, marginBottom: 10 }}>
              <div style={{ fontSize: 8.5, fontWeight: 800, color: "rgba(45,58,82,0.28)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 5 }}>Prompt</div>
              <div style={{ fontSize: 12, color: "rgba(45,58,82,0.72)", lineHeight: 1.5 }}>{entry.prompt}</div>
            </div>
          )}

          {entry.summary && (
            <div style={{ padding: "10px 12px", background: "rgba(45,58,82,0.04)", border: "1px solid rgba(45,58,82,0.08)", borderRadius: 9, marginBottom: 10 }}>
              <div style={{ fontSize: 8.5, fontWeight: 800, color: "rgba(45,58,82,0.28)", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 5 }}>Summary</div>
              <div style={{ fontSize: 12, color: "rgba(45,58,82,0.72)", lineHeight: 1.5 }}>{entry.summary}</div>
            </div>
          )}

          {sectors.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {sectors.map((sector) => {
                const meta = SECTORS[sector] || { color: "#2D3A52", label: sector };
                return (
                  <span key={`${entry.id}-${sector}`} style={{ fontSize: 9, fontWeight: 700, color: meta.color, background: meta.color + "18", borderRadius: 5, padding: "2px 7px", border: `1px solid ${meta.color}33` }}>
                    {meta.label}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function DebateHistoryPage({ onNavigate = () => {} }) {
  const [debateHistory, setDebateHistory] = useState([]);
  const [scenarioHistory, setScenarioHistory] = useState([]);
  const [expandedDebateId, setExpandedDebateId] = useState(null);
  const [expandedScenarioId, setExpandedScenarioId] = useState(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    try {
      const storedDebates = JSON.parse(localStorage.getItem("alore_debates") || "[]");
      const storedScenarios = JSON.parse(localStorage.getItem("alore_scenarios") || "[]");
      setDebateHistory(storedDebates);
      setScenarioHistory(storedScenarios);
    } catch {
      setDebateHistory([]);
      setScenarioHistory([]);
    }
  }, []);

  const FILTERS = [
    { id: "all",         label: "All" },
    { id: "proceed",     label: "Proceed" },
    { id: "conditional", label: "Conditional" },
    { id: "monitor",     label: "Monitor" },
    { id: "hold",        label: "Hold" },
    { id: "abort",       label: "Abort" },
  ];

  const totalItems = debateHistory.length + scenarioHistory.length;
  const filtered = filter === "all"
    ? debateHistory
    : debateHistory.filter((e) => e.synthesis?.final_position === filter);

  const clearHistory = () => {
    localStorage.removeItem("alore_debates");
    localStorage.removeItem("alore_scenarios");
    setDebateHistory([]);
    setScenarioHistory([]);
  };

  return (
    <div style={{ minHeight: "100%", background: "#F5F2EE", fontFamily: "'Inter',sans-serif", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "22px 20px 0", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 18 }}>
          <div>
            <div style={{ fontSize: 9, fontWeight: 800, color: "rgba(45,58,82,0.35)", textTransform: "uppercase", letterSpacing: "0.14em", marginBottom: 5 }}>Alore · Archive</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: "#2D3A52", letterSpacing: "-0.025em", lineHeight: 1.1, marginBottom: 5 }}>History</div>
            <div style={{ fontSize: 12.5, color: "rgba(45,58,82,0.45)", lineHeight: 1.5 }}>Debate outcomes and scenario simulation records in one place</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: "#2D3A52", letterSpacing: "-0.02em", background: "#FDFCFA", border: "1px solid rgba(45,58,82,0.1)", borderRadius: 10, padding: "6px 14px", lineHeight: 1 }}>
              {totalItems}
              <span style={{ fontSize: 11, fontWeight: 600, color: "rgba(45,58,82,0.35)", marginLeft: 6 }}>record{totalItems !== 1 ? "s" : ""}</span>
            </div>
            <div style={{ fontSize: 11, color: "rgba(45,58,82,0.4)" }}>
              {debateHistory.length} debate{debateHistory.length !== 1 ? "s" : ""} · {scenarioHistory.length} simulation{scenarioHistory.length !== 1 ? "s" : ""}
            </div>
            {totalItems > 0 && (
              <button onClick={clearHistory} style={{ fontSize: 10, fontWeight: 600, color: "rgba(45,58,82,0.38)", background: "transparent", border: "1px solid rgba(45,58,82,0.12)", borderRadius: 6, padding: "4px 10px", cursor: "pointer", fontFamily: "'Inter',sans-serif" }}>
                Clear all
              </button>
            )}
          </div>
        </div>

        {debateHistory.length > 0 && (
          <div style={{ display: "flex", gap: 5, overflowX: "auto", paddingBottom: 2 }}>
            {FILTERS.map((f) => {
              const pos = POSITION_META[f.id];
              const isActive = filter === f.id;
              const count = f.id === "all" ? debateHistory.length : debateHistory.filter((e) => e.synthesis?.final_position === f.id).length;
              if (f.id !== "all" && count === 0) return null;
              return (
                <button
                  key={f.id}
                  onClick={() => setFilter(f.id)}
                  style={{
                    flexShrink: 0, display: "flex", alignItems: "center", gap: 5,
                    padding: "5px 12px",
                    background: isActive ? (pos?.color ? pos.color + "18" : "rgba(45,58,82,0.08)") : "rgba(45,58,82,0.05)",
                    border: `1px solid ${isActive ? (pos?.color ? pos.color + "44" : "rgba(45,58,82,0.25)") : "rgba(45,58,82,0.1)"}`,
                    borderRadius: 20, fontSize: 11, fontWeight: isActive ? 700 : 500,
                    color: isActive ? (pos?.color || "#2D3A52") : "rgba(45,58,82,0.5)",
                    cursor: "pointer", fontFamily: "'Inter',sans-serif", transition: "all 0.14s",
                  }}
                >
                  {pos && <span style={{ fontSize: 10 }}>{pos.icon}</span>}
                  {f.label}
                  <span style={{ fontSize: 9.5, fontWeight: 700, color: isActive ? (pos?.color || "#2D3A52") : "rgba(45,58,82,0.32)", background: isActive ? (pos?.color ? pos.color + "18" : "rgba(45,58,82,0.08)") : "rgba(45,58,82,0.07)", borderRadius: 10, padding: "0px 5px" }}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div style={{ flex: 1, padding: "14px 20px 24px", overflowY: "auto" }}>
        {totalItems === 0 && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "64px 24px", textAlign: "center" }}>
            <div style={{ width: 64, height: 64, borderRadius: 18, background: "rgba(45,58,82,0.06)", border: "1px solid rgba(45,58,82,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, marginBottom: 18 }}>🗂️</div>
            <div style={{ fontSize: 17, fontWeight: 700, color: "#2D3A52", marginBottom: 8, letterSpacing: "-0.01em" }}>No history yet</div>
            <div style={{ fontSize: 12.5, color: "rgba(45,58,82,0.45)", lineHeight: 1.6, maxWidth: 280, marginBottom: 22 }}>
              Run a debate or scenario simulation first, then results will appear here.
            </div>
            <button onClick={() => onNavigate("dashboard")} style={{ padding: "10px 22px", background: "#2D3A52", border: "none", borderRadius: 10, fontSize: 12, fontWeight: 700, color: "#F5F2EE", cursor: "pointer", fontFamily: "'Inter',sans-serif", letterSpacing: "0.01em" }}>
              Go to Home →
            </button>
          </div>
        )}

        {debateHistory.length > 0 && (
          <div style={{ marginBottom: 18 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <div style={{ fontSize: 11, fontWeight: 800, color: "rgba(45,58,82,0.35)", textTransform: "uppercase", letterSpacing: "0.12em" }}>Debate Generator</div>
              <div style={{ fontSize: 10.5, color: "rgba(45,58,82,0.35)" }}>{filtered.length} shown</div>
            </div>
            {filtered.length === 0 && (
              <div style={{ padding: "14px 0", textAlign: "center", color: "rgba(45,58,82,0.38)", fontSize: 13 }}>No debates match this filter.</div>
            )}
            {filtered.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {filtered.map((entry) => (
                  <DebateCard
                    key={entry.id}
                    entry={entry}
                    expanded={expandedDebateId === entry.id}
                    onToggle={() => setExpandedDebateId(expandedDebateId === entry.id ? null : entry.id)}
                    onGoHome={() => onNavigate("dashboard")}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {scenarioHistory.length > 0 && (
          <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
              <div style={{ fontSize: 11, fontWeight: 800, color: "rgba(45,58,82,0.35)", textTransform: "uppercase", letterSpacing: "0.12em" }}>Scenario Generator</div>
              <div style={{ fontSize: 10.5, color: "rgba(45,58,82,0.35)" }}>{scenarioHistory.length} simulation{scenarioHistory.length !== 1 ? "s" : ""}</div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {scenarioHistory.map((entry) => (
                <ScenarioCard
                  key={entry.id}
                  entry={entry}
                  expanded={expandedScenarioId === entry.id}
                  onToggle={() => setExpandedScenarioId(expandedScenarioId === entry.id ? null : entry.id)}
                />
              ))}
            </div>
          </div>
        )}

        {debateHistory.length === 0 && scenarioHistory.length > 0 && (
          <div style={{ padding: "4px 0 22px", color: "rgba(45,58,82,0.4)", fontSize: 12 }}>No debate records yet. Scenario simulations are available below.</div>
        )}
      </div>
    </div>
  );
}
