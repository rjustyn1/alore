import { useState, useEffect, useRef } from "react";

const SECTOR_COLORS = {
  food: "#E85550",
  energy: "#F0A020",
  water: "#3090E8",
  trade: "#18A87A",
  diplomacy: "#9B59D0",
};

const SIGNALS = [
  { id: 1, name: "Brent Crude Price", sector: "energy", value: "$87.40/bbl", threshold: "Alert > $95", change: "+2.3%", dir: "up", status: "watching", checked: "2m ago", sourcesN: 3 },
  { id: 2, name: "Malaysia Water Agreement", sector: "water", value: "Active", threshold: "Policy change monitor", change: "No change", dir: "stable", status: "watching", checked: "8m ago", sourcesN: 2 },
  { id: 3, name: "China Export Controls", sector: "food", value: "34% tariff", threshold: "New restrictions", change: "ESCALATED", dir: "up", status: "triggered", checked: "12m ago", sourcesN: 4 },
  { id: 4, name: "Palm Oil Futures", sector: "food", value: "MYR 3,840/t", threshold: "Alert > MYR 4,200", change: "+1.8%", dir: "up", status: "watching", checked: "5m ago", sourcesN: 2 },
  { id: 5, name: "Red Sea Shipping", sector: "trade", value: "23 vessels", threshold: "Rerouting events", change: "3 rerouted", dir: "mild", status: "mild", checked: "18m ago", sourcesN: 3 },
  { id: 6, name: "Qatar LNG Supply", sector: "energy", value: "22% of imports", threshold: "Alert if < 15%", change: "Stable", dir: "stable", status: "watching", checked: "31m ago", sourcesN: 2 },
  { id: 7, name: "Indonesia Diplomatic", sector: "diplomacy", value: "Stable", threshold: "Trade disputes", change: "Stable", dir: "stable", status: "watching", checked: "45m ago", sourcesN: 2 },
  { id: 8, name: "Global Food Price Index", sector: "food", value: "127.4", threshold: "Alert > 135", change: "+0.6%", dir: "up", status: "watching", checked: "1h ago", sourcesN: 3 },
];

const DETECTIONS = [
  { time: "14 min ago", signal: "China Export Controls", sector: "food", severity: "urgent", msg: "New 34% tariff on processed food exports confirmed. 4 corroborating sources across Reuters, SCMP, Bloomberg, MTI." },
  { time: "1h 22m ago", signal: "Red Sea Shipping", sector: "trade", severity: "mild", msg: "Maersk rerouting 3 SG-bound vessels via Cape of Good Hope. ETA impact +12 days detected via MarineTraffic." },
  { time: "3h 45m ago", signal: "Brent Crude Price", sector: "energy", severity: "mild", msg: "Price crossed $85/bbl monitoring threshold. Watching for continued escalation toward $95 alert level." },
  { time: "Yesterday", signal: "Palm Oil Futures", sector: "food", severity: "stable", msg: "Weekly settlement within normal range. No threshold breach. Next check scheduled." },
];

const SOURCE_POOL = [
  { name: "Reuters", color: "#E85550" },
  { name: "Bloomberg", color: "#F0A020" },
  { name: "Straits Times", color: "#2D3A52" },
  { name: "SCMP", color: "#E85550" },
  { name: "MarineTraffic", color: "#3090E8" },
  { name: "MFA.gov.sg", color: "#2D3A52" },
  { name: "FAO", color: "#18A87A" },
  { name: "MTI", color: "#2D3A52" },
  { name: "Freightos", color: "#18A87A" },
  { name: "MPOB", color: "#F0A020" },
  { name: "IEA", color: "#F0A020" },
  { name: "Bernama", color: "#9B59D0" },
];

const SWEEP_SEQUENCE = [
  "Querying Reuters...",
  "Reading Bloomberg...",
  "Scanning Straits Times...",
  "Fetching SCMP...",
  "Checking MarineTraffic...",
  "Querying MFA.gov.sg...",
  "Fetching FAO data...",
  "Reading MTI releases...",
  "Querying Freightos...",
  "Reading MPOB index...",
  "Checking IEA reports...",
  "Scanning Bernama...",
];

