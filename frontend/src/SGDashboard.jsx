import { useEffect, useMemo, useRef, useState } from "react";
import StakeholderGuidance from "./StakeholderGuidance";

// Robinson projection lookup tables (per 5° latitude, 0°–90°)
const ROB_X = [
  1.0, 0.9986, 0.9954, 0.99, 0.9822, 0.973, 0.96, 0.9427, 0.9216, 0.8962,
  0.8679, 0.835, 0.7986, 0.7597, 0.7186, 0.6732, 0.6213, 0.5722, 0.5322,
];
const ROB_Y = [
  0.0, 0.062, 0.124, 0.186, 0.248, 0.31, 0.372, 0.434, 0.4958, 0.5571, 0.6176,
  0.6769, 0.7346, 0.7903, 0.8435, 0.8936, 0.9394, 0.9761, 1.0,
];

const SECTORS = {
  food: { color: "#E85550", label: "Food Security" },
  energy: { color: "#F0A020", label: "Energy" },
  water: { color: "#3090E8", label: "Water Supply" },
  trade: { color: "#18A87A", label: "Trade" },
  diplomacy: { color: "#9B59D0", label: "Diplomacy" },
};

const COUNTRY_DOT_RADIUS = {
  MY: 9,
  ID: 16,
  TH: 9,
  CN: 22,
  AU: 24,
  US: 28,
  JP: 9,
  SA: 13,
  QA: 7,
  IN: 16,
  BR: 22,
  DE: 9,
};

const FLAGS = {
  MY: "🇲🇾",
  ID: "🇮🇩",
  TH: "🇹🇭",
  CN: "🇨🇳",
  AU: "🇦🇺",
  US: "🇺🇸",
  JP: "🇯🇵",
  SA: "🇸🇦",
  QA: "🇶🇦",
  IN: "🇮🇳",
  BR: "🇧🇷",
  DE: "🇩🇪",
};

const ROUTES = [
  {
    country: "Malaysia",
    code: "MY",
    lat: 3.1,
    lon: 101.7,
    sector: "water",
    note: "Johor pipeline — 162 MGD daily supply",
    status: "stable",
  },
  {
    country: "Malaysia",
    code: "MY",
    lat: 3.1,
    lon: 101.7,
    sector: "food",
    note: "Fresh produce and poultry corridor",
    status: "stable",
  },
  {
    country: "Indonesia",
    code: "ID",
    lat: -6.2,
    lon: 106.8,
    sector: "food",
    note: "Rice, palm oil, and vegetables",
    status: "stable",
  },
  {
    country: "Indonesia",
    code: "ID",
    lat: -6.2,
    lon: 106.8,
    sector: "trade",
    note: "ASEAN bilateral trade — $50B+",
    status: "stable",
  },
  {
    country: "Thailand",
    code: "TH",
    lat: 13.7,
    lon: 100.5,
    sector: "food",
    note: "Rice and seafood — alternative buffer",
    status: "stable",
  },
  {
    country: "China",
    code: "CN",
    lat: 35.9,
    lon: 104.2,
    sector: "food",
    note: "⚠ Tariff escalation — 34% duty active",
    status: "disrupted",
  },
  {
    country: "China",
    code: "CN",
    lat: 35.9,
    lon: 104.2,
    sector: "trade",
    note: "Largest trading partner — $136B annual",
    status: "mild",
  },
  {
    country: "Australia",
    code: "AU",
    lat: -25.3,
    lon: 133.8,
    sector: "food",
    note: "Wheat, beef, dairy imports",
    status: "stable",
  },
  {
    country: "Australia",
    code: "AU",
    lat: -25.3,
    lon: 133.8,
    sector: "diplomacy",
    note: "Five Eyes and AUKUS alignment",
    status: "stable",
  },
  {
    country: "United States",
    code: "US",
    lat: 37.1,
    lon: -95.7,
    sector: "diplomacy",
    note: "Key security and strategic partner",
    status: "stable",
  },
  {
    country: "United States",
    code: "US",
    lat: 37.1,
    lon: -95.7,
    sector: "trade",
    note: "FTA, financial services, tech corridor",
    status: "stable",
  },
  {
    country: "Japan",
    code: "JP",
    lat: 36.2,
    lon: 138.3,
    sector: "trade",
    note: "Electronics and shipping coordination",
    status: "stable",
  },
  {
    country: "Japan",
    code: "JP",
    lat: 36.2,
    lon: 138.3,
    sector: "diplomacy",
    note: "Regional security cooperation",
    status: "stable",
  },
  {
    country: "Saudi Arabia",
    code: "SA",
    lat: 24.0,
    lon: 45.0,
    sector: "energy",
    note: "Crude oil — 18% of SG energy imports",
    status: "stable",
  },
  {
    country: "Qatar",
    code: "QA",
    lat: 25.4,
    lon: 51.2,
    sector: "energy",
    note: "LNG — 22% of SG gas supply",
    status: "mild",
  },
  {
    country: "India",
    code: "IN",
    lat: 20.6,
    lon: 78.9,
    sector: "trade",
    note: "CECA, port and logistics corridor",
    status: "stable",
  },
  {
    country: "India",
    code: "IN",
    lat: 20.6,
    lon: 78.9,
    sector: "food",
    note: "Onion, lentil and rice imports",
    status: "stable",
  },
  {
    country: "Brazil",
    code: "BR",
    lat: -14.2,
    lon: -51.9,
    sector: "food",
    note: "Soy and poultry — diversification route",
    status: "stable",
  },
  {
    country: "Germany",
    code: "DE",
    lat: 51.2,
    lon: 10.5,
    sector: "trade",
    note: "EU manufacturing and precision goods",
    status: "stable",
  },
  {
    country: "Germany",
    code: "DE",
    lat: 51.2,
    lon: 10.5,
    sector: "diplomacy",
    note: "EU diplomatic bridge partner",
    status: "stable",
  },
];

const NEWS_FALLBACK = [
  {
    tag: "diplomacy",
    headline: "Trump invokes Pearl Harbour in meeting with Japan PM Ishiba",
    snippet:
      "Remarks interpreted as leverage over trade concessions — markets flag elevated US-Japan tension ahead of tariff review.",
    url: "https://www.reuters.com",
  },
  {
    tag: "food",
    headline: "China raises tariffs 34% on Singapore-origin processed foods",
    snippet:
      "New duties take effect in 21 days, impacting an estimated $2.1B in annual bilateral food trade.",
    url: "https://www.straitstimes.com",
  },
  {
    tag: "energy",
    headline: "Qatar LNG shipments face Red Sea rerouting delays",
    snippet:
      "Three major carriers now bypassing Suez Canal, adding 12–14 days to delivery and pushing freight costs up 18%.",
    url: "https://www.bbc.com/news",
  },
  {
    tag: "trade",
    headline: "Indonesia tightens palm oil export quota for Q2 2026",
    snippet:
      "A 15% reduction vs prior quarter will affect Singapore's food manufacturing and downstream processing sectors.",
    url: "https://www.channelnewsasia.com",
  },
  {
    tag: "water",
    headline: "Malaysia–Singapore water agreement review set for 2027",
    snippet:
      "Johor officials signal intent to renegotiate pricing terms, raising long-term supply security questions.",
    url: "https://www.straitstimes.com",
  },
  {
    tag: "diplomacy",
    headline: "ASEAN ministers convene emergency session on South China Sea",
    snippet:
      "Singapore's FM Lawrence Wong chairs dialogue following increased Chinese naval activity near disputed zones.",
    url: "https://www.reuters.com",
  },
  {
    tag: "trade",
    headline:
      "US FTA review: Washington signals intent to revisit preferential terms",
    snippet:
      "Trade representative cites digital services and financial sector imbalances as key sticking points.",
    url: "https://www.ft.com",
  },
  {
    tag: "food",
    headline: "Australia beef exports to Singapore hit record high in Q1",
    snippet:
      "Strong demand and diversification push from Singapore buyers drove a 22% year-on-year increase.",
    url: "https://www.channelnewsasia.com",
  },
];

function inferNewsTag(title, hook) {
  const text = `${title} ${hook}`.toLowerCase();
  if (/oil|gas|lng|crude|fuel|energy|coal|diesel/.test(text)) return "energy";
  if (/rice|wheat|food|palm|beef|poultry|soy|dairy|produce|fish/.test(text)) return "food";
  if (/water|pipeline|johor|reservoir|desalin/.test(text)) return "water";
  if (/diplomat|asean|minister|treaty|bilateral|aukus|security/.test(text)) return "diplomacy";
  return "trade";
}

