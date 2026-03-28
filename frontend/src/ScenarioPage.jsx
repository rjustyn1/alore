import { useState } from "react";
import StakeholderGuidance from "./StakeholderGuidance";

const SECTOR_COLORS = {
  food: "#E85550",
  energy: "#F0A020",
  water: "#3090E8",
  trade: "#18A87A",
  diplomacy: "#9B59D0",
  singapore: "#2D3A52",
};

const SECTOR_LABELS = {
  food: "Food Security",
  energy: "Energy",
  water: "Water Supply",
  trade: "Trade",
  diplomacy: "Diplomacy",
  singapore: "Singapore",
};

const SECTOR_ICONS = {
  food: "🌾",
  energy: "⚡",
  water: "💧",
  trade: "📦",
  diplomacy: "🤝",
  singapore: "🇸🇬",
};

const MITIGATION_SECTOR_ORDER = ["food", "energy", "water", "trade", "diplomacy"];

const MITIGATION_KEYWORDS = {
  food: ["food", "sfa", "supermarket", "rice", "poultry", "oil", "voucher", "grocery"],
  energy: ["energy", "oil", "lng", "petroleum", "fuel", "solar", "battery", "grid"],
  water: ["water", "desalination", "newater", "pipeline", "rationing", "pub"],
  trade: ["trade", "import", "export", "shipping", "freight", "port", "tariff", "wto", "sourcing"],
  diplomacy: ["diplomacy", "asean", "jakarta", "china", "mediation", "agreement", "consultation", "engage", "mti"],
};

const SEVERITY = {
  stable: { color: "#18A87A", bg: "rgba(24,168,122,0.1)", label: "Low Impact" },
  mild: { color: "#F0A020", bg: "rgba(240,160,32,0.1)", label: "Moderate" },
  urgent: { color: "#E85550", bg: "rgba(232,85,80,0.1)", label: "High Impact" },
};

const TIMEFRAME_LABELS = {
  immediate: "0–48h",
  "short-term": "1–4 wks",
  "medium-term": "1–6 mo",
  "long-term": "6+ mo",
};

const EXAMPLE_SCENARIOS = [
  "What if China restricts food exports to Singapore?",
  "What if oil prices spike 40% due to Middle East conflict?",
  "What if Malaysia cuts the Johor water pipeline?",
  "What if Indonesia bans palm oil exports?",
  "What if a major cyberattack hits Singapore's port infrastructure?",
];

const SYSTEM_PROMPT = `You are a Singapore supply chain risk analyst. Singapore's critical supply network includes:

WATER: Malaysia (Johor pipeline, 162 MGD — ~40% of daily needs), desalination (30%), NEWater (30%)
FOOD: Malaysia (fresh produce, poultry), Indonesia (rice, palm oil), Thailand (rice, seafood), China (processed foods, $2.1B trade), Australia (beef, wheat), India (onions, lentils), Brazil (soy, poultry)
ENERGY: Saudi Arabia (18% crude oil imports), Qatar (22% LNG supply)
TRADE: China ($136B, largest partner), Indonesia (ASEAN, $50B+), US (FTA, tech corridor), Japan (electronics), India (CECA), Germany (EU gateway)
DIPLOMACY: Five Eyes (AU, US), AUKUS, ASEAN chair role

Given a "what if" scenario, generate a realistic chain reaction showing how disruption cascades through Singapore's supply network.

Return ONLY valid JSON — no markdown, no code fences, no explanation — with exactly this structure:
{
  "scenario": "concise scenario title (under 60 chars)",
  "summary": "2-3 sentence executive summary with specific numbers where possible",
  "severity": "stable|mild|urgent",
  "chain": [
    {
      "step": 1,
      "entity": "entity name (country or 'Singapore')",
      "sector": "food|energy|water|trade|diplomacy|singapore",
      "severity": "stable|mild|urgent",
      "impact": "impact title under 55 chars",
      "detail": "1-2 sentences with specific numbers/percentages where possible",
      "timeframe": "immediate|short-term|medium-term|long-term"
    }
  ],
  "mitigations": ["specific action 1", "action 2", "action 3", "action 4"]
}

Chain should have 5-7 steps. Start with the trigger event, show primary effects on supply/price, cascade to secondary sectors, then show Singapore's systemic response needs.`;