const STATUS_CONFIG = {
  triggered: { bg: "#E85550", color: "#fff", label: "TRIGGERED" },
  mild:      { bg: "#F0A020", color: "#fff", label: "MILD" },
  watching:  { bg: "rgba(45,58,82,0.08)", color: "rgba(45,58,82,0.55)", label: "WATCHING" },
};

const SEVERITY_CONFIG = {
  urgent: { color: "#E85550", bg: "rgba(232,85,80,0.1)", label: "Urgent" },
  mild:   { color: "#F0A020", bg: "rgba(240,160,32,0.1)", label: "Mild" },
  stable: { color: "#18A87A", bg: "rgba(24,168,122,0.1)", label: "Stable" },
};

const SEVERITY_TO_STATUS = {
  CRITICAL: "triggered",
  DISRUPTED: "triggered",
  CONSTRAINED: "mild",
  WARNING: "mild",
};

const SEVERITY_TO_DETECTION = {
  CRITICAL: "urgent",
  DISRUPTED: "urgent",
  CONSTRAINED: "mild",
  WARNING: "stable",
};

function resourceTag(resource_types) {
  const keys = Object.keys(resource_types);
  if (keys.includes("energy")) return "energy";
  if (keys.includes("food")) return "food";
  return "trade";
}

export default function SentryPage({ onNavigate: _onNavigate = () => {} }) {
  const [sweeping, setSweeping] = useState(false);
  const [sweepStep, setSweepStep] = useState(-1);
  const [sweepDone, setSweepDone] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const intervalRef = useRef(null);
  const [detections, setDetections] = useState(DETECTIONS);

  useEffect(() => {
    fetch("/api/v1/disruptions/events")
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then(({ data }) => {
        if (!data.events.length) return;
        const mapped = data.events.map((e) => ({
          time: e.updated_at ? new Date(e.updated_at).toLocaleString() : "recently",
          signal: e.from_country,
          sector: resourceTag(e.resource_types),
          severity: SEVERITY_TO_DETECTION[e.severity] ?? "mild",
          msg: e.headline,
        }));
        setDetections(mapped);
      })
      .catch(() => {/* keep fallback */});
  }, []);

  const runSweep = () => {
    if (sweeping) return;
    setSweeping(true);
    setSweepDone(false);
    setSweepStep(-1);
    setModalOpen(true);
    let step = 0;
    // Small delay before first step so modal appears first
    setTimeout(() => {
      setSweepStep(0);
      intervalRef.current = setInterval(() => {
        step++;
        setSweepStep(step);
        if (step >= SOURCE_POOL.length) {
          clearInterval(intervalRef.current);
          setSweepDone(true);
          setSweeping(false);
        }
      }, 420);
    }, 300);
  };

  useEffect(() => () => clearInterval(intervalRef.current), []);

  const triggeredCount = SIGNALS.filter((s) => s.status === "triggered").length;
  const mildCount = SIGNALS.filter((s) => s.status === "mild").length;

  return (
    <div style={{ minHeight: "100%", background: "#F5F2EE", fontFamily: "'Inter',sans-serif", padding: "20px 20px 32px" }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 9, fontWeight: 800, color: "rgba(45,58,82,0.35)", textTransform: "uppercase", letterSpacing: "0.14em", marginBottom: 5 }}>
          Alore · Signal Intelligence
        </div>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 26, fontWeight: 800, color: "#2D3A52", letterSpacing: "-0.025em", lineHeight: 1.1, marginBottom: 5 }}>Sentry</div>
            <div style={{ fontSize: 12.5, color: "rgba(45,58,82,0.45)" }}>Live signal monitoring across Singapore's supply network</div>
          </div>
          <button
            onClick={sweeping ? () => setModalOpen(true) : runSweep}
            style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "9px 18px",
              background: sweeping ? "rgba(45,58,82,0.08)" : "#2D3A52",
              border: sweeping ? "1px solid rgba(45,58,82,0.15)" : "none",
              borderRadius: 10, fontSize: 12, fontWeight: 700,
              color: sweeping ? "#2D3A52" : "#F5F2EE",
              cursor: "pointer",
              fontFamily: "'Inter',sans-serif", transition: "all 0.2s",
            }}
          >
            {sweeping ? (
              <>
                <div style={{ width: 12, height: 12, border: "2px solid rgba(45,58,82,0.1)", borderTopColor: "#2D3A52", borderRadius: "50%", animation: "spin 0.7s linear infinite" }} />
                Sweeping…
              </>
            ) : (
              <>
                <svg width="13" height="13" viewBox="0 0 20 20" fill="none">
                  <circle cx="10" cy="10" r="2.5" fill="currentColor" opacity="0.8"/>
                  <circle cx="10" cy="10" r="5.5" stroke="currentColor" strokeWidth="1.4" opacity="0.5" fill="none"/>
                  <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="1.2" opacity="0.25" fill="none"/>
                </svg>
                Run Sweep
              </>
            )}
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div style={{ display: "flex", gap: 8, marginBottom: 18, flexWrap: "wrap" }}>
        {[
          { label: "Signals Watching", value: SIGNALS.length, color: "#2D3A52" },
          { label: "Triggered / Mild", value: `${triggeredCount} / ${mildCount}`, color: triggeredCount > 0 ? "#E85550" : "#F0A020" },
          { label: "Sources Monitored", value: SOURCE_POOL.length, color: "#18A87A" },
        ].map((s) => (
          <div key={s.label} style={{ flex: "1 1 120px", background: "#FDFCFA", border: "1px solid rgba(45,58,82,0.09)", borderRadius: 10, padding: "10px 14px" }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: s.color, letterSpacing: "-0.02em", lineHeight: 1 }}>{s.value}</div>
            <div style={{ fontSize: 10, color: "rgba(45,58,82,0.42)", marginTop: 3, fontWeight: 500 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Signal cards */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 9, fontWeight: 800, color: "rgba(45,58,82,0.32)", textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 10 }}>Monitored Signals</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 8 }}>
          {SIGNALS.map((sig) => {
            const sc = SECTOR_COLORS[sig.sector];
            const st = STATUS_CONFIG[sig.status];
            return (
              <div key={sig.id} style={{ background: "#FDFCFA", border: `1px solid ${sig.status === "triggered" ? "rgba(232,85,80,0.25)" : "rgba(45,58,82,0.09)"}`, borderLeft: `3px solid ${sc}`, borderRadius: "0 10px 10px 0", padding: "12px 14px", transition: "box-shadow 0.15s" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 8 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#2D3A52", lineHeight: 1.3, marginBottom: 2 }}>{sig.name}</div>
                    <div style={{ fontSize: 9.5, color: sc, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em" }}>{sig.sector}</div>
                  </div>
                  <div style={{ padding: "3px 8px", background: st.bg, borderRadius: 20, fontSize: 8.5, fontWeight: 800, color: st.color, textTransform: "uppercase", letterSpacing: "0.07em", flexShrink: 0 }}>
                    {st.label}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 6 }}>
                  <span style={{ fontSize: 15, fontWeight: 800, color: "#2D3A52", letterSpacing: "-0.01em" }}>{sig.value}</span>
                  <span style={{ fontSize: 10.5, fontWeight: 600, color: sig.dir === "up" ? "#E85550" : sig.dir === "mild" ? "#F0A020" : "#18A87A" }}>{sig.change}</span>
                </div>
                <div style={{ fontSize: 10, color: "rgba(45,58,82,0.38)", marginBottom: 4 }}>Threshold: {sig.threshold}</div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 9.5, color: "rgba(45,58,82,0.3)" }}>Checked {sig.checked}</span>
                  <span style={{ fontSize: 9.5, color: "rgba(45,58,82,0.3)" }}>{sig.sourcesN} sources</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Detections */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 9, fontWeight: 800, color: "rgba(45,58,82,0.32)", textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 10 }}>Recent Detections</div>
        <div style={{ background: "#FDFCFA", border: "1px solid rgba(45,58,82,0.09)", borderRadius: 12, overflow: "hidden" }}>
          {detections.map((d, i) => {
            const sc = SECTOR_COLORS[d.sector];
            const sv = SEVERITY_CONFIG[d.severity];
            return (
              <div key={i} style={{ display: "flex", gap: 12, padding: "13px 16px", borderBottom: i < detections.length - 1 ? "1px solid rgba(45,58,82,0.07)" : "none", alignItems: "flex-start" }}>
                <div style={{ flexShrink: 0, marginTop: 2 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: sv.color, animation: d.severity === "urgent" ? "pulse 1.5s ease-in-out infinite" : "none" }} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 4 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: "#2D3A52" }}>{d.signal}</span>
                    <span style={{ fontSize: 9, fontWeight: 700, color: sc, background: sc + "18", borderRadius: 4, padding: "1px 6px" }}>{d.sector}</span>
                    <span style={{ fontSize: 9, fontWeight: 700, color: sv.color, background: sv.bg, borderRadius: 4, padding: "1px 6px" }}>{sv.label}</span>
                    <span style={{ fontSize: 9.5, color: "rgba(45,58,82,0.3)", marginLeft: "auto", flexShrink: 0 }}>{d.time}</span>
                  </div>
                  <div style={{ fontSize: 11.5, color: "rgba(45,58,82,0.6)", lineHeight: 1.55 }}>{d.msg}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Source Pool */}
      <div>
        <div style={{ fontSize: 9, fontWeight: 800, color: "rgba(45,58,82,0.32)", textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 10 }}>Source Pool</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {SOURCE_POOL.map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 11px", background: "#FDFCFA", border: "1px solid rgba(45,58,82,0.09)", borderRadius: 20, fontSize: 11, fontWeight: 600, color: "rgba(45,58,82,0.65)" }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: s.color, flexShrink: 0 }} />
              {s.name}
            </div>
          ))}
        </div>
      </div>

      {/* Sweep Modal */}
      {modalOpen && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(45,58,82,0.35)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
          <div style={{ background: "#FDFCFA", borderRadius: 16, width: "100%", maxWidth: 420, boxShadow: "0 20px 60px rgba(45,58,82,0.22)", animation: "panelIn 0.22s ease", overflow: "hidden" }}>
            {/* Modal header */}
            <div style={{ padding: "18px 20px 14px", borderBottom: "1px solid rgba(45,58,82,0.08)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ position: "relative", width: 28, height: 28, flexShrink: 0 }}>
                  <svg width="28" height="28" viewBox="0 0 20 20" fill="none" style={{ position: "absolute", inset: 0, animation: sweeping ? "spin 1.8s linear infinite" : "none", opacity: sweeping ? 1 : 0.4 }}>
                    <circle cx="10" cy="10" r="2.5" fill="#2D3A52" opacity="0.8"/>
                    <circle cx="10" cy="10" r="5.5" stroke="#2D3A52" strokeWidth="1.4" opacity="0.5" fill="none"/>
                    <circle cx="10" cy="10" r="9" stroke="#2D3A52" strokeWidth="1.2" opacity="0.25" fill="none"/>
                  </svg>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 800, color: "#2D3A52" }}>
                    {sweepDone ? "Sweep Complete" : "Running Sweep"}
                  </div>
                  <div style={{ fontSize: 10, color: "rgba(45,58,82,0.42)", marginTop: 1 }}>
                    {sweepDone ? `${SOURCE_POOL.length} sources checked` : SWEEP_SEQUENCE[Math.min(sweepStep, SWEEP_SEQUENCE.length - 1)] || "Initialising…"}
                  </div>
                </div>
                {sweepDone && (
                  <div style={{ fontSize: 9, fontWeight: 800, color: "#18A87A", background: "rgba(24,168,122,0.1)", padding: "3px 9px", borderRadius: 20, letterSpacing: "0.06em" }}>DONE</div>
                )}
              </div>
              {/* Progress bar */}
              <div style={{ marginTop: 12, height: 3, background: "rgba(45,58,82,0.08)", borderRadius: 2, overflow: "hidden" }}>
                <div style={{ height: "100%", background: sweepDone ? "#18A87A" : "#2D3A52", borderRadius: 2, width: `${Math.max(0, (sweepStep + 1) / SOURCE_POOL.length * 100)}%`, transition: "width 0.3s ease" }} />
              </div>
            </div>

            {/* Source list */}
            <div style={{ padding: "10px 0", maxHeight: 340, overflowY: "auto" }}>
              {SOURCE_POOL.map((s, i) => {
                const isDone = i < sweepStep || sweepDone;
                const isActive = !sweepDone && i === sweepStep;
                const isPending = !sweepDone && i > sweepStep;
                return (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 11, padding: "8px 20px", background: isActive ? "rgba(45,58,82,0.04)" : "transparent", transition: "background 0.2s" }}>
                    {/* Status indicator */}
                    <div style={{ width: 18, height: 18, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      {isDone ? (
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                          <circle cx="7" cy="7" r="6.5" fill="rgba(24,168,122,0.12)" stroke="#18A87A" strokeWidth="1.2"/>
                          <path d="M4.5 7l2 2 3-3" stroke="#18A87A" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      ) : isActive ? (
                        <div style={{ width: 14, height: 14, border: "2px solid rgba(45,58,82,0.1)", borderTopColor: "#2D3A52", borderRadius: "50%", animation: "spin 0.6s linear infinite" }} />
                      ) : (
                        <div style={{ width: 6, height: 6, borderRadius: "50%", background: "rgba(45,58,82,0.18)" }} />
                      )}
                    </div>
                    {/* Source dot */}
                    <div style={{ width: 7, height: 7, borderRadius: "50%", background: s.color, flexShrink: 0, opacity: isPending ? 0.3 : 1, transition: "opacity 0.2s" }} />
                    {/* Source name */}
                    <span style={{ fontSize: 12, fontWeight: isActive ? 700 : 500, color: isPending ? "rgba(45,58,82,0.3)" : isActive ? "#2D3A52" : "rgba(45,58,82,0.65)", transition: "all 0.2s", flex: 1 }}>
                      {SWEEP_SEQUENCE[i]?.replace(/\.\.\.$/, "") || s.name}
                    </span>
                    {isDone && (
                      <span style={{ fontSize: 9, color: "rgba(45,58,82,0.28)", fontWeight: 500 }}>ok</span>
                    )}
                    {isActive && (
                      <span style={{ fontSize: 9, color: "#2D3A52", fontWeight: 700, letterSpacing: "0.05em" }}>LIVE</span>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Footer */}
            <div style={{ padding: "12px 20px", borderTop: "1px solid rgba(45,58,82,0.08)", display: "flex", justifyContent: "flex-end" }}>
              <button
                onClick={() => setModalOpen(false)}
                disabled={!sweepDone}
                style={{ padding: "8px 20px", background: sweepDone ? "#2D3A52" : "rgba(45,58,82,0.06)", border: "none", borderRadius: 8, fontSize: 12, fontWeight: 700, color: sweepDone ? "#F5F2EE" : "rgba(45,58,82,0.3)", cursor: sweepDone ? "pointer" : "not-allowed", fontFamily: "'Inter',sans-serif", transition: "all 0.2s" }}>
                {sweepDone ? "Close" : "Sweeping…"}
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes panelIn { from { opacity: 0; transform: translateY(10px) scale(0.97); } to { opacity: 1; transform: none; } }
      `}</style>
    </div>
  );
}