const LANDS = [
  [
    [-168, 60],
    [-165, 56],
    [-155, 58],
    [-138, 56],
    [-128, 50],
    [-124, 44],
    [-118, 34],
    [-114, 30],
    [-106, 22],
    [-98, 20],
    [-90, 18],
    [-84, 20],
    [-82, 24],
    [-80, 26],
    [-76, 34],
    [-70, 42],
    [-66, 44],
    [-60, 46],
    [-56, 48],
    [-52, 56],
    [-60, 72],
    [-100, 72],
    [-140, 72],
    [-168, 60],
  ],
  [
    [-44, 60],
    [-56, 68],
    [-48, 82],
    [-18, 76],
    [-18, 70],
    [-24, 64],
    [-44, 60],
  ],
  [
    [-90, 18],
    [-86, 14],
    [-84, 10],
    [-80, 8],
    [-78, 10],
    [-80, 12],
    [-84, 18],
    [-88, 18],
    [-90, 18],
  ],
  [
    [-78, 8],
    [-72, 10],
    [-66, 8],
    [-56, 4],
    [-44, 2],
    [-34, 6],
    [-36, -2],
    [-36, -10],
    [-38, -16],
    [-40, -22],
    [-44, -24],
    [-48, -28],
    [-52, -34],
    [-58, -38],
    [-66, -44],
    [-72, -44],
    [-74, -44],
    [-72, -38],
    [-70, -32],
    [-72, -22],
    [-72, -12],
    [-76, -4],
    [-78, 4],
  ],
  [
    [-10, 36],
    [-8, 38],
    [-4, 44],
    [2, 44],
    [6, 44],
    [8, 46],
    [10, 44],
    [14, 42],
    [18, 40],
    [22, 38],
    [24, 40],
    [28, 42],
    [28, 48],
    [24, 56],
    [18, 58],
    [12, 56],
    [8, 58],
    [4, 54],
    [0, 52],
    [-2, 50],
    [-4, 46],
    [-6, 44],
    [-8, 40],
    [-10, 36],
  ],
  [
    [6, 58],
    [10, 62],
    [14, 66],
    [18, 70],
    [24, 70],
    [28, 68],
    [28, 64],
    [24, 58],
    [18, 58],
    [14, 56],
    [10, 58],
    [6, 58],
  ],
  [
    [-6, 50],
    [-4, 50],
    [0, 52],
    [0, 56],
    [-2, 58],
    [-4, 58],
    [-6, 56],
    [-4, 52],
    [-6, 50],
  ],
  [
    [28, 60],
    [28, 72],
    [60, 72],
    [100, 72],
    [140, 72],
    [180, 68],
    [180, 50],
    [165, 52],
    [152, 48],
    [142, 48],
    [136, 46],
    [128, 44],
    [120, 50],
    [110, 52],
    [100, 52],
    [90, 56],
    [80, 58],
    [70, 56],
    [60, 56],
    [50, 54],
    [40, 56],
    [28, 60],
  ],
  [
    [26, 38],
    [30, 38],
    [36, 40],
    [42, 42],
    [54, 44],
    [64, 44],
    [70, 42],
    [66, 32],
    [58, 26],
    [52, 22],
    [44, 12],
    [38, 18],
    [36, 22],
    [36, 30],
    [40, 30],
    [42, 34],
    [38, 38],
    [30, 40],
    [26, 38],
  ],
  [
    [36, 30],
    [44, 30],
    [52, 26],
    [58, 20],
    [58, 16],
    [52, 12],
    [44, 12],
    [38, 16],
    [36, 22],
    [36, 30],
  ],
  [
    [62, 24],
    [68, 36],
    [76, 34],
    [80, 32],
    [82, 18],
    [80, 10],
    [76, 8],
    [72, 10],
    [66, 22],
    [62, 24],
  ],
  [
    [80, 46],
    [90, 50],
    [100, 52],
    [112, 52],
    [124, 52],
    [132, 48],
    [136, 46],
    [142, 38],
    [136, 34],
    [130, 28],
    [124, 24],
    [118, 22],
    [112, 18],
    [108, 18],
    [104, 20],
    [100, 22],
    [100, 16],
    [104, 10],
    [104, 2],
    [100, 0],
    [104, -2],
    [110, 0],
    [116, 0],
    [120, -2],
    [122, 2],
    [118, 6],
    [112, 8],
    [106, 18],
    [104, 22],
    [96, 28],
    [88, 28],
    [84, 30],
    [80, 32],
    [76, 34],
    [80, 40],
    [80, 46],
  ],
  [
    [130, 32],
    [132, 34],
    [136, 38],
    [138, 40],
    [140, 42],
    [140, 44],
    [136, 44],
    [132, 42],
    [130, 36],
    [130, 32],
  ],
  [
    [-18, 16],
    [-14, 10],
    [-12, 6],
    [-8, 4],
    [0, 4],
    [6, 4],
    [12, 4],
    [14, 0],
    [14, -6],
    [14, -16],
    [16, -20],
    [20, -26],
    [24, -32],
    [28, -34],
    [30, -32],
    [34, -22],
    [36, -14],
    [40, -10],
    [42, -4],
    [44, 4],
    [44, 10],
    [38, 18],
    [36, 22],
    [36, 28],
    [32, 30],
    [20, 30],
    [10, 30],
    [4, 22],
    [0, 16],
    [-4, 14],
    [-8, 14],
    [-12, 14],
    [-18, 14],
  ],
  [
    [44, -12],
    [48, -14],
    [50, -18],
    [48, -24],
    [44, -26],
    [42, -22],
    [44, -16],
    [44, -12],
  ],
  [
    [95, -4],
    [100, 4],
    [104, 2],
    [108, 0],
    [114, -2],
    [120, -2],
    [124, -6],
    [126, -8],
    [120, -10],
    [114, -6],
    [108, -6],
    [104, -4],
    [100, -2],
    [95, -4],
  ],
  [
    [130, -2],
    [136, -4],
    [142, -4],
    [146, -6],
    [146, -8],
    [142, -8],
    [136, -6],
    [132, -4],
    [130, -2],
  ],
  [
    [114, -22],
    [122, -20],
    [130, -16],
    [136, -12],
    [140, -18],
    [146, -20],
    [152, -24],
    [154, -28],
    [152, -36],
    [148, -38],
    [144, -38],
    [138, -36],
    [130, -34],
    [122, -34],
    [114, -30],
    [114, -22],
  ],
  [
    [168, -44],
    [170, -44],
    [172, -38],
    [174, -36],
    [172, -34],
    [170, -38],
    [168, -44],
  ],
  [
    [118, 10],
    [122, 14],
    [122, 18],
    [120, 18],
    [118, 14],
    [116, 10],
    [118, 10],
  ],
];

const SG = { lat: 1.35, lon: 103.82 };

// ── Projection ───────────────────────────────────────────────────────────────

function robinsonProj(lon, lat, W, H) {
  const absLat = Math.abs(lat);
  const idx = Math.min(Math.floor(absLat / 5), 17);
  const t = (absLat % 5) / 5;
  const xf = ROB_X[idx] + (ROB_X[idx + 1] - ROB_X[idx]) * t;
  const yf = ROB_Y[idx] + (ROB_Y[idx + 1] - ROB_Y[idx]) * t;
  const lonRad = (lon * Math.PI) / 180;
  const sign = lat < 0 ? -1 : 1;
  const robX = 0.8487 * xf * lonRad;
  const robY = 1.3523 * yf * sign;
  const robXMax = 0.8487 * Math.PI;
  const robYMax = 1.3523;
  const pad = 0.01;
  const scale = Math.min(
    (W / (2 * robXMax)) * (1 - 2 * pad),
    (H / (2 * robYMax)) * (1 - 2 * pad),
  );
  return { x: W / 2 + robX * scale, y: H / 2 - robY * scale };
}

// Perspective tilt: top of map recedes (horizon), bottom comes forward
function perspTilt(x, y, W, H) {
  const theta = (26 * Math.PI) / 180;
  const d = H * 1.75;
  const cx = W / 2,
    cy = H / 2;
  const px = x - cx,
    py = y - cy;
  const z3d = py * Math.sin(theta);
  const y3d = py * Math.cos(theta);
  const pScale = d / (d - z3d);
  return { x: cx + px * pScale, y: cy + y3d * pScale };
}

function project(lon, lat, W, H) {
  const r = robinsonProj(lon, lat, W, H);
  return perspTilt(r.x, r.y, W, H);
}

// ── Map dot builder ──────────────────────────────────────────────────────────

function pointInPolygon(point, polygon) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i][0],
      yi = polygon[i][1];
    const xj = polygon[j][0],
      yj = polygon[j][1];
    const intersect =
      yi > point[1] !== yj > point[1] &&
      point[0] < ((xj - xi) * (point[1] - yi)) / (yj - yi || 1e-6) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