function getMockResponse(prompt) {
  const p = prompt.toLowerCase();
  if (p.includes("water") || p.includes("malaysia") || p.includes("johor")) {
    return {
      scenario: "Malaysia restricts Johor water pipeline",
      summary:
        "A pipeline restriction would immediately threaten ~40% of Singapore's 430 MGD daily water demand. PUB emergency protocols and rapid desalination surge are the first lines of defence, but sustained disruption would require rationing within 72 hours.",
      severity: "urgent",
      chain: [
        {
          step: 1,
          entity: "Malaysia",
          sector: "water",
          severity: "urgent",
          impact: "Johor pipeline flow cut — 162 MGD offline",
          detail:
            "Singapore's largest single water source halted. PUB activates Tier 1 emergency protocol within hours.",
          timeframe: "immediate",
        },
        {
          step: 2,
          entity: "Singapore",
          sector: "water",
          severity: "urgent",
          impact: "40% supply deficit — emergency reserves activated",
          detail:
            "Desalination plants surge to 110% capacity (+26 MGD). NEWater output maximised. Strategic reserves provide ~14-day buffer.",
          timeframe: "immediate",
        },
        {
          step: 3,
          entity: "Singapore",
          sector: "singapore",
          severity: "urgent",
          impact: "Island-wide water rationing enforced",
          detail:
            "Non-essential usage banned within 48h. Car washing, irrigation, and decorative water features prohibited. Fines escalate.",
          timeframe: "short-term",
        },
        {
          step: 4,
          entity: "Singapore",
          sector: "trade",
          severity: "mild",
          impact: "Water-intensive industry capacity down 15–20%",
          detail:
            "Semiconductor fabs, food processing, and pharmaceuticals reduce throughput. Estimated S$400M/week GDP impact.",
          timeframe: "short-term",
        },
        {
          step: 5,
          entity: "Singapore",
          sector: "diplomacy",
          severity: "urgent",
          impact: "Emergency diplomatic escalation invoked",
          detail:
            "PM-level engagement activated. 1962 Water Agreement provisions cited. ASEAN Secretary-General notified.",
          timeframe: "immediate",
        },
        {
          step: 6,
          entity: "Singapore",
          sector: "water",
          severity: "stable",
          impact: "Emergency desalination tender fast-tracked",
          detail:
            "S$2.5B emergency procurement for two new 100 MGD desalination plants. Target: 18-month build timeline.",
          timeframe: "medium-term",
        },
      ],
      mitigations: [
        "Surge desalination to 110% capacity — immediate +26 MGD output",
        "Implement tiered water rationing scheme across all sectors",
        "Invoke 1962 Water Agreement and request ASEAN mediation",
        "Fast-track S$2.5B emergency desalination capacity procurement",
      ],
    };
  }
  if (p.includes("oil") || p.includes("energy") || p.includes("fuel")) {
    return {
      scenario: "Oil prices spike 40% — Middle East escalation",
      summary:
        "A 40% oil spike would compress Singapore's refinery margins, add ~18% to shipping costs, and push CPI 1.8–2.4 percentage points higher within 8 weeks. Singapore's strategic petroleum reserve provides a 30-day buffer before structural adjustments are required.",
      severity: "urgent",
      chain: [
        {
          step: 1,
          entity: "Saudi Arabia / Qatar",
          sector: "energy",
          severity: "urgent",
          impact: "Crude +40%, LNG rerouted via Cape of Good Hope",
          detail:
            "Saudi crude rises from ~$80 to ~$112/bbl. Qatar LNG adds 12–14 days via Red Sea bypass, raising freight 18%.",
          timeframe: "immediate",
        },
        {
          step: 2,
          entity: "Singapore",
          sector: "energy",
          severity: "urgent",
          impact: "Refinery input costs surge — margins compressed",
          detail:
            "Singapore processes ~1.5M barrels/day. Refinery sector loses est. S$800M/month in margin compression.",
          timeframe: "immediate",
        },
        {
          step: 3,
          entity: "Singapore",
          sector: "trade",
          severity: "mild",
          impact: "Port bunker surcharges +18% on all routes",
          detail:
            "All outbound shipping lanes apply emergency fuel surcharge. Port throughput unaffected; freight costs rise.",
          timeframe: "short-term",
        },
        {
          step: 4,
          entity: "Singapore",
          sector: "food",
          severity: "mild",
          impact: "Food import costs up 6–9% via transport surcharges",
          detail:
            "Cold chain and processed goods most affected. Supermarket CPI component rises within 3–4 weeks.",
          timeframe: "short-term",
        },
        {
          step: 5,
          entity: "Singapore",
          sector: "singapore",
          severity: "mild",
          impact: "CPI inflation +1.8–2.4 percentage points",
          detail:
            "MAS reviews monetary policy stance. Government likely to issue cost-of-living support package for lower-income households.",
          timeframe: "medium-term",
        },
        {
          step: 6,
          entity: "Singapore",
          sector: "energy",
          severity: "stable",
          impact: "Strategic reserve + spot LNG diversification",
          detail:
            "30-day strategic petroleum reserve released. Spot LNG contracts activated with US Gulf Coast and Australian suppliers.",
          timeframe: "medium-term",
        },
      ],
      mitigations: [
        "Release 30-day strategic petroleum reserve to stabilise local prices",
        "Activate spot LNG contracts with US and Australian suppliers",
        "Issue cost-of-living support package for lower-income households",
        "Accelerate solar + battery grid tenders to reduce import dependency",
      ],
    };
  }
  if (p.includes("indonesia") || p.includes("palm oil")) {
    return {
      scenario: "Indonesia bans palm oil exports",
      summary:
        "An Indonesian palm oil export ban would disrupt Singapore's food manufacturing sector and raise processed food costs by 8–14%. Singapore would need to rapidly activate alternative sourcing from Malaysia and global spot markets.",
      severity: "mild",
      chain: [
        {
          step: 1,
          entity: "Indonesia",
          sector: "food",
          severity: "urgent",
          impact: "Palm oil export ban — immediate supply cut",
          detail:
            "Indonesia supplies ~60% of global palm oil. Singapore food manufacturers lose primary ingredient source.",
          timeframe: "immediate",
        },
        {
          step: 2,
          entity: "Singapore",
          sector: "food",
          severity: "mild",
          impact: "Food manufacturing costs rise 8–14%",
          detail:
            "Palm oil is a key ingredient in baked goods, instant noodles, and processed snacks. Supply chain disruption within 2 weeks.",
          timeframe: "short-term",
        },
        {
          step: 3,
          entity: "Singapore",
          sector: "trade",
          severity: "mild",
          impact: "ASEAN bilateral trade strained",
          detail:
            "Singapore-Indonesia trade ($50B+ annually) faces diplomatic tension. MTI opens emergency consultations.",
          timeframe: "short-term",
        },
        {
          step: 4,
          entity: "Malaysia / Global",
          sector: "food",
          severity: "stable",
          impact: "Alternative sourcing activated at premium",
          detail:
            "Malaysian palm oil and Ukrainian sunflower oil sourced at 15–20% premium. SFA diversification protocols engaged.",
          timeframe: "short-term",
        },
        {
          step: 5,
          entity: "Singapore",
          sector: "singapore",
          severity: "mild",
          impact: "CPI food component +1.2% — vouchers considered",
          detail:
            "Government monitors food CPI weekly. Essential goods voucher scheme pre-positioned for deployment.",
          timeframe: "medium-term",
        },
      ],
      mitigations: [
        "Activate SFA emergency palm oil sourcing from Malaysia and spot markets",
        "Engage MTI for ASEAN diplomatic consultations with Jakarta",
        "Pre-position essential food vouchers for lower-income households",
        "Diversify to sunflower and canola oil across food manufacturing",
      ],
    };
  }
  return {
    scenario: "China restricts food exports to Singapore",
    summary:
      "China's 34% food tariff would directly impact $2.1B in annual bilateral food trade, driving processed food costs up 12–18% within weeks. Singapore's food security is manageable via diversification, but the diplomatic and inflation impacts require immediate coordinated response.",
    severity: "urgent",
    chain: [
      {
        step: 1,
        entity: "China",
        sector: "food",
        severity: "urgent",
        impact: "34% tariff on Singapore food imports active",
        detail:
          "$2.1B annual bilateral food trade affected. Processed foods, sauces, and packaged goods hit hardest within 21 days.",
        timeframe: "immediate",
      },
      {
        step: 2,
        entity: "Singapore",
        sector: "food",
        severity: "urgent",
        impact: "Food import costs spike 12–18%",
        detail:
          "Supermarket shelves reflect increases within 3–4 weeks. F&B sector margin compression forces menu price hikes.",
        timeframe: "short-term",
      },
      {
        step: 3,
        entity: "Singapore",
        sector: "trade",
        severity: "mild",
        impact: "Bilateral trade relationship strained",
        detail:
          "China is Singapore's largest trade partner at $136B annually. MTI initiates quiet diplomatic engagement; WTO options assessed.",
        timeframe: "immediate",
      },
      {
        step: 4,
        entity: "Australia / Thailand",
        sector: "food",
        severity: "stable",
        impact: "Alternative sourcing accelerated 20–30%",
        detail:
          "SFA activates food diversification protocols. Australian beef and Thai rice suppliers increase orders. India lentils sourced.",
        timeframe: "short-term",
      },
      {
        step: 5,
        entity: "Singapore",
        sector: "singapore",
        severity: "mild",
        impact: "CPI food component +2.1% — voucher scheme",
        detail:
          "MAS monitors core inflation. Government deploys GST voucher expansion and supermarket support for essential items.",
        timeframe: "medium-term",
      },
      {
        step: 6,
        entity: "Singapore",
        sector: "diplomacy",
        severity: "mild",
        impact: "Back-channel diplomatic engagement activated",
        detail:
          "PM-level call requested. Singapore avoids public escalation, pursues quiet ASEAN-framework diplomacy to preserve trade relationship.",
        timeframe: "medium-term",
      },
    ],
    mitigations: [
      "Activate SFA import diversification to Australia, Thailand, and India",
      "Deploy expanded GST vouchers and supermarket essentials support",
      "Initiate WTO consultations on discriminatory tariff measures",
      "Engage China through ASEAN back-channel to de-escalate",
    ],
  };
}

async function simulateScenario(prompt) {
  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;
  if (!apiKey) return getMockResponse(prompt);
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-calls": "true",
    },
    body: JSON.stringify({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 1400,
      system: SYSTEM_PROMPT,
      messages: [{ role: "user", content: prompt }],
    }),
  });
  if (!response.ok) throw new Error(`API ${response.status}`);
  const data = await response.json();
  const text = data.content[0].text.trim();
  const clean = text
    .replace(/^```json\s*/, "")
    .replace(/\s*```$/, "")
    .trim();
  return JSON.parse(clean);
}

function ChainStep({ step, index, total, animKey }) {
  const [expanded, setExpanded] = useState(false);
  const sc = SECTOR_COLORS[step.sector] || "#2D3A52";
  const sv = SEVERITY[step.severity] || SEVERITY.mild;
  const isLast = index === total - 1;
  const delay = index * 0.14;

  return (
    <div
      style={{ display: "flex", gap: 0, position: "relative" }}
      key={`${animKey}-${index}`}
    >
      {/* Spine column */}
      <div
        style={{
          width: 44,
          flexShrink: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {/* Node dot with ripple */}
        <div
          style={{ position: "relative", width: 36, height: 36, flexShrink: 0 }}
        >
          {/* Ripple ring 1 */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "50%",
              border: `1.5px solid ${sc}`,
              animation: `nodeRipple1 1.6s cubic-bezier(0.2,0,0.4,1) ${delay + 0.05}s both`,
            }}
          />
          {/* Ripple ring 2 */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              borderRadius: "50%",
              border: `1px solid ${sc}`,
              animation: `nodeRipple2 1.6s cubic-bezier(0.2,0,0.4,1) ${delay + 0.25}s both`,
            }}
          />
          {/* Main circle */}
          <div
            style={{
              position: "absolute",
              inset: 6,
              borderRadius: "50%",
              background: sc,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 10,
              fontWeight: 800,
              color: "#fff",
              animation: `nodeAppear 0.35s cubic-bezier(0.34,1.56,0.64,1) ${delay}s both`,
              boxShadow: `0 2px 10px ${sc}55`,
              cursor: "default",
            }}
          >
            {step.step}
          </div>
        </div>

        {/* Connector line to next step */}
        {!isLast && (
          <div
            style={{
              flex: 1,
              width: 2,
              minHeight: 20,
              background: `linear-gradient(to bottom, ${sc}88, ${
                SECTOR_COLORS[
                  // fade to next step's color (approximated as transparent)
                  "singapore"
                ]
              }22)`,
              animation: `connectorDraw 0.4s ease ${delay + 0.28}s both`,
              transformOrigin: "top",
            }}
          />
        )}
      </div>

      {/* Card */}
      <div
        style={{
          flex: 1,
          marginBottom: isLast ? 0 : 12,
          marginTop: 2,
          animation: `cardSlide 0.4s cubic-bezier(0.4,0,0.2,1) ${delay}s both`,
        }}
      >
        <div
          onClick={() => setExpanded((v) => !v)}
          style={{
            background: expanded ? "#FDFCFA" : "rgba(253,252,250,0.85)",
            border: `1px solid ${expanded ? sc + "44" : "rgba(45,58,82,0.08)"}`,
            borderRadius: 12,
            overflow: "hidden",
            cursor: "pointer",
            transition: "border-color 0.2s, box-shadow 0.2s, background 0.2s",
            boxShadow: expanded ? `0 2px 20px ${sc}18` : "none",
          }}
          onMouseEnter={(e) => {
            if (!expanded) {
              e.currentTarget.style.borderColor = sc + "33";
              e.currentTarget.style.boxShadow = `0 2px 12px ${sc}12`;
            }
          }}
          onMouseLeave={(e) => {
            if (!expanded) {
              e.currentTarget.style.borderColor = "rgba(45,58,82,0.08)";
              e.currentTarget.style.boxShadow = "none";
            }
          }}
        >
          {/* Sector color top bar */}
          <div
            style={{
              height: 3,
              background: `linear-gradient(to right, ${sc}, ${sc}66)`,
              opacity: expanded ? 1 : 0.5,
              transition: "opacity 0.2s",
            }}
          />

          {/* Collapsed header */}
          <div style={{ padding: "11px 14px 10px" }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 7,
                marginBottom: 6,
                flexWrap: "wrap",
              }}
            >
              {/* Sector icon + label */}
              <span style={{ fontSize: 13 }}>
                {SECTOR_ICONS[step.sector] || "•"}
              </span>
              <span
                style={{
                  fontSize: 9.5,
                  fontWeight: 800,
                  color: sc,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                }}
              >
                {step.entity}
              </span>
              <span
                style={{
                  fontSize: 9,
                  fontWeight: 600,
                  color: "rgba(45,58,82,0.4)",
                  background: "rgba(45,58,82,0.06)",
                  padding: "1px 7px",
                  borderRadius: 4,
                }}
              >
                {SECTOR_LABELS[step.sector] || step.sector}
              </span>
              <span
                style={{
                  fontSize: 9,
                  fontWeight: 600,
                  color: "rgba(45,58,82,0.32)",
                  marginLeft: 1,
                }}
              >
                · {TIMEFRAME_LABELS[step.timeframe] || step.timeframe}
              </span>
              <span
                style={{
                  marginLeft: "auto",
                  fontSize: 8,
                  fontWeight: 700,
                  padding: "2px 8px",
                  borderRadius: 10,
                  background: sv.bg,
                  color: sv.color,
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                  border: `1px solid ${sv.color}30`,
                  flexShrink: 0,
                }}
              >
                {sv.label}
              </span>
            </div>

            {/* Impact title */}
            <div
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: "rgba(45,58,82,0.92)",
                lineHeight: 1.3,
                letterSpacing: "-0.01em",
              }}
            >
              {step.impact}
            </div>

            {/* Expand hint */}
            {!expanded && (
              <div
                style={{
                  fontSize: 10,
                  color: "rgba(45,58,82,0.28)",
                  marginTop: 5,
                  fontWeight: 500,
                }}
              >
                Tap to expand ↓
              </div>
            )}
          </div>

          {/* Expanded detail */}
          <div
            style={{
              maxHeight: expanded ? 200 : 0,
              overflow: "hidden",
              transition: "max-height 0.35s cubic-bezier(0.4,0,0.2,1)",
            }}
          >
            <div
              style={{
                padding: "0 14px 13px",
                borderTop: `1px solid ${sc}22`,
                marginTop: 0,
              }}
            >
              <div
                style={{
                  height: 1,
                  background: `linear-gradient(to right, ${sc}33, transparent)`,
                  marginBottom: 10,
                  marginTop: 10,
                }}
              />
              <div
                style={{
                  fontSize: 12,
                  color: "rgba(45,58,82,0.65)",
                  lineHeight: 1.7,
                }}
              >
                {step.detail}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function buildMitigationCards(result) {
  const mitigations = result?.mitigations || [];
  const chain = result?.chain || [];
  const impacted = new Set(
    chain
      .map((step) => step.sector)
      .filter((sector) => MITIGATION_SECTOR_ORDER.includes(sector)),
  );
  const bucket = Object.fromEntries(MITIGATION_SECTOR_ORDER.map((sector) => [sector, []]));

  mitigations.forEach((mitigation) => {
    const text = mitigation.toLowerCase();
    let bestSector = null;
    let bestScore = 0;

    MITIGATION_SECTOR_ORDER.forEach((sector) => {
      const score = MITIGATION_KEYWORDS[sector].reduce(
        (sum, keyword) => sum + (text.includes(keyword) ? 1 : 0),
        0,
      );
      if (score > bestScore) {
        bestScore = score;
        bestSector = sector;
      }
    });

    if (bestSector && bestScore > 0) {
      bucket[bestSector].push(mitigation);
    }
  });

  const sectorsToShow = MITIGATION_SECTOR_ORDER.filter(
    (sector) => impacted.has(sector) || bucket[sector].length > 0,
  );

  return (sectorsToShow.length > 0 ? sectorsToShow : MITIGATION_SECTOR_ORDER).map((sector) => ({
    sector,
    actions: bucket[sector],
  }));
}