function buildDots(W, H, density = 2.7) {
  const dots = [];
  for (let lat = -56; lat <= 78; lat += density) {
    for (let lon = -178; lon <= 178; lon += density) {
      if (!LANDS.some((poly) => pointInPolygon([lon, lat], poly))) continue;
      const pt = project(lon, lat, W, H);
      dots.push({ x: pt.x, y: pt.y, lat, lon });
    }
  }
  return dots;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function useElementSize(ref) {
  const [size, setSize] = useState({ width: 1200, height: 480 });
  useEffect(() => {
    if (!ref.current) return;
    const ro = new ResizeObserver(([e]) => {
      const { width, height } = e.contentRect;
      setSize({ width, height });
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, [ref]);
  return size;
}

// laneOffset: fractional lane index centred on 0 (e.g. -0.5, +0.5 for 2 routes)
function arcPath(a, b, laneOffset = 0) {
  const dist = Math.hypot(b.x - a.x, b.y - a.y);
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2 - dist * 0.3;
  // Perpendicular unit vector for lane separation
  const dx = b.x - a.x,
    dy = b.y - a.y;
  const len = Math.hypot(dx, dy) || 1;
  const px = -dy / len,
    py = dx / len;
  const spread = Math.min(dist * 0.055, 22); // scale with distance, capped
  return `M ${a.x} ${a.y} Q ${mx + px * laneOffset * spread} ${my + py * laneOffset * spread} ${b.x} ${b.y}`;
}

// ── Component ────────────────────────────────────────────────────────────────

// ── Decision Simulation ───────────────────────────────────────────────────

const GOALS = [
  { id: "cost", label: "Minimise Cost", icon: "💰" },
  { id: "risk", label: "Minimise Risk", icon: "🛡" },
  { id: "resilience", label: "Maximise Resilience", icon: "🔄" },
];

const AGENTS = [
  {
    id: "trade",
    name: "Trade Minister",
    icon: "📦",
    objective: "minimise cost and preserve trade flows",
  },
  {
    id: "foreign",
    name: "Foreign Minister",
    icon: "🤝",
    objective: "maintain diplomatic relations and soft power",
  },
  {
    id: "risk",
    name: "Risk Agent",
    icon: "🛡",
    objective: "minimise supply chain disruption and exposure",
  },
];

const DECISION_SYSTEM = (agentName, agentObjective, route, goal, newsContext) =>
  `You are Singapore's ${agentName}. Your primary objective is to ${agentObjective}.
A supply chain disruption has been detected: ${route.country} — ${route.sector} sector (${route.status}).
The user's optimisation goal is: ${goal}.${newsContext ? `\n\nSelected news signals for context:\n${newsContext}` : ""}
Return ONLY valid JSON with this structure:
{
  "strategy": "one-line strategy title under 50 chars",
  "rationale": "1 sentence explaining the core reasoning",
  "actions": [
    { "step": 1, "action": "specific action under 60 chars", "impact": "expected outcome under 40 chars" },
    { "step": 2, "action": "...", "impact": "..." },
    { "step": 3, "action": "...", "impact": "..." }
  ],
  "tradeoff": "one sentence on what is sacrificed with this strategy"
}`;

function getMockDecision(agentId, route, goal) {
  const mocks = {
    trade: {
      strategy: "Activate spot market procurement",
      rationale:
        "Immediate cost-competitive sourcing from alternative suppliers reduces fiscal exposure.",
      actions: [
        {
          step: 1,
          action: "Issue emergency tender on spot market",
          impact: "Source at 5–8% premium vs tariff",
        },
        {
          step: 2,
          action: "Negotiate volume discounts with AU/TH suppliers",
          impact: "Lock in 3-month stable pricing",
        },
        {
          step: 3,
          action: "Review and freeze non-essential import contracts",
          impact: "Free up S$120M procurement budget",
        },
      ],
      tradeoff:
        "Short-term cost savings may reduce leverage in future bilateral negotiations.",
      sources: [
        { name: "MTI Trade Advisory", age: "4h ago" },
        { name: "Bloomberg: Export Curbs", age: "1d ago" },
        { name: "WTO Tariff Database", age: "Live" },
      ],
    },
    foreign: {
      strategy: "Quiet diplomacy via ASEAN framework",
      rationale:
        "Back-channel engagement preserves the bilateral relationship while buying time for diversification.",
      actions: [
        {
          step: 1,
          action: "Request PM-level bilateral call within 48h",
          impact: "Signal seriousness without escalation",
        },
        {
          step: 2,
          action: "Invoke ASEAN mediation clause quietly",
          impact: "Neutral third-party buffer engaged",
        },
        {
          step: 3,
          action: "Offer joint infrastructure investment as carrot",
          impact: "Create mutual incentive to resolve",
        },
      ],
      tradeoff:
        "Diplomatic patience delays faster economic solutions and may signal weakness.",
      sources: [
        { name: "MFA Singapore Statement", age: "6h ago" },
        { name: "ASEAN Secretariat", age: "2d ago" },
        { name: "Reuters: Diplomacy", age: "3h ago" },
      ],
    },
    risk: {
      strategy: "Diversify and build strategic buffer",
      rationale:
        "Spreading supply across 3+ sources and increasing reserve depth eliminates single-point risk.",
      actions: [
        {
          step: 1,
          action: "Activate SFA emergency diversification protocol",
          impact: "Reduce single-source dependency to <30%",
        },
        {
          step: 2,
          action: "Double strategic reserve to 90-day supply",
          impact: "Eliminate short-term supply shock",
        },
        {
          step: 3,
          action: "Fast-track agreements with 2 new partner nations",
          impact: "Long-term resilience score +40%",
        },
      ],
      tradeoff:
        "Diversification increases short-term procurement costs by an estimated 12–18%.",
      sources: [
        { name: "SFA Emergency Protocol", age: "Internal" },
        { name: "FAO Food Price Index", age: "1h ago" },
        { name: "Straits Times: Supply Chain", age: "5h ago" },
      ],
    },
  };
  return mocks[agentId] || mocks.trade;
}

async function callDecisionAgent(
  agentId,
  agentName,
  agentObjective,
  route,
  goal,
  newsItems = [],
) {
  const newsContext =
    newsItems.length > 0
      ? newsItems
          .map((n, i) => `${i + 1}. ${n.headline}: ${n.snippet}`)
          .join("\n")
      : "";
  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;
  if (!apiKey) {
    await new Promise((r) => setTimeout(r, 600 + Math.random() * 800));
    return getMockDecision(agentId, route, goal);
  }
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-calls": "true",
    },
    body: JSON.stringify({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 600,
      system: DECISION_SYSTEM(
        agentName,
        agentObjective,
        route,
        goal,
        newsContext,
      ),
      messages: [
        {
          role: "user",
          content: `Optimisation goal: ${goal}. Disruption: ${route.country} ${route.sector} (${route.status}). Generate your strategy.`,
        },
      ],
    }),
  });
  if (!res.ok) return getMockDecision(agentId, route, goal);
  const data = await res.json();
  const text = data.content[0].text
    .trim()
    .replace(/^```json\s*/, "")
    .replace(/\s*```$/, "");
  try {
    return JSON.parse(text);
  } catch {
    return getMockDecision(agentId, route, goal);
  }
}

// ── Synthesis ──────────────────────────────────────────────────────────────

function getMockSynthesis(route) {
  const isDisrupted = route.status === "disrupted";
  const isMild = route.status === "mild";
  if (isDisrupted)
    return {
      final_position: "conditional",
      viability_score: 0.62,
      pros: [
        "Alternative suppliers identified in Australia and Thailand",
        "ASEAN diplomatic channel available for back-channel outreach",
        "Strategic reserves provide 45-day supply buffer",
      ],
      cons: [
        "34% tariff escalation increases procurement costs significantly",
        "Diversification takes 60–90 days to fully operationalise",
        "Diplomatic resolution timeline remains uncertain",
      ],
      rationale:
        "Ministers reached conditional consensus: activate emergency procurement while pursuing quiet diplomacy. The tariff impact is containable given reserve depth, but a diversification programme must begin immediately.",
      recommended_action:
        "Dual-track: diplomatic outreach + emergency procurement",
      urgency: "high",
    };
  if (isMild)
    return {
      final_position: "monitor",
      viability_score: 0.79,
      pros: [
        "Supply continuity maintained at current levels",
        "Early signals allow proactive pre-positioning",
        "No immediate fiscal impact requires emergency spend",
      ],
      cons: [
        "Mild stress could escalate rapidly if unaddressed",
        "Premature action risks diplomatic capital unnecessarily",
      ],
      rationale:
        "Ministers advise watchful monitoring with pre-positioned contingency. Current disruption level does not warrant emergency intervention, but 72-hour trigger conditions should be defined now.",
      recommended_action: "Monitor with 72h review cadence + contingency brief",
      urgency: "medium",
    };
  return {
    final_position: "proceed",
    viability_score: 0.91,
    pros: [
      "Connection operating within normal parameters",
      "No geopolitical signals of concern detected",
      "Trade flows at expected seasonal volumes",
    ],
    cons: ["Routine diversification hygiene always advisable"],
    rationale:
      "No immediate action required. Ministers unanimously recommend maintaining current approach with standard monitoring protocols in place.",
    recommended_action: "Maintain standard monitoring — no action required",
    urgency: "low",
  };
}

const SYNTHESIS_SYSTEM = (
  route,
  goal,
  newsContext,
  tradeStrategy,
  foreignStrategy,
  riskStrategy,
) =>
  `You are a neutral policy synthesiser for Singapore's National Security Council.
Three advisors have presented strategies for a ${route.sector} supply chain disruption involving ${route.country} (status: ${route.status}).
Optimisation goal: ${goal}.${newsContext ? `\n\nRelevant news signals:\n${newsContext}` : ""}

Trade Minister strategy: ${tradeStrategy}
Foreign Minister strategy: ${foreignStrategy}
Risk Agent strategy: ${riskStrategy}

Synthesise their positions into a final consensus report. Return ONLY valid JSON:
{
  "final_position": "proceed|conditional|monitor|hold|abort",
  "viability_score": 0.0-1.0,
  "pros": ["up to 3 concise pros, each under 60 chars"],
  "cons": ["up to 3 concise cons, each under 60 chars"],
  "rationale": "1-2 sentence consensus rationale",
  "recommended_action": "one specific action under 65 chars",
  "urgency": "low|medium|high"
}`;

async function synthesizeDebate(route, goal, newsItems, ministerResults) {
  const newsContext =
    newsItems.length > 0
      ? newsItems
          .map((n, i) => `${i + 1}. ${n.headline}: ${n.snippet}`)
          .join("\n")
      : "";
  const fmt = (r) => (r ? `${r.strategy} — ${r.rationale}` : "no response");
  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;
  if (!apiKey) {
    await new Promise((r) => setTimeout(r, 900 + Math.random() * 600));
    return getMockSynthesis(route);
  }
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-calls": "true",
    },
    body: JSON.stringify({
      model: "claude-haiku-4-5-20251001",
      max_tokens: 500,
      system: SYNTHESIS_SYSTEM(
        route,
        goal,
        newsContext,
        fmt(ministerResults.trade),
        fmt(ministerResults.foreign),
        fmt(ministerResults.risk),
      ),
      messages: [
        {
          role: "user",
          content:
            "Synthesise the three minister positions into a final consensus report.",
        },
      ],
    }),
  });
  if (!res.ok) return getMockSynthesis(route);
  const data = await res.json();
  const text = data.content[0].text
    .trim()
    .replace(/^```json\s*/, "")
    .replace(/\s*```$/, "");
  try {
    return JSON.parse(text);
  } catch {
    return getMockSynthesis(route);
  }
}

// ── DecisionSimPanel ───────────────────────────────────────────────────────

const POSITION_META = {
  proceed: {
    label: "Proceed",
    color: "#18A87A",
    bg: "rgba(24,168,122,0.12)",
    icon: "✓",
  },
  conditional: {
    label: "Conditional",
    color: "#F0A020",
    bg: "rgba(240,160,32,0.12)",
    icon: "⚡",
  },
  monitor: {
    label: "Monitor",
    color: "#3090E8",
    bg: "rgba(48,144,232,0.12)",
    icon: "◉",
  },
  hold: {
    label: "Hold",
    color: "#E85550",
    bg: "rgba(232,85,80,0.1)",
    icon: "⏸",
  },
  abort: {
    label: "Abort",
    color: "#E85550",
    bg: "rgba(232,85,80,0.15)",
    icon: "✕",
  },
};

function DecisionSimPanel({ route, sectorColor, selectedNewsItems = [] }) {
  const [goals, setGoals] = useState([]);
  const [phase, setPhase] = useState("idle"); // idle | debating | synthesizing | done
  const [loadingAgents, setLoadingAgents] = useState({});
  const [results, setResults] = useState(null);
  const [synthesis, setSynthesis] = useState(null);
  const [dotCount, setDotCount] = useState(0);

  // Animated dots for loading phases
  useEffect(() => {
    if (phase === "idle" || phase === "done") return;
    const t = setInterval(() => setDotCount((d) => (d + 1) % 4), 380);
    return () => clearInterval(t);
  }, [phase]);

  const runAgents = async (selectedGoal) => {
    const goalText = selectedGoal.join(", ");
    setPhase("debating");
    setResults(null);
    setSynthesis(null);
    setLoadingAgents({ trade: true, foreign: true, risk: true });

    const agentResults = {};
    await Promise.all(
      AGENTS.map(async (agent) => {
        const result = await callDecisionAgent(
          agent.id,
          agent.name,
          agent.objective,
          route,
          goalText,
          selectedNewsItems,
        );
        agentResults[agent.id] = result;
        setLoadingAgents((prev) => ({ ...prev, [agent.id]: false }));
        setResults((prev) => ({ ...prev, [agent.id]: result }));
      }),
    );

    setPhase("synthesizing");
    const synth = await synthesizeDebate(
      route,
      goalText,
      selectedNewsItems,
      agentResults,
    );
    setSynthesis(synth);
    setPhase("done");

    // Persist to debate history
    try {
      const entry = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        route: {
          country: route.country,
          code: route.code,
          sector: route.sector,
          status: route.status,
          note: route.note,
        },
        goal: goalText,
        selectedNewsCount: selectedNewsItems.length,
        synthesis: synth,
      };
      const prev = JSON.parse(localStorage.getItem("alore_debates") || "[]");
      localStorage.setItem(
        "alore_debates",
        JSON.stringify([entry, ...prev].slice(0, 50)),
      );
    } catch {
      /* storage unavailable */
    }
  };

  const dots = "·".repeat(dotCount);

  return (
    <div style={{ flexShrink: 0 }}>
      {/* ── Goal selector (idle phase only) ── */}
      {phase === "idle" && (
        <div style={{ padding: "18px 18px 16px" }}>
          <div
            style={{
              fontSize: 9,
              fontWeight: 800,
              color: "rgba(45,58,82,0.3)",
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              marginBottom: 6,
            }}
          >
            Decision Simulation
          </div>
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: "#2D3A52",
              letterSpacing: "-0.01em",
              marginBottom: 5,
            }}
          >
            What do you want to optimise?
          </div>
          <div
            style={{
              fontSize: 11.5,
              color: "rgba(45,58,82,0.48)",
              marginBottom: 16,
              lineHeight: 1.5,
            }}
          >
            Select one or more goals. Three AI ministers will debate and balance
            these priorities into a consensus strategy
            {selectedNewsItems.length > 0 && (
              <span style={{ color: sectorColor, fontWeight: 600 }}>
                {" "}
                {selectedNewsItems.length} signal
                {selectedNewsItems.length !== 1 ? "s" : ""} included.
              </span>
            )}
          </div>
          <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
            {GOALS.map((g) => {
              const isActive = goals.includes(g.id);
              return (
                <button
                  key={g.id}
                  onClick={() =>
                    setGoals((prev) =>
                      prev.includes(g.id)
                        ? prev.filter((id) => id !== g.id)
                        : [...prev, g.id],
                    )
                  }
                  style={{
                    flex: 1,
                    padding: "12px 6px",
                    background: isActive
                      ? sectorColor + "18"
                      : "rgba(45,58,82,0.04)",
                    border: `1.5px solid ${isActive ? sectorColor : "rgba(45,58,82,0.1)"}`,
                    borderRadius: 10,
                    fontSize: 11,
                    fontWeight: 700,
                    color: isActive ? sectorColor : "rgba(45,58,82,0.52)",
                    cursor: "pointer",
                    fontFamily: "'Inter',sans-serif",
                    transition: "all 0.16s",
                    lineHeight: 1.3,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <span style={{ fontSize: 20 }}>{g.icon}</span>
                  <span>{g.label}</span>
                </button>
              );
            })}
          </div>
          {goals.length > 0 && (
            <button
              onClick={() => runAgents(goals)}
              style={{
                width: "100%",
                padding: "13px",
                background: sectorColor,
                border: "none",
                borderRadius: 10,
                fontSize: 13,
                fontWeight: 700,
                color: "#fff",
                cursor: "pointer",
                fontFamily: "'Inter',sans-serif",
                letterSpacing: "0.01em",
                transition: "opacity 0.15s",
                animation: "panelIn 0.22s ease both",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.86")}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
            >
              Start Resolve →
            </button>
          )}
        </div>
      )}

      {/* ── Debating / Synthesising animation ── */}
      {(phase === "debating" || phase === "synthesizing") && (
        <div style={{ padding: "22px 18px 24px" }}>
          {/* Animated orb + label */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              marginBottom: 22,
            }}
          >
            <div
              style={{
                position: "relative",
                width: 40,
                height: 40,
                flexShrink: 0,
              }}
            >
              {/* Ripple rings */}
              <div
                style={{
                  position: "absolute",
                  inset: -8,
                  borderRadius: "50%",
                  border: `1.5px solid ${sectorColor}33`,
                  animation: "pulse 1.6s ease-in-out infinite",
                }}
              />
              <div
                style={{
                  position: "absolute",
                  inset: -2,
                  borderRadius: "50%",
                  border: `1.5px solid ${sectorColor}55`,
                  animation: "pulse 1.6s ease-in-out 0.3s infinite",
                }}
              />
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: "50%",
                  background: `linear-gradient(135deg, ${sectorColor}22 0%, ${sectorColor}44 100%)`,
                  border: `1.5px solid ${sectorColor}66`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <span style={{ fontSize: 18 }}>
                  {phase === "synthesizing" ? "⚡" : "💬"}
                </span>
              </div>
            </div>
            <div>
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 800,
                  color: "#2D3A52",
                  letterSpacing: "-0.02em",
                  lineHeight: 1.2,
                }}
              >
                {phase === "synthesizing" ? "Synthesising" : "Debating"}
                <span
                  style={{
                    color: sectorColor,
                    minWidth: 24,
                    display: "inline-block",
                  }}
                >
                  {dots}
                </span>
              </div>
              <div
                style={{
                  fontSize: 11.5,
                  color: "rgba(45,58,82,0.45)",
                  marginTop: 3,
                }}
              >
                {phase === "synthesizing"
                  ? "Consolidating minister positions into a consensus report"
                  : `3 ministers analysing ${selectedNewsItems.length > 0 ? `${selectedNewsItems.length} signal${selectedNewsItems.length !== 1 ? "s" : ""}` : "the situation"}`}
              </div>
            </div>
          </div>

          {/* Minister status rows */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {AGENTS.map((agent) => {
              const isDone = !loadingAgents[agent.id] && results?.[agent.id];
              const isActive = loadingAgents[agent.id];
              return (
                <div
                  key={agent.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "10px 14px",
                    background: isDone
                      ? "rgba(24,168,122,0.05)"
                      : isActive
                        ? sectorColor + "07"
                        : "rgba(45,58,82,0.03)",
                    border: `1px solid ${isDone ? "rgba(24,168,122,0.18)" : isActive ? sectorColor + "22" : "rgba(45,58,82,0.07)"}`,
                    borderRadius: 10,
                    transition: "all 0.4s",
                  }}
                >
                  <span style={{ fontSize: 18, flexShrink: 0 }}>
                    {agent.icon}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: 700,
                        color: isDone ? "#18A87A" : "rgba(45,58,82,0.7)",
                        transition: "color 0.3s",
                      }}
                    >
                      {agent.name}
                    </div>
                    <div
                      style={{
                        fontSize: 10,
                        color: "rgba(45,58,82,0.38)",
                        marginTop: 1,
                      }}
                    >
                      {isDone
                        ? results[agent.id].strategy
                        : isActive
                          ? `Analysing${dots}`
                          : "Waiting"}
                    </div>
                  </div>
                  {isDone && (
                    <div
                      style={{
                        width: 22,
                        height: 22,
                        borderRadius: "50%",
                        background: "rgba(24,168,122,0.15)",
                        border: "1.5px solid rgba(24,168,122,0.4)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        animation: "panelIn 0.25s ease both",
                      }}
                    >
                      <span
                        style={{
                          fontSize: 11,
                          color: "#18A87A",
                          fontWeight: 800,
                        }}
                      >
                        ✓
                      </span>
                    </div>
                  )}
                  {isActive && (
                    <div
                      style={{
                        width: 16,
                        height: 16,
                        border: `2px solid ${sectorColor}33`,
                        borderTopColor: sectorColor,
                        borderRadius: "50%",
                        animation: "debateSpin 0.75s linear infinite",
                        flexShrink: 0,
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {phase === "synthesizing" && (
            <div
              style={{
                marginTop: 14,
                padding: "10px 14px",
                background: sectorColor + "0a",
                border: `1px solid ${sectorColor}22`,
                borderRadius: 10,
                display: "flex",
                alignItems: "center",
                gap: 10,
                animation: "panelIn 0.3s ease both",
              }}
            >
              <div
                style={{
                  width: 14,
                  height: 14,
                  border: `2px solid ${sectorColor}33`,
                  borderTopColor: sectorColor,
                  borderRadius: "50%",
                  animation: "debateSpin 0.75s linear infinite",
                  flexShrink: 0,
                }}
              />
              <span
                style={{ fontSize: 11, color: sectorColor, fontWeight: 600 }}
              >
                Building consensus report{dots}
              </span>
            </div>
          )}
        </div>
      )}

      {/* ── Synthesis report (done phase) ── */}
      {phase === "done" &&
        synthesis &&
        (() => {
          const pos =
            POSITION_META[synthesis.final_position] ||
            POSITION_META.conditional;
          const score = Math.max(
            0,
            Math.min(1, synthesis.viability_score || 0),
          );
          const urgencyColor =
            { low: "#18A87A", medium: "#F0A020", high: "#E85550" }[
              synthesis.urgency
            ] || sectorColor;
          return (
            <div
              style={{
                padding: "20px 18px 22px",
                animation: "panelIn 0.4s ease both",
              }}
            >
              {/* Report header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 16,
                }}
              >
                <div
                  style={{
                    fontSize: 9,
                    fontWeight: 800,
                    color: "rgba(45,58,82,0.3)",
                    textTransform: "uppercase",
                    letterSpacing: "0.12em",
                  }}
                >
                  Debate Summary
                </div>
                <div
                  style={{
                    marginLeft: "auto",
                    fontSize: 9,
                    fontWeight: 700,
                    color: urgencyColor,
                    background: urgencyColor + "18",
                    border: `1px solid ${urgencyColor}33`,
                    borderRadius: 20,
                    padding: "2px 9px",
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                  }}
                >
                  {synthesis.urgency} urgency
                </div>
              </div>

              {/* Verdict badge */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  marginBottom: 16,
                  padding: "14px 16px",
                  background: pos.bg,
                  border: `1.5px solid ${pos.color}44`,
                  borderRadius: 12,
                }}
              >
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: "50%",
                    background: pos.color + "22",
                    border: `1.5px solid ${pos.color}55`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <span
                    style={{ fontSize: 16, fontWeight: 800, color: pos.color }}
                  >
                    {pos.icon}
                  </span>
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 9,
                      fontWeight: 800,
                      color: pos.color,
                      textTransform: "uppercase",
                      letterSpacing: "0.12em",
                      marginBottom: 3,
                    }}
                  >
                    Final Position
                  </div>
                  <div
                    style={{
                      fontSize: 20,
                      fontWeight: 800,
                      color: pos.color,
                      letterSpacing: "-0.02em",
                      lineHeight: 1,
                    }}
                  >
                    {pos.label}
                  </div>
                </div>
              </div>

              {/* Pros / Cons */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 10,
                  marginBottom: 14,
                }}
              >
                {/* Pros */}
                <div
                  style={{
                    padding: "12px 13px",
                    background: "rgba(24,168,122,0.06)",
                    border: "1px solid rgba(24,168,122,0.15)",
                    borderRadius: 10,
                  }}
                >
                  <div
                    style={{
                      fontSize: 9,
                      fontWeight: 800,
                      color: "#18A87A",
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      marginBottom: 8,
                    }}
                  >
                    Pros
                  </div>
                  {synthesis.pros?.map((p, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        gap: 7,
                        marginBottom: 6,
                        alignItems: "flex-start",
                      }}
                    >
                      <span
                        style={{
                          fontSize: 10,
                          color: "#18A87A",
                          flexShrink: 0,
                          marginTop: 1,
                          fontWeight: 700,
                        }}
                      >
                        ✓
                      </span>
                      <span
                        style={{
                          fontSize: 10.5,
                          color: "rgba(45,58,82,0.75)",
                          lineHeight: 1.45,
                        }}
                      >
                        {p}
                      </span>
                    </div>
                  ))}
                </div>
                {/* Cons */}
                <div
                  style={{
                    padding: "12px 13px",
                    background: "rgba(232,85,80,0.05)",
                    border: "1px solid rgba(232,85,80,0.15)",
                    borderRadius: 10,
                  }}
                >
                  <div
                    style={{
                      fontSize: 9,
                      fontWeight: 800,
                      color: "#E85550",
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      marginBottom: 8,
                    }}
                  >
                    Cons
                  </div>
                  {synthesis.cons?.map((c, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        gap: 7,
                        marginBottom: 6,
                        alignItems: "flex-start",
                      }}
                    >
                      <span
                        style={{
                          fontSize: 10,
                          color: "#E85550",
                          flexShrink: 0,
                          marginTop: 1,
                          fontWeight: 700,
                        }}
                      >
                        ✕
                      </span>
                      <span
                        style={{
                          fontSize: 10.5,
                          color: "rgba(45,58,82,0.75)",
                          lineHeight: 1.45,
                        }}
                      >
                        {c}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Rationale */}
              <div
                style={{
                  padding: "12px 14px",
                  background: "rgba(45,58,82,0.04)",
                  border: "1px solid rgba(45,58,82,0.08)",
                  borderRadius: 10,
                  marginBottom: 12,
                }}
              >
                <div
                  style={{
                    fontSize: 9,
                    fontWeight: 800,
                    color: "rgba(45,58,82,0.3)",
                    textTransform: "uppercase",
                    letterSpacing: "0.1em",
                    marginBottom: 6,
                  }}
                >
                  Consensus Rationale
                </div>
                <div
                  style={{
                    fontSize: 12.5,
                    color: "rgba(45,58,82,0.78)",
                    lineHeight: 1.6,
                    fontStyle: "italic",
                  }}
                >
                  "{synthesis.rationale}"
                </div>
              </div>

              {/* Recommended action */}
              {synthesis.recommended_action && (
                <div
                  style={{
                    padding: "12px 14px",
                    background: pos.color + "10",
                    border: `1.5px solid ${pos.color}33`,
                    borderRadius: 10,
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <span style={{ fontSize: 16, flexShrink: 0 }}>→</span>
                  <div>
                    <div
                      style={{
                        fontSize: 9,
                        fontWeight: 800,
                        color: pos.color,
                        textTransform: "uppercase",
                        letterSpacing: "0.1em",
                        marginBottom: 3,
                      }}
                    >
                      Recommended Action
                    </div>
                    <div
                      style={{
                        fontSize: 12.5,
                        fontWeight: 700,
                        color: "rgba(45,58,82,0.85)",
                        lineHeight: 1.4,
                      }}
                    >
                      {synthesis.recommended_action}
                    </div>
                  </div>
                </div>
              )}

              {/* Footer */}
              <div
                style={{
                  marginTop: 14,
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <div style={{ display: "flex", gap: 5 }}>
                  {AGENTS.map((a) => (
                    <span key={a.id} style={{ fontSize: 14 }}>
                      {a.icon}
                    </span>
                  ))}
                </div>
                <span style={{ fontSize: 10, color: "rgba(45,58,82,0.32)" }}>
                  3 agents consulted · {selectedNewsItems.length} signal
                  {selectedNewsItems.length !== 1 ? "s" : ""} analysed
                </span>
                <button
                  onClick={() => {
                    setPhase("idle");
                    setGoals([]);
                    setSynthesis(null);
                    setResults(null);
                  }}
                  style={{
                    marginLeft: "auto",
                    fontSize: 10,
                    fontWeight: 600,
                    color: "rgba(45,58,82,0.45)",
                    background: "transparent",
                    border: "1px solid rgba(45,58,82,0.15)",
                    borderRadius: 7,
                    padding: "4px 10px",
                    cursor: "pointer",
                    fontFamily: "'Inter',sans-serif",
                  }}
                >
                  Restart
                </button>
              </div>
            </div>
          );
        })()}

      <style>{`
        @keyframes debateSpin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default function SGDashboard({ onNavigate = () => {} }) {
  const mapRef = useRef(null);
  const debateRef = useRef(null);
  const { width, height } = useElementSize(mapRef);
  // selectedRoute = { code, sector } | null  — one specific sector×country arc
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [scrapeFreq, setScrapeFreq] = useState("6h");
  const [scrapeMenuOpen, setScrapeMenuOpen] = useState(false);
  const [statusTab, setStatusTab] = useState(null);
  const [alertDismissed, setAlertDismissed] = useState(false);
  const [active, setActive] = useState(new Set(Object.keys(SECTORS)));
  const [selectedNews, setSelectedNews] = useState(new Set());
  const [NEWS, setNEWS] = useState(NEWS_FALLBACK);

  useEffect(() => {
    fetch("/api/v1/news-curator/singapore")
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then(({ data }) => {
        const mapped = [...data.internal, ...data.external].map((a) => ({
          tag: inferNewsTag(a.title, a.hook),
          headline: a.title,
          snippet: a.hook,
          url: a.url,
        }));
        if (mapped.length > 0) setNEWS(mapped);
      })
      .catch(() => {/* keep fallback */});
  }, []);

  const toggleSector = (key) => {
    setActive((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next.size === 0 ? prev : next;
    });
  };

  // When a route is selected, pre-select all related news + scroll to debate section
  useEffect(() => {
    if (selectedRoute) {
      const news = NEWS.filter((n) => n.tag === selectedRoute.sector);
      setSelectedNews(new Set(news.map((_, i) => i)));
      setTimeout(
        () =>
          debateRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          }),
        350,
      );
    }
  }, [selectedRoute?.code, selectedRoute?.sector]);

  const W = Math.max(600, width);
  const H = Math.max(320, height);

  const dots = useMemo(() => buildDots(W, H, 2.7), [W, H]);

  const grouped = useMemo(() => {
    const b = {};
    ROUTES.forEach((r) => {
      (b[r.code] = b[r.code] || []).push(r);
    });
    return b;
  }, []);

  const nodes = useMemo(() => {
    const map = {};
    Object.keys(grouped).forEach((code) => {
      const base = grouped[code][0];
      map[code] = project(base.lon, base.lat, W, H);
    });
    map.SG = project(SG.lon, SG.lat, W, H);
    return map;
  }, [grouped, W, H]);

  // Derived from selectedRoute
  const selectedCode = selectedRoute?.code ?? null;
  const selectedRoutes = selectedRoute
    ? (grouped[selectedRoute.code] || []).filter(
        (r) => r.sector === selectedRoute.sector,
      )
    : [];
  const relatedNews = selectedRoute
    ? NEWS.filter((n) => n.tag === selectedRoute.sector)
    : [];

  const codes = Object.keys(grouped);
  const sgNode = nodes.SG;

  // Zoom-to-country transform
  const selNode = selectedCode ? nodes[selectedCode] : null;
  const zoomScale = selNode ? 1.38 : 1;
  const zoomTx = selNode ? W / 2 - selNode.x * zoomScale : 0;
  const zoomTy = selNode ? H * 0.46 - selNode.y * zoomScale : 0;
  // Position info overlay left or right based on country's original map position
  void (selNode ? selNode.x > W * 0.45 : false); // kept for potential re-use
  const primaryHighlightColor = selectedRoute
    ? SECTORS[selectedRoute.sector].color
    : "#C9B89A";

  // Status metrics
  const allActiveRoutes = ROUTES.filter((r) => active.has(r.sector));
  const _stableCount = allActiveRoutes.filter(
    (r) => r.status === "stable",
  ).length;
  void _stableCount;
  const mildCount = allActiveRoutes.filter((r) => r.status === "mild").length;
  const disruptedCount = allActiveRoutes.filter(
    (r) => r.status === "disrupted",
  ).length;
  const totalCountries = new Set(ROUTES.map((r) => r.code)).size;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100%",
        background: "#F5F2EE",
        fontFamily: "'Inter',sans-serif",
        overflowY: "auto",
        overflowX: "hidden",
      }}
    >
      {/* ── MAP ─────────────────────────────────────────────────────── */}
      <div
        ref={mapRef}
        style={{
          height: "68vh",
          flexShrink: 0,
          position: "relative",
          margin: "8px 0 4px",
          border: "none",
          borderTop: "1px solid rgba(45,58,82,0.15)",
          borderBottom: "1px solid rgba(45,58,82,0.1)",
          overflow: "hidden",
          background: "#E8E4DE",
        }}
      >
        {/* Header — Alore logo */}
        <div
          style={{
            position: "absolute",
            top: 12,
            left: 14,
            zIndex: 10,
            display: "flex",
            alignItems: "center",
            gap: 7,
          }}
        >
          <span
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: "#2D3A52",
              letterSpacing: "-0.01em",
            }}
          >
            Alore.
          </span>
        </div>

        {/* ── Overall status — center top ── */}
        {!selectedRoute &&
          (() => {
            const isDisrupted = disruptedCount > 0;
            const overallColor = isDisrupted
              ? "#E85550"
              : mildCount > 0
                ? "#F0A020"
                : "#18A87A";
            const overallLabel = isDisrupted
              ? "Network Disruption Detected"
              : mildCount > 0
                ? "Mild Disruption"
                : "All Systems Stable";
            return (
              <div
                onClick={() => isDisrupted && setAlertDismissed(false)}
                style={{
                  position: "absolute",
                  top: 14,
                  left: "50%",
                  transform: "translateX(-50%)",
                  zIndex: 10,
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  background: isDisrupted
                    ? "rgba(232,85,80,0.12)"
                    : "rgba(245,242,238,0.92)",
                  backdropFilter: "blur(10px)",
                  border: `1.5px solid ${overallColor}${isDisrupted ? "66" : "33"}`,
                  borderRadius: isDisrupted ? 10 : 20,
                  padding: isDisrupted
                    ? "7px 16px 7px 10px"
                    : "5px 13px 5px 8px",
                  boxShadow: isDisrupted
                    ? `0 4px 20px ${overallColor}30`
                    : `0 2px 12px ${overallColor}18`,
                  cursor: isDisrupted ? "pointer" : "default",
                }}
              >
                <div
                  style={{
                    position: "relative",
                    width: isDisrupted ? 10 : 8,
                    height: isDisrupted ? 10 : 8,
                    flexShrink: 0,
                  }}
                >
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      borderRadius: "50%",
                      background: overallColor,
                      opacity: 0.3,
                      animation: "pulse 1.5s ease-in-out infinite",
                      transform: "scale(2.2)",
                    }}
                  />
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      borderRadius: "50%",
                      background: overallColor,
                    }}
                  />
                </div>
                <span
                  style={{
                    fontSize: isDisrupted ? 12 : 10,
                    fontWeight: 800,
                    color: overallColor,
                    letterSpacing: isDisrupted ? "-0.01em" : "0.04em",
                  }}
                >
                  {overallLabel}
                </span>
                {isDisrupted && (
                  <span
                    style={{
                      fontSize: 9,
                      fontWeight: 600,
                      color: "rgba(232,85,80,0.6)",
                      background: "rgba(232,85,80,0.1)",
                      borderRadius: 6,
                      padding: "1px 6px",
                    }}
                  >
                    {disruptedCount} active · tap to review
                  </span>
                )}
                {!isDisrupted && mildCount > 0 && (
                  <span
                    style={{ fontSize: 9.5, color: "#F0A020", fontWeight: 600 }}
                  >
                    {mildCount} mild
                  </span>
                )}
              </div>
            );
          })()}

        {/* Sector toggles — right side panel */}
        {!selectedRoute && (
          <div
            style={{
              position: "absolute",
              top: "50%",
              right: 14,
              transform: "translateY(-50%)",
              zIndex: 10,
              display: "flex",
              flexDirection: "column",
              gap: 5,
              background: "rgba(245,242,238,0.96)",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(45,58,82,0.12)",
              borderRadius: 10,
              padding: "10px 8px",
            }}
          >
            {Object.entries(SECTORS).map(([key, { color, label }]) => {
              const on = active.has(key);
              return (
                <button
                  key={key}
                  onClick={() => toggleSector(key)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    padding: "6px 10px",
                    border: `1px solid ${on ? color + "50" : "rgba(45,58,82,0.1)"}`,
                    borderRadius: 7,
                    background: on ? color + "16" : "transparent",
                    cursor: "pointer",
                    transition: "all 0.18s",
                    whiteSpace: "nowrap",
                    fontFamily: "'Inter',sans-serif",
                  }}
                >
                  <div
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: on ? color : "rgba(45,58,82,0.2)",
                      boxShadow: on ? `0 0 7px ${color}` : "none",
                      transition: "all 0.18s",
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      color: on ? "#2D3A52" : "rgba(45,58,82,0.4)",
                      letterSpacing: "0.03em",
                      transition: "color 0.18s",
                    }}
                  >
                    {label}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* Back / hint overlay */}
        {selectedRoute ? (
          <button
            onClick={() => setSelectedRoute(null)}
            style={{
              position: "absolute",
              top: 12,
              right: 14,
              zIndex: 10,
              background: "rgba(245,242,238,0.96)",
              backdropFilter: "blur(8px)",
              border: "1px solid rgba(45,58,82,0.18)",
              borderRadius: 8,
              padding: "6px 13px",
              cursor: "pointer",
              fontSize: 11,
              fontWeight: 600,
              color: "rgba(45,58,82,0.7)",
              letterSpacing: "0.02em",
              fontFamily: "'Inter',sans-serif",
            }}
          >
            ← Overview
          </button>
        ) : (
          /* Logged-in user chip */
          <div
            style={{
              position: "absolute",
              top: 12,
              right: 14,
              zIndex: 10,
              display: "flex",
              alignItems: "center",
              gap: 7,
              background: "rgba(245,242,238,0.96)",
              backdropFilter: "blur(8px)",
              border: "1px solid rgba(45,58,82,0.15)",
              borderRadius: 20,
              padding: "4px 10px 4px 4px",
            }}
          >
            {/* Avatar circle */}
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: "50%",
                background: "#2D3A52",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 10,
                fontWeight: 800,
                color: "#F5F2EE",
                letterSpacing: "0.02em",
                flexShrink: 0,
              }}
            >
              RJ
            </div>
            <span
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "rgba(45,58,82,0.75)",
                fontFamily: "'Inter',sans-serif",
              }}
            >
              RyanJustyn
            </span>
          </div>
        )}

        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${W} ${H}`}
          style={{ display: "block" }}
        >
          <defs>
            <radialGradient id="bgGrad" cx="50%" cy="35%" r="70%">
              <stop offset="0%" stopColor="#8FB8D8" />
              <stop offset="45%" stopColor="#A8C8E0" />
              <stop offset="100%" stopColor="#C8DFF0" />
            </radialGradient>
            <radialGradient id="bgVignette" cx="50%" cy="50%" r="75%">
              <stop offset="55%" stopColor="rgba(0,0,0,0)" />
              <stop offset="100%" stopColor="rgba(45,58,82,0.12)" />
            </radialGradient>
            <linearGradient id="horizonFade" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(201,184,154,0.18)" />
              <stop offset="30%" stopColor="rgba(0,0,0,0)" />
            </linearGradient>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="7" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="routeGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Ocean — outside zoom group so it always fills frame */}
          <rect width={W} height={H} fill="url(#bgGrad)" />
          <rect width={W} height={H} fill="url(#bgVignette)" />
          <rect width={W} height={H} fill="url(#horizonFade)" />

          {/* ── Zoom group: all geo content scales towards selected country ── */}
          <g
            style={{
              transform: `translate(${zoomTx}px, ${zoomTy}px) scale(${zoomScale})`,
              transformOrigin: "0px 0px",
              transition: "transform 0.75s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            {/* Land dots */}
            {dots.map((d, i) => {
              let fill = "#3D5070";
              let opacity = 0.68;
              if (selNode) {
                const base = grouped[selectedCode][0];
                const dist = Math.hypot(d.lat - base.lat, d.lon - base.lon);
                const radius = COUNTRY_DOT_RADIUS[selectedCode] || 15;
                if (dist < radius) {
                  fill = primaryHighlightColor;
                  opacity = 0.9;
                } else {
                  opacity = 0.35;
                }
              }
              return (
                <circle
                  key={i}
                  cx={d.x}
                  cy={d.y}
                  r={1.9}
                  fill={fill}
                  opacity={opacity}
                />
              );
            })}

            {/* Route arcs — glow + crisp + hit area */}
            {codes.map((code) => {
              if (!nodes[code] || !sgNode) return null;
              const activeRoutes = grouped[code].filter((r) =>
                active.has(r.sector),
              );
              const total = activeRoutes.length;
              return activeRoutes.map((route, idx) => {
                const isSel =
                  selectedRoute &&
                  code === selectedRoute.code &&
                  route.sector === selectedRoute.sector;
                const isDim = selectedRoute && !isSel;
                const laneOffset = total === 1 ? 0 : idx - (total - 1) / 2;
                const d = arcPath(nodes[code], sgNode, laneOffset);
                return (
                  <g key={`arc-${code}-${route.sector}`}>
                    {/* Glow */}
                    {!isDim && (
                      <path
                        d={d}
                        fill="none"
                        stroke={SECTORS[route.sector].color}
                        strokeWidth={isSel ? 12 : 6}
                        strokeOpacity={isSel ? 0.22 : 0.1}
                        strokeLinecap="round"
                      />
                    )}
                    {/* Crisp line */}
                    <path
                      d={d}
                      fill="none"
                      stroke={SECTORS[route.sector].color}
                      strokeWidth={isSel ? 3.2 : 1.8}
                      strokeOpacity={isDim ? 0.07 : isSel ? 1 : 0.52}
                      strokeLinecap="round"
                      strokeDasharray={
                        route.status === "disrupted" ? "7 5" : "none"
                      }
                    />
                    {/* Wide transparent hit area */}
                    <path
                      d={d}
                      fill="none"
                      stroke="transparent"
                      strokeWidth={18}
                      style={{ cursor: "pointer" }}
                      onClick={() =>
                        setSelectedRoute({ code, sector: route.sector })
                      }
                    />
                  </g>
                );
              });
            })}

            {/* Country pins */}
            {codes.map((code) => {
              const pt = nodes[code];
              if (!pt) return null;
              const routes = grouped[code].filter((r) => active.has(r.sector));
              if (routes.length === 0) return null;
              const isSel = selectedRoute && code === selectedRoute.code;
              const isDim = selectedRoute && !isSel;
              const color = SECTORS[routes[0].sector].color;
              const r = isSel ? 9 : 7;
              const tipY = pt.y + r * 2.1;
              return (
                <g
                  key={code}
                  onClick={() =>
                    setSelectedRoute({ code, sector: routes[0].sector })
                  }
                  style={{ cursor: "pointer" }}
                  opacity={isDim ? 0.18 : 1}
                >
                  {/* Drop shadow at pin tip */}
                  <ellipse
                    cx={pt.x}
                    cy={tipY + 3}
                    rx={r * 0.65}
                    ry={r * 0.28}
                    fill="rgba(0,0,0,0.35)"
                  />
                  {/* Glow ring */}
                  <circle
                    cx={pt.x}
                    cy={pt.y - r}
                    r={r * 2.6}
                    fill={color}
                    opacity={isSel ? 0.22 : 0.1}
                  />
                  {/* Pin circle */}
                  <circle cx={pt.x} cy={pt.y - r} r={r} fill={color} />
                  {/* Pin stem triangle */}
                  <path
                    d={`M ${pt.x - r * 0.78} ${pt.y - r * 0.3} L ${pt.x + r * 0.78} ${pt.y - r * 0.3} L ${pt.x} ${tipY}`}
                    fill={color}
                  />
                  {/* Inner white dot */}
                  <circle
                    cx={pt.x}
                    cy={pt.y - r}
                    r={r * 0.38}
                    fill="rgba(255,255,255,0.92)"
                  />
                  {/* Country code */}
                  <text
                    x={pt.x}
                    y={tipY + 13}
                    textAnchor="middle"
                    fontSize={isSel ? "9.5" : "8"}
                    fontWeight="700"
                    fill={isSel ? "rgba(45,58,82,0.9)" : "rgba(45,58,82,0.6)"}
                    fontFamily="Inter,sans-serif"
                  >
                    {code}
                  </text>
                </g>
              );
            })}

            {/* SG node */}
            {sgNode && (
              <g filter="url(#glow)">
                <circle
                  cx={sgNode.x}
                  cy={sgNode.y}
                  r={30}
                  fill="rgba(45,58,82,0.08)"
                />
                <circle
                  cx={sgNode.x}
                  cy={sgNode.y}
                  r={18}
                  fill="rgba(45,58,82,0.15)"
                />
                <circle cx={sgNode.x} cy={sgNode.y} r={11} fill="#2D3A52" />
                <circle
                  cx={sgNode.x}
                  cy={sgNode.y}
                  r={4.5}
                  fill="rgba(255,255,255,0.95)"
                />
                <text
                  x={sgNode.x}
                  y={sgNode.y + 27}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight="700"
                  fill="rgba(45,58,82,0.7)"
                  fontFamily="Inter,sans-serif"
                >
                  SG
                </text>
              </g>
            )}
          </g>
          {/* end zoom group */}
        </svg>

        {/* ── Disruption Alert Modal ── */}
        {disruptedCount > 0 &&
          !alertDismissed &&
          !selectedRoute &&
          (() => {
            const disrupted = allActiveRoutes.filter(
              (r) => r.status === "disrupted",
            );
            return (
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  zIndex: 50,
                  background: "rgba(232,85,80,0.13)",
                  backdropFilter: "blur(3px)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  animation: "panelIn 0.3s ease both",
                }}
              >
                <div
                  style={{
                    background: "#FDFCFA",
                    borderRadius: 18,
                    overflow: "hidden",
                    width: 420,
                    maxWidth: "90%",
                    boxShadow:
                      "0 24px 60px rgba(232,85,80,0.25), 0 8px 24px rgba(0,0,0,0.12)",
                    border: "1.5px solid rgba(232,85,80,0.3)",
                  }}
                >
                  {/* Red accent bar */}
                  <div
                    style={{
                      height: 5,
                      background: "linear-gradient(to right, #E85550, #ff7875)",
                    }}
                  />

                  {/* Header */}
                  <div
                    style={{
                      padding: "22px 24px 18px",
                      borderBottom: "1px solid rgba(232,85,80,0.1)",
                      background: "rgba(232,85,80,0.04)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                        marginBottom: 6,
                      }}
                    >
                      <div style={{ fontSize: 22 }}>🚨</div>
                      <div>
                        <div
                          style={{
                            fontSize: 9,
                            fontWeight: 800,
                            color: "#E85550",
                            textTransform: "uppercase",
                            letterSpacing: "0.14em",
                            marginBottom: 3,
                          }}
                        >
                          Network Alert
                        </div>
                        <div
                          style={{
                            fontSize: 20,
                            fontWeight: 800,
                            color: "#2D3A52",
                            letterSpacing: "-0.02em",
                            lineHeight: 1.2,
                          }}
                        >
                          Supply Chain Disruption
                          {disrupted.length > 1 ? "s" : ""} Detected
                        </div>
                      </div>
                    </div>
                    <div
                      style={{
                        fontSize: 12.5,
                        color: "rgba(45,58,82,0.55)",
                        lineHeight: 1.6,
                        marginLeft: 32,
                      }}
                    >
                      {disrupted.length} active disruption
                      {disrupted.length > 1 ? "s" : ""} require
                      {disrupted.length === 1 ? "s" : ""} immediate review. Use
                      the decision simulation to generate response strategies.
                    </div>
                  </div>

                  {/* Disruption list */}
                  <div style={{ padding: "14px 24px" }}>
                    {disrupted.map((r, i) => (
                      <div
                        key={i}
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 12,
                          padding: "10px 0",
                          borderBottom:
                            i < disrupted.length - 1
                              ? "1px solid rgba(45,58,82,0.06)"
                              : "none",
                        }}
                      >
                        <span
                          style={{ fontSize: 22, flexShrink: 0, lineHeight: 1 }}
                        >
                          {FLAGS[r.code] || "🌐"}
                        </span>
                        <div style={{ flex: 1 }}>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 7,
                              marginBottom: 3,
                            }}
                          >
                            <span
                              style={{
                                fontSize: 13,
                                fontWeight: 700,
                                color: "#2D3A52",
                              }}
                            >
                              {r.country}
                            </span>
                            <span
                              style={{
                                fontSize: 9.5,
                                fontWeight: 700,
                                color: SECTORS[r.sector]?.color,
                                background: SECTORS[r.sector]?.color + "18",
                                borderRadius: 5,
                                padding: "1px 6px",
                              }}
                            >
                              {SECTORS[r.sector]?.label}
                            </span>
                          </div>
                          <div
                            style={{
                              fontSize: 11.5,
                              color: "rgba(45,58,82,0.6)",
                              lineHeight: 1.5,
                            }}
                          >
                            {r.note}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Actions */}
                  <div
                    style={{
                      display: "flex",
                      gap: 10,
                      padding: "14px 24px 22px",
                    }}
                  >
                    <button
                      onClick={() => setAlertDismissed(true)}
                      style={{
                        flex: 1,
                        padding: "11px",
                        background: "transparent",
                        border: "1.5px solid rgba(45,58,82,0.15)",
                        borderRadius: 10,
                        fontSize: 12,
                        fontWeight: 600,
                        color: "rgba(45,58,82,0.55)",
                        cursor: "pointer",
                        fontFamily: "'Inter',sans-serif",
                        transition: "all 0.15s",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background =
                          "rgba(45,58,82,0.05)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.background = "transparent")
                      }
                    >
                      Acknowledge
                    </button>
                    <button
                      onClick={() => {
                        setAlertDismissed(true);
                        setSelectedRoute({
                          code: disrupted[0].code,
                          sector: disrupted[0].sector,
                        });
                      }}
                      style={{
                        flex: 2,
                        padding: "11px",
                        background: "#E85550",
                        border: "none",
                        borderRadius: 10,
                        fontSize: 12,
                        fontWeight: 700,
                        color: "#fff",
                        cursor: "pointer",
                        fontFamily: "'Inter',sans-serif",
                        transition: "all 0.15s",
                        letterSpacing: "0.01em",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background = "#d44")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.background = "#E85550")
                      }
                    >
                      Start Resolve →
                    </button>
                  </div>
                </div>
              </div>
            );
          })()}

        {/* ── Scrape frequency control — bottom-right ── */}
        {(() => {
          const FREQS = [
            { id: "1h", label: "Every hour" },
            { id: "6h", label: "Every 6 hours" },
            { id: "12h", label: "Every 12 hours" },
            { id: "1d", label: "Daily" },
            { id: "3d", label: "Every 3 days" },
            { id: "7d", label: "Weekly" },
          ];
          const current = FREQS.find((f) => f.id === scrapeFreq);
          return (
            <div
              style={{
                position: "absolute",
                bottom: 20,
                right: 16,
                zIndex: 20,
              }}
            >
              {/* Dropdown */}
              {scrapeMenuOpen && (
                <div
                  style={{
                    position: "absolute",
                    bottom: "calc(100% + 6px)",
                    right: 0,
                    background: "rgba(253,252,250,0.97)",
                    backdropFilter: "blur(14px)",
                    border: "1px solid rgba(45,58,82,0.12)",
                    borderRadius: 10,
                    padding: "6px 5px",
                    minWidth: 160,
                    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
                    animation: "panelIn 0.18s ease both",
                  }}
                >
                  <div
                    style={{
                      fontSize: 8.5,
                      fontWeight: 800,
                      color: "rgba(45,58,82,0.32)",
                      textTransform: "uppercase",
                      letterSpacing: "0.11em",
                      padding: "2px 8px 6px",
                    }}
                  >
                    Scrape frequency
                  </div>
                  {FREQS.map((f) => {
                    const active = f.id === scrapeFreq;
                    return (
                      <button
                        key={f.id}
                        onClick={() => {
                          setScrapeFreq(f.id);
                          setScrapeMenuOpen(false);
                        }}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          width: "100%",
                          padding: "6px 10px",
                          background: active
                            ? "rgba(45,58,82,0.07)"
                            : "transparent",
                          border: "none",
                          borderRadius: 7,
                          cursor: "pointer",
                          fontFamily: "'Inter',sans-serif",
                          transition: "background 0.12s",
                        }}
                        onMouseEnter={(e) => {
                          if (!active)
                            e.currentTarget.style.background =
                              "rgba(45,58,82,0.04)";
                        }}
                        onMouseLeave={(e) => {
                          if (!active)
                            e.currentTarget.style.background = "transparent";
                        }}
                      >
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: active ? 700 : 500,
                            color: active ? "#2D3A52" : "rgba(45,58,82,0.6)",
                          }}
                        >
                          {f.label}
                        </span>
                        {active && (
                          <span
                            style={{
                              fontSize: 10,
                              color: "#18A87A",
                              fontWeight: 700,
                            }}
                          >
                            ✓
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Toggle button */}
              <button
                onClick={() => setScrapeMenuOpen((v) => !v)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "5px 10px 5px 7px",
                  background: scrapeMenuOpen
                    ? "rgba(45,58,82,0.1)"
                    : "rgba(245,242,238,0.92)",
                  backdropFilter: "blur(10px)",
                  border: "1px solid rgba(45,58,82,0.14)",
                  borderRadius: 20,
                  cursor: "pointer",
                  fontFamily: "'Inter',sans-serif",
                  transition: "all 0.15s",
                  boxShadow: "0 1px 6px rgba(0,0,0,0.07)",
                }}
              >
                {/* Radar icon */}
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 20 20"
                  fill="none"
                  style={{ flexShrink: 0 }}
                >
                  <circle
                    cx="10"
                    cy="10"
                    r="2.5"
                    fill="#2D3A52"
                    opacity="0.7"
                  />
                  <circle
                    cx="10"
                    cy="10"
                    r="5.5"
                    stroke="#2D3A52"
                    strokeWidth="1.4"
                    opacity="0.4"
                    fill="none"
                  />
                  <circle
                    cx="10"
                    cy="10"
                    r="9"
                    stroke="#2D3A52"
                    strokeWidth="1.2"
                    opacity="0.18"
                    fill="none"
                  />
                </svg>
                <span
                  style={{
                    fontSize: 10.5,
                    fontWeight: 700,
                    color: "rgba(45,58,82,0.75)",
                  }}
                >
                  {current?.id}
                </span>
                <span
                  style={{
                    fontSize: 9,
                    color: "rgba(45,58,82,0.35)",
                    fontWeight: 500,
                  }}
                >
                  sweep
                </span>
                <span
                  style={{
                    fontSize: 8,
                    color: "rgba(45,58,82,0.4)",
                    marginLeft: 1,
                  }}
                >
                  {scrapeMenuOpen ? "▲" : "▼"}
                </span>
              </button>
            </div>
          );
        })()}
      </div>
      {/* end map container */}

      {/* ── STATUS TAB PANEL ── */}
      {!selectedRoute &&
        (() => {
          const TABS = [
            {
              id: "disrupted",
              label: "Disrupted",
              color: "#E85550",
              routes: allActiveRoutes.filter((r) => r.status === "disrupted"),
              desc: (n) =>
                `${n} connection${n !== 1 ? "s" : ""} with active disruption. Immediate attention required — supply continuity at risk.`,
            },
            {
              id: "mild",
              label: "Mild",
              color: "#F0A020",
              routes: allActiveRoutes.filter((r) => r.status === "mild"),
              desc: (n) =>
                `${n} connection${n !== 1 ? "s" : ""} showing early stress signals. Monitor closely for escalation.`,
            },
            {
              id: "stable",
              label: "Stable",
              color: "#18A87A",
              routes: allActiveRoutes.filter((r) => r.status === "stable"),
              desc: (n) =>
                `${n} connection${n !== 1 ? "s" : ""} operating normally. No intervention required at this time.`,
            },
          ];
          const activeTab = TABS.find((t) => t.id === statusTab);

          return (
            <div
              style={{
                flexShrink: 0,
                margin: "0 10px 6px",
                background: "#FDFCFA",
                border: "1px solid rgba(45,58,82,0.1)",
                borderRadius: 12,
                overflow: "hidden",
              }}
            >
              {/* Tab bar */}
              <div
                style={{
                  display: "flex",
                  borderBottom: "1px solid rgba(45,58,82,0.08)",
                }}
              >
                {TABS.map((t) => {
                  const active = statusTab === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setStatusTab(active ? null : t.id)}
                      style={{
                        flex: 1,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 6,
                        padding: "9px 8px",
                        background: active ? t.color + "0f" : "transparent",
                        border: "none",
                        borderBottom: active
                          ? `2px solid ${t.color}`
                          : "2px solid transparent",
                        cursor: "pointer",
                        fontFamily: "'Inter',sans-serif",
                        transition: "all 0.15s",
                        marginBottom: -1,
                      }}
                    >
                      <div
                        style={{
                          width: 7,
                          height: 7,
                          borderRadius: "50%",
                          background:
                            t.routes.length > 0
                              ? t.color
                              : "rgba(45,58,82,0.2)",
                          flexShrink: 0,
                          animation:
                            t.id === "disrupted" && t.routes.length > 0
                              ? "pulse 2s ease-in-out infinite"
                              : "none",
                        }}
                      />
                      <span
                        style={{
                          fontSize: 11.5,
                          fontWeight: active ? 700 : 500,
                          color: active ? t.color : "rgba(45,58,82,0.45)",
                        }}
                      >
                        {t.label}
                      </span>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 700,
                          color: active ? t.color : "rgba(45,58,82,0.35)",
                          background: active
                            ? t.color + "18"
                            : "rgba(45,58,82,0.06)",
                          borderRadius: 10,
                          padding: "1px 6px",
                          minWidth: 20,
                          textAlign: "center",
                        }}
                      >
                        {t.routes.length}
                      </span>
                    </button>
                  );
                })}
                {/* Metrics right side */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "0 14px",
                    borderLeft: "1px solid rgba(45,58,82,0.08)",
                  }}
                >
                  <span
                    style={{
                      fontSize: 9.5,
                      color: "rgba(45,58,82,0.28)",
                      fontWeight: 500,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {allActiveRoutes.length} total · {totalCountries} countries
                  </span>
                </div>
              </div>

              {/* Connection cards for active tab */}
              {activeTab && (
                <div style={{ animation: "panelIn 0.18s ease both" }}>
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      padding: "10px 12px",
                      overflowX: "auto",
                    }}
                  >
                    {activeTab.routes.map((r, i) => {
                      const sc = SECTORS[r.sector]?.color || "#2D3A52";
                      return (
                        <button
                          key={i}
                          onClick={() => {
                            setSelectedRoute({
                              code: r.code,
                              sector: r.sector,
                            });
                            setStatusTab(null);
                          }}
                          style={{
                            flexShrink: 0,
                            display: "flex",
                            alignItems: "center",
                            gap: 10,
                            padding: "9px 13px",
                            background: "rgba(245,242,238,0.6)",
                            border: `1px solid rgba(45,58,82,0.09)`,
                            borderLeft: `3px solid ${sc}`,
                            borderRadius: "0 9px 9px 0",
                            cursor: "pointer",
                            fontFamily: "'Inter',sans-serif",
                            textAlign: "left",
                            transition: "all 0.14s",
                            minWidth: 210,
                            maxWidth: 260,
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = sc + "12";
                            e.currentTarget.style.boxShadow = `0 2px 12px ${sc}18`;
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background =
                              "rgba(245,242,238,0.6)";
                            e.currentTarget.style.boxShadow = "none";
                          }}
                        >
                          <span
                            style={{
                              fontSize: 20,
                              lineHeight: 1,
                              flexShrink: 0,
                            }}
                          >
                            {FLAGS[r.code] || "🌐"}
                          </span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 6,
                                marginBottom: 2,
                              }}
                            >
                              <div
                                style={{
                                  fontSize: 12.5,
                                  fontWeight: 700,
                                  color: "#2D3A52",
                                  lineHeight: 1.2,
                                }}
                              >
                                {r.country}
                              </div>
                              <div
                                style={{
                                  fontSize: 9,
                                  color: sc,
                                  fontWeight: 700,
                                  background: sc + "18",
                                  borderRadius: 4,
                                  padding: "1px 5px",
                                  flexShrink: 0,
                                }}
                              >
                                {SECTORS[r.sector]?.label}
                              </div>
                            </div>
                            <div
                              style={{
                                fontSize: 10.5,
                                color: "rgba(45,58,82,0.48)",
                                lineHeight: 1.4,
                                whiteSpace: "normal",
                              }}
                            >
                              {r.note}
                            </div>
                          </div>
                          <span
                            style={{
                              fontSize: 12,
                              color: "rgba(45,58,82,0.25)",
                              flexShrink: 0,
                              marginLeft: 6,
                            }}
                          >
                            →
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })()}

      {/* ── DEBATE SECTION — below map when route selected ── */}
      {selectedRoute &&
        (() => {
          const route = selectedRoutes[0] || {
            country:
              grouped[selectedRoute.code]?.[0]?.country || selectedRoute.code,
            sector: selectedRoute.sector,
            status: "stable",
            note: "",
          };
          const sectorColor = SECTORS[selectedRoute.sector].color;
          const isDisrupted = route.status === "disrupted";
          const isMild = route.status === "mild";
          const statusColor = isDisrupted
            ? "#E85550"
            : isMild
              ? "#F0A020"
              : "#18A87A";
          const statusLabel = isDisrupted
            ? "Disrupted"
            : isMild
              ? "Mild"
              : "Stable";
          const selectedNewsItems = relatedNews.filter((_, i) =>
            selectedNews.has(i),
          );

          return (
            <div
              ref={debateRef}
              style={{
                margin: "8px 10px 10px",
                display: "flex",
                flexDirection: "column",
                gap: 8,
                animation: "panelIn 0.35s ease both",
              }}
            >
              {/* ── Connection Brief ── */}
              <div
                style={{
                  background: "#FDFCFA",
                  border: "1px solid rgba(45,58,82,0.1)",
                  borderRadius: 12,
                  overflow: "hidden",
                }}
              >
                <div style={{ height: 3, background: sectorColor }} />
                <div style={{ padding: "16px 18px 18px" }}>
                  {/* Sector + status */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: 13,
                    }}
                  >
                    <span
                      style={{
                        fontSize: 9,
                        fontWeight: 800,
                        color: sectorColor,
                        textTransform: "uppercase",
                        letterSpacing: "0.13em",
                      }}
                    >
                      {SECTORS[selectedRoute.sector].label} · SG Supply Network
                    </span>
                    <span
                      style={{
                        fontSize: 8.5,
                        fontWeight: 700,
                        padding: "3px 9px",
                        borderRadius: 20,
                        background: statusColor + "18",
                        color: statusColor,
                        border: `1px solid ${statusColor}44`,
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                      }}
                    >
                      {isDisrupted ? "⚠ " : "● "}
                      {statusLabel}
                    </span>
                  </div>
                  {/* Country */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 14,
                      marginBottom: 16,
                    }}
                  >
                    <span style={{ fontSize: 36, lineHeight: 1 }}>
                      {FLAGS[selectedRoute.code] || "🌍"}
                    </span>
                    <div>
                      <div
                        style={{
                          fontSize: 24,
                          fontWeight: 800,
                          color: "#2D3A52",
                          letterSpacing: "-0.02em",
                          lineHeight: 1.1,
                        }}
                      >
                        {grouped[selectedRoute.code]?.[0]?.country ||
                          selectedRoute.code}
                      </div>
                      <div
                        style={{
                          fontSize: 10.5,
                          color: "rgba(45,58,82,0.38)",
                          marginTop: 3,
                          fontWeight: 500,
                        }}
                      >
                        Singapore ↔{" "}
                        {grouped[selectedRoute.code]?.[0]?.country ||
                          selectedRoute.code}
                      </div>
                    </div>
                  </div>
                  {/* Note */}
                  {route.note && (
                    <>
                      <div
                        style={{
                          fontSize: 9,
                          fontWeight: 800,
                          color: "rgba(45,58,82,0.3)",
                          textTransform: "uppercase",
                          letterSpacing: "0.12em",
                          marginBottom: 6,
                        }}
                      >
                        Connection Brief
                      </div>
                      <div
                        style={{
                          fontSize: 14.5,
                          fontWeight: 600,
                          color: "rgba(45,58,82,0.9)",
                          lineHeight: 1.55,
                          letterSpacing: "-0.01em",
                        }}
                      >
                        {route.note}
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* ── Related Signals — selectable ── */}
              {relatedNews.length > 0 && (
                <div
                  style={{
                    background: "#FDFCFA",
                    border: "1px solid rgba(45,58,82,0.1)",
                    borderRadius: 12,
                    overflow: "hidden",
                  }}
                >
                  {/* Header */}
                  <div
                    style={{
                      padding: "12px 18px 10px",
                      display: "flex",
                      alignItems: "center",
                      gap: 7,
                      borderBottom: "1px solid rgba(45,58,82,0.07)",
                      background: "rgba(45,58,82,0.015)",
                    }}
                  >
                    <div
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        background: "#E85550",
                        flexShrink: 0,
                        animation: "pulse 1.5s ease-in-out infinite",
                      }}
                    />
                    <span
                      style={{
                        fontSize: 10,
                        fontWeight: 800,
                        color: "rgba(45,58,82,0.75)",
                        letterSpacing: "0.09em",
                        textTransform: "uppercase",
                      }}
                    >
                      Related Signals
                    </span>
                    <span
                      style={{
                        marginLeft: "auto",
                        fontSize: 9.5,
                        color: "rgba(45,58,82,0.35)",
                      }}
                    >
                      {selectedNews.size}/{relatedNews.length} selected for
                      debate
                    </span>
                  </div>
                  {relatedNews.map((n, i) => {
                    const checked = selectedNews.has(i);
                    return (
                      <div
                        key={i}
                        onClick={() =>
                          setSelectedNews((prev) => {
                            const next = new Set(prev);
                            next.has(i) ? next.delete(i) : next.add(i);
                            return next;
                          })
                        }
                        style={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 12,
                          padding: "13px 18px",
                          borderBottom:
                            i < relatedNews.length - 1
                              ? "1px solid rgba(45,58,82,0.06)"
                              : "none",
                          background: checked
                            ? sectorColor + "07"
                            : "transparent",
                          cursor: "pointer",
                          transition: "background 0.14s",
                        }}
                      >
                        {/* Custom checkbox */}
                        <div
                          style={{
                            flexShrink: 0,
                            width: 17,
                            height: 17,
                            borderRadius: 5,
                            marginTop: 2,
                            border: `1.5px solid ${checked ? sectorColor : "rgba(45,58,82,0.18)"}`,
                            background: checked ? sectorColor : "transparent",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            transition: "all 0.15s",
                          }}
                        >
                          {checked && (
                            <span
                              style={{
                                fontSize: 10,
                                color: "#fff",
                                lineHeight: 1,
                                fontWeight: 700,
                              }}
                            >
                              ✓
                            </span>
                          )}
                        </div>
                        {/* Number */}
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 800,
                            color: sectorColor + "77",
                            lineHeight: "18px",
                            minWidth: 22,
                            flexShrink: 0,
                            paddingTop: 1,
                          }}
                        >
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div
                            style={{
                              fontSize: 12.5,
                              fontWeight: 700,
                              color: "rgba(45,58,82,0.92)",
                              lineHeight: 1.4,
                              letterSpacing: "-0.01em",
                              marginBottom: 4,
                            }}
                          >
                            {n.headline}
                          </div>
                          <div
                            style={{
                              fontSize: 11,
                              color: "rgba(45,58,82,0.5)",
                              lineHeight: 1.55,
                            }}
                          >
                            {n.snippet}
                          </div>
                        </div>
                        <span
                          style={{
                            fontSize: 13,
                            color: "rgba(45,58,82,0.2)",
                            marginTop: 2,
                            flexShrink: 0,
                          }}
                        >
                          ↗
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* ── Decision Simulation ── */}
              <div
                style={{
                  background: "#FDFCFA",
                  border: "1px solid rgba(45,58,82,0.1)",
                  borderRadius: 12,
                  overflow: "hidden",
                }}
              >
                <div style={{ height: 3, background: sectorColor }} />
                <DecisionSimPanel
                  route={route}
                  sectorColor={sectorColor}
                  selectedNewsItems={selectedNewsItems}
                />
              </div>
            </div>
          );
        })()}

      {/* ── BOTTOM PANEL — collapses when connection selected ─────── */}
      <div
        style={{
          flex: "0 0 auto",
          maxHeight: selectedRoute ? "0" : "36vh",
          minHeight: 0,
          overflow: "hidden",
          opacity: selectedRoute ? 0 : 1,
          transition:
            "max-height 0.55s cubic-bezier(0.4,0,0.2,1), opacity 0.35s ease",
          margin: "0 10px 10px",
        }}
      >
        <div
          style={{
            height: "100%",
            background: "#FDFCFA",
            border: "1px solid rgba(45,58,82,0.1)",
            borderRadius: 12,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "10px 18px",
              borderBottom: "1px solid rgba(45,58,82,0.1)",
              display: "flex",
              alignItems: "center",
              gap: 8,
              flexShrink: 0,
              background: "rgba(45,58,82,0.03)",
            }}
          >
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: "#E85550",
                animation: "pulse 1.5s ease-in-out infinite",
              }}
            />
            <span
              style={{
                fontSize: 13,
                fontWeight: 700,
                color: "rgba(45,58,82,0.9)",
                letterSpacing: "-0.01em",
              }}
            >
              Global Signals
            </span>
            <span
              style={{
                fontSize: 10,
                fontWeight: 600,
                color: "rgba(45,58,82,0.35)",
                marginLeft: 2,
              }}
            >
              — Live Feed
            </span>
            <div
              style={{
                marginLeft: "auto",
                display: "flex",
                alignItems: "center",
                gap: 10,
              }}
            >
              <span style={{ fontSize: 10, color: "rgba(45,58,82,0.3)" }}>
                {NEWS.length} stories
              </span>
              <button
                onClick={() => onNavigate("scenario")}
                style={{
                  padding: "4px 11px",
                  background: "#2D3A52",
                  border: "none",
                  borderRadius: 7,
                  fontSize: 10,
                  fontWeight: 700,
                  color: "#F5F2EE",
                  cursor: "pointer",
                  fontFamily: "'Inter',sans-serif",
                  letterSpacing: "0.02em",
                  whiteSpace: "nowrap",
                }}
              >
                Scenario Sim →
              </button>
            </div>
          </div>
          <div style={{ overflowY: "auto", flex: 1 }}>
            {NEWS.map((n, i) => {
              const s = SECTORS[n.tag];
              return (
                <a
                  key={i}
                  href={n.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 12,
                    padding: "10px 18px",
                    borderBottom: "1px solid rgba(45,58,82,0.07)",
                    textDecoration: "none",
                    transition: "background 0.14s",
                    background: "transparent",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "rgba(45,58,82,0.04)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = "transparent")
                  }
                >
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: "rgba(201,184,154,0.8)",
                      lineHeight: "20px",
                      minWidth: 20,
                      flexShrink: 0,
                    }}
                  >
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div
                    style={{
                      flexShrink: 0,
                      marginTop: 2,
                      padding: "2px 7px",
                      borderRadius: 5,
                      border: `1px solid ${s.color}44`,
                      background: s.color + "14",
                      fontSize: 9,
                      fontWeight: 700,
                      color: s.color,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {s.label}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontSize: 12.5,
                        fontWeight: 600,
                        color: "rgba(45,58,82,0.9)",
                        marginBottom: 2,
                        lineHeight: 1.4,
                        letterSpacing: "-0.01em",
                      }}
                    >
                      {n.headline}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: "rgba(45,58,82,0.5)",
                        lineHeight: 1.55,
                      }}
                    >
                      {n.snippet}
                    </div>
                  </div>
                  <span
                    style={{
                      flexShrink: 0,
                      fontSize: 12,
                      color: "rgba(45,58,82,0.3)",
                      marginTop: 2,
                    }}
                  >
                    ↗
                  </span>
                </a>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── STAKEHOLDER GUIDANCE — collapses when connection selected ── */}
      <div
        style={{
          flex: "0 0 auto",
          maxHeight: selectedRoute ? "0" : "600px",
          minHeight: 0,
          overflow: "hidden",
          opacity: selectedRoute ? 0 : 1,
          transition:
            "max-height 0.55s cubic-bezier(0.4,0,0.2,1), opacity 0.35s ease",
          margin: "0 10px 10px",
        }}
      >
        <StakeholderGuidance />
      </div>
    </div>
  );
}