export default function ScenarioPage({ onNavigate: _onNavigate }) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [animKey, setAnimKey] = useState(0);
  const [pipelineStep, setPipelineStep] = useState(-1);
  const [pipelineDone, setPipelineDone] = useState([]);

  const PIPELINE = [
    {
      icon: "🔍",
      label: "Scanning live sources",
      detail: "Reuters · Bloomberg · Straits Times · MFA.gov.sg",
    },
    {
      icon: "📄",
      label: "Extracting relevant signals",
      detail: "Matching articles · Active price feeds · Trade advisories",
    },
    {
      icon: "⚖",
      label: "Cross-referencing market indices",
      detail: "Commodity prices · Shipping freight · FX rates",
    },
    {
      icon: "🧠",
      label: "Synthesising cascade model",
      detail: "Building impact chain across sectors",
    },
  ];

  const handleSimulate = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setError(null);
    setPipelineStep(0);
    setPipelineDone([]);

    // Start API call concurrently with animation
    const apiPromise = simulateScenario(prompt).catch((e) => {
      setError(e.message);
      return null;
    });

    // Animate steps 0–2 with fake delays
    for (let i = 0; i < 3; i++) {
      setPipelineStep(i);
      await new Promise((r) => setTimeout(r, 750 + Math.random() * 450));
      setPipelineDone((prev) => [...prev, i]);
    }

    // Step 3 waits for real API response
    setPipelineStep(3);
    const data = await apiPromise;
    setPipelineDone((prev) => [...prev, 3]);

    if (data) {
      setResult(data);
      setAnimKey((k) => k + 1);
      try {
        const entry = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          prompt: prompt.trim(),
          scenario: data.scenario,
          summary: data.summary,
          severity: data.severity,
          chain: data.chain || [],
          mitigations: data.mitigations || [],
        };
        const prev = JSON.parse(localStorage.getItem("alore_scenarios") || "[]");
        localStorage.setItem(
          "alore_scenarios",
          JSON.stringify([entry, ...prev].slice(0, 50)),
        );
      } catch {
        /* storage unavailable */
      }
    }
    setLoading(false);
    setPipelineStep(-1);
  };

  const sev = result ? SEVERITY[result.severity] || SEVERITY.mild : null;
  const mitigationCards = result ? buildMitigationCards(result) : [];

  return (
    <div
      style={{
        height: "100%",
        background: "#F5F2EE",
        fontFamily: "'Inter', sans-serif",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* ── Nav bar ── */}
      <div
        style={{
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          padding: "0 20px",
          height: 52,
          borderBottom: "1px solid rgba(45,58,82,0.1)",
          background: "#FDFCFA",
          gap: 14,
        }}
      >
        <span
          style={{
            fontSize: 13,
            fontWeight: 700,
            color: "rgba(45,58,82,0.9)",
            letterSpacing: "-0.01em",
          }}
        >
          Scenario Simulator
        </span>
        <span
          style={{
            fontSize: 11,
            color: "rgba(45,58,82,0.35)",
            fontWeight: 500,
          }}
        >
          — AI-powered supply chain impact analysis
        </span>
      </div>

      {/* ── Scrollable content ── */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 24px 40px",
        }}
      >
        {/* ── Prompt card ── */}
        <div
          style={{
            background: "#FDFCFA",
            border: "1px solid rgba(45,58,82,0.1)",
            borderRadius: 14,
            padding: "18px 18px 14px",
            marginBottom: 20,
          }}
        >
          <div
            style={{
              fontSize: 9.5,
              fontWeight: 800,
              color: "rgba(45,58,82,0.38)",
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              marginBottom: 11,
            }}
          >
            Simulate a supply chain scenario
          </div>
          <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSimulate();
                }
              }}
              placeholder="e.g. What if China restricts food exports to Singapore?"
              rows={2}
              style={{
                flex: 1,
                background: "rgba(45,58,82,0.04)",
                border: "1px solid rgba(45,58,82,0.12)",
                borderRadius: 10,
                padding: "10px 14px",
                fontSize: 13,
                fontFamily: "'Inter', sans-serif",
                color: "rgba(45,58,82,0.9)",
                resize: "none",
                outline: "none",
                lineHeight: 1.5,
              }}
            />
            <button
              onClick={handleSimulate}
              disabled={!prompt.trim() || loading}
              style={{
                alignSelf: "stretch",
                padding: "0 22px",
                background:
                  prompt.trim() && !loading ? "#2D3A52" : "rgba(45,58,82,0.12)",
                border: "none",
                borderRadius: 10,
                fontSize: 13,
                fontWeight: 700,
                color:
                  prompt.trim() && !loading ? "#F5F2EE" : "rgba(45,58,82,0.3)",
                cursor: prompt.trim() && !loading ? "pointer" : "default",
                fontFamily: "'Inter', sans-serif",
                transition: "all 0.18s",
                whiteSpace: "nowrap",
              }}
            >
              {loading ? "Simulating…" : "Simulate →"}
            </button>
          </div>
          {/* Example chips */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
            <span
              style={{
                fontSize: 9.5,
                fontWeight: 600,
                color: "rgba(45,58,82,0.32)",
                alignSelf: "center",
                marginRight: 2,
              }}
            >
              Try:
            </span>
            {EXAMPLE_SCENARIOS.map((s, i) => (
              <button
                key={i}
                onClick={() => setPrompt(s)}
                style={{
                  padding: "4px 10px",
                  background: "rgba(45,58,82,0.05)",
                  border: "1px solid rgba(45,58,82,0.1)",
                  borderRadius: 20,
                  fontSize: 10.5,
                  fontWeight: 500,
                  color: "rgba(45,58,82,0.6)",
                  cursor: "pointer",
                  fontFamily: "'Inter', sans-serif",
                  transition: "all 0.14s",
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.background = "rgba(45,58,82,0.1)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.background = "rgba(45,58,82,0.05)")
                }
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* ── Loading ── */}
        {loading && (
          <div
            style={{
              background: "#FDFCFA",
              border: "1px solid rgba(45,58,82,0.1)",
              borderRadius: 14,
              padding: "20px 20px 16px",
              marginBottom: 16,
            }}
          >
            <div
              style={{
                fontSize: 9,
                fontWeight: 800,
                color: "rgba(45,58,82,0.32)",
                textTransform: "uppercase",
                letterSpacing: "0.13em",
                marginBottom: 14,
              }}
            >
              Agent Pipeline
            </div>
            {PIPELINE.map((step, i) => {
              const isDone = pipelineDone.includes(i);
              const isActive = pipelineStep === i && !isDone;
              return (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 12,
                    marginBottom: i < PIPELINE.length - 1 ? 14 : 0,
                    opacity: pipelineStep < i ? 0.3 : 1,
                    transition: "opacity 0.3s",
                  }}
                >
                  {/* Step icon / spinner / check */}
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      flexShrink: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      borderRadius: 8,
                      background: isDone
                        ? "rgba(24,168,122,0.1)"
                        : isActive
                          ? "rgba(45,58,82,0.06)"
                          : "rgba(45,58,82,0.04)",
                      border: `1px solid ${isDone ? "rgba(24,168,122,0.25)" : "rgba(45,58,82,0.1)"}`,
                      fontSize: 14,
                    }}
                  >
                    {isDone ? (
                      <span style={{ fontSize: 13, color: "#18A87A" }}>✓</span>
                    ) : isActive ? (
                      <div
                        style={{
                          width: 12,
                          height: 12,
                          border: "2px solid rgba(45,58,82,0.12)",
                          borderTopColor: "#2D3A52",
                          borderRadius: "50%",
                          animation: "spin 0.7s linear infinite",
                        }}
                      />
                    ) : (
                      <span>{step.icon}</span>
                    )}
                  </div>
                  <div style={{ flex: 1, paddingTop: 2 }}>
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: isDone ? 600 : isActive ? 700 : 500,
                        color: isDone
                          ? "rgba(45,58,82,0.5)"
                          : isActive
                            ? "rgba(45,58,82,0.9)"
                            : "rgba(45,58,82,0.35)",
                        marginBottom: 2,
                      }}
                    >
                      {step.label}
                      {isActive && (
                        <span
                          style={{
                            color: "rgba(45,58,82,0.35)",
                            fontWeight: 400,
                          }}
                        >
                          {" "}
                          …
                        </span>
                      )}
                    </div>
                    <div
                      style={{
                        fontSize: 10.5,
                        color: isDone
                          ? "rgba(45,58,82,0.35)"
                          : isActive
                            ? "rgba(45,58,82,0.45)"
                            : "rgba(45,58,82,0.2)",
                      }}
                    >
                      {step.detail}
                    </div>
                  </div>
                  {/* Connector line */}
                </div>
              );
            })}
          </div>
        )}

        {/* ── Error ── */}
        {error && (
          <div
            style={{
              padding: "14px 16px",
              background: "rgba(232,85,80,0.08)",
              border: "1px solid rgba(232,85,80,0.22)",
              borderRadius: 10,
              color: "#E85550",
              fontSize: 12,
              marginBottom: 16,
            }}
          >
            ⚠ {error}
          </div>
        )}

        {/* ── Results ── */}
        {result && !loading && (
          <div key={animKey}>
            {/* Scenario header card */}
            <div
              style={{
                background: "#FDFCFA",
                border: `1px solid ${sev.color}33`,
                borderRadius: 14,
                overflow: "hidden",
                marginBottom: 22,
                animation: "panelIn 0.4s cubic-bezier(0.4,0,0.2,1) both",
                boxShadow: `0 4px 24px ${sev.color}14`,
              }}
            >
              <div
                style={{
                  height: 4,
                  background: `linear-gradient(to right, ${sev.color}, ${sev.color}88)`,
                }}
              />
              <div style={{ padding: "16px 18px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                    gap: 12,
                    marginBottom: 9,
                  }}
                >
                  <div
                    style={{
                      fontSize: 18,
                      fontWeight: 800,
                      color: "rgba(45,58,82,0.95)",
                      letterSpacing: "-0.02em",
                      lineHeight: 1.2,
                    }}
                  >
                    {result.scenario}
                  </div>
                  <span
                    style={{
                      flexShrink: 0,
                      fontSize: 9,
                      fontWeight: 800,
                      padding: "4px 11px",
                      borderRadius: 20,
                      background: sev.bg,
                      color: sev.color,
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      border: `1px solid ${sev.color}44`,
                    }}
                  >
                    {sev.label}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 12.5,
                    color: "rgba(45,58,82,0.58)",
                    lineHeight: 1.65,
                  }}
                >
                  {result.summary}
                </div>
              </div>
            </div>

            {/* Chain reaction label */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: 14,
                paddingLeft: 2,
              }}
            >
              <div
                style={{
                  fontSize: 9,
                  fontWeight: 800,
                  color: "rgba(45,58,82,0.32)",
                  textTransform: "uppercase",
                  letterSpacing: "0.13em",
                }}
              >
                Cascade Chain
              </div>
              <div
                style={{
                  flex: 1,
                  height: 1,
                  background:
                    "linear-gradient(to right, rgba(45,58,82,0.12), transparent)",
                }}
              />
              <div
                style={{
                  fontSize: 9.5,
                  color: "rgba(45,58,82,0.28)",
                  fontWeight: 500,
                }}
              >
                {result.chain.length} steps · tap any to expand
              </div>
            </div>

            {/* Chain steps */}
            <div style={{ paddingLeft: 4 }}>
              {result.chain.map((step, i) => (
                <ChainStep
                  key={`${animKey}-${i}`}
                  step={step}
                  index={i}
                  total={result.chain.length}
                  animKey={animKey}
                />
              ))}
            </div>

            {/* Mitigations */}
            {result.mitigations?.length > 0 && (
              <div
                style={{
                  background: "#FDFCFA",
                  border: "1px solid rgba(45,58,82,0.1)",
                  borderRadius: 14,
                  overflow: "hidden",
                  marginTop: 20,
                  animation: `panelIn 0.4s cubic-bezier(0.4,0,0.2,1) ${
                    result.chain.length * 0.14 + 0.2
                  }s both`,
                }}
              >
                <div
                  style={{
                    height: 3,
                    background:
                      "linear-gradient(to right, #18A87A, #3090E8, #2D3A52)",
                  }}
                />
                <div style={{ padding: "14px 16px" }}>
                  <div
                    style={{
                      fontSize: 9,
                      fontWeight: 800,
                      color: "rgba(45,58,82,0.32)",
                      textTransform: "uppercase",
                      letterSpacing: "0.12em",
                      marginBottom: 12,
                    }}
                  >
                    Recommended Mitigations
                  </div>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
                      gap: 10,
                    }}
                  >
                    {mitigationCards.map(({ sector, actions }) => (
                      <div
                        key={sector}
                        style={{
                          border: `1px solid ${SECTOR_COLORS[sector]}33`,
                          borderRadius: 12,
                          background: `${SECTOR_COLORS[sector]}0D`,
                          padding: "10px 11px",
                          minHeight: 112,
                          display: "flex",
                          flexDirection: "column",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 7,
                            marginBottom: 8,
                          }}
                        >
                          <span style={{ fontSize: 13 }}>{SECTOR_ICONS[sector] || "•"}</span>
                          <span
                            style={{
                              fontSize: 9.5,
                              fontWeight: 800,
                              color: SECTOR_COLORS[sector],
                              textTransform: "uppercase",
                              letterSpacing: "0.09em",
                            }}
                          >
                            {SECTOR_LABELS[sector] || sector}
                          </span>
                        </div>
                        {actions.length > 0 ? (
                          actions.slice(0, 2).map((action, i) => (
                            <div
                              key={`${sector}-${i}`}
                              style={{
                                display: "flex",
                                gap: 8,
                                alignItems: "flex-start",
                                marginBottom: i === actions.length - 1 ? 0 : 6,
                              }}
                            >
                              <div
                                style={{
                                  width: 16,
                                  height: 16,
                                  borderRadius: "50%",
                                  background: `${SECTOR_COLORS[sector]}1A`,
                                  border: `1px solid ${SECTOR_COLORS[sector]}44`,
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontSize: 8,
                                  fontWeight: 700,
                                  color: SECTOR_COLORS[sector],
                                  flexShrink: 0,
                                  marginTop: 1,
                                }}
                              >
                                {i + 1}
                              </div>
                              <div
                                style={{
                                  fontSize: 11.5,
                                  color: "rgba(45,58,82,0.8)",
                                  lineHeight: 1.45,
                                }}
                              >
                                {action}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div
                            style={{
                              fontSize: 11.5,
                              color: "rgba(45,58,82,0.5)",
                              lineHeight: 1.45,
                              fontStyle: "italic",
                            }}
                          >
                            No direct mitigation generated for this sector in this run.
                          </div>
                        )}
                        {actions.length > 2 && (
                          <div
                            style={{
                              fontSize: 10,
                              color: "rgba(45,58,82,0.42)",
                              marginTop: "auto",
                              paddingTop: 8,
                            }}
                          >
                            +{actions.length - 2} more action{actions.length - 2 > 1 ? "s" : ""}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Stakeholder Guidance */}
            <StakeholderGuidance
              animDelay={result.chain.length * 0.14 + 0.5}
            />
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes nodeAppear {
          from { opacity: 0; transform: scale(0.4); }
          to   { opacity: 1; transform: scale(1); }
        }
        @keyframes nodeRipple1 {
          0%   { opacity: 0.7; transform: scale(0.6); }
          100% { opacity: 0;   transform: scale(2.2); }
        }
        @keyframes nodeRipple2 {
          0%   { opacity: 0.45; transform: scale(0.6); }
          100% { opacity: 0;    transform: scale(2.8); }
        }
        @keyframes connectorDraw {
          from { transform: scaleY(0); opacity: 0; }
          to   { transform: scaleY(1); opacity: 1; }
        }
        @keyframes cardSlide {
          from { opacity: 0; transform: translateX(-10px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
