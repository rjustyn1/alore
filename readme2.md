# ALORE: Singapore Supply Chain Resilience Platform

## What is ALORE?

ALORE is an **intelligent supply chain monitoring and intelligence platform** designed to help Singapore anticipate, monitor, and respond to global disruptions that threaten critical imports—food, energy, and essential commodities.

The platform automatically:
- **Tracks** Singapore's supply chain dependencies (where goods come from, what commodities are at risk)
- **Monitors** global disruption events in real-time (political instability, natural disasters, trade conflicts)
- **Curates** relevant news and signals that impact Singapore's supply security
- **Alerts** decision-makers with severity-ranked intelligence when disruptions occur

---

## Business Value

### 1. **Risk Mitigation**
- **Identify vulnerabilities early**: Know which suppliers, countries, and commodities pose the highest risk
- **Reduce supply chain shocks**: Early warning enables proactive sourcing, inventory adjustments, and contingency planning
- **Protect critical sectors**: Ensure food security, energy stability, and essential goods availability

### 2. **Strategic Decision Support**
- **Evidence-based planning**: Data-driven intelligence for trade negotiations, supplier diversification, and strategic reserves
- **Policy informed by reality**: Supply chain visibility and predictive modeling informs national resilience policies
- **Cross-agency coordination**: Centralized intelligence platform for government agencies to share insights

### 3. **Operational Efficiency**
- **Automated intelligence gathering**: Continuous monitoring reduces manual research burden
- **Fast signal detection**: LLM-powered classification flags high-severity disruptions immediately
- **Reduced false positives**: Intelligent deduplication and consolidation filters noise, surfaces only meaningful events

### 4. **Competitive Advantage**
- **Market knowledge**: Understanding supply chain shifts before competitors enables faster adaptation
- **Procurement optimization**: Negotiate from position of strength with better visibility into market conditions
- **Investor confidence**: Demonstrate supply chain resilience to stakeholders and markets

---

## How ALORE Works

### **Current Modules (Phase 1)**

#### 🌍 **Supply Chain Connections Scraper**
**What it does**: Maps Singapore's import dependencies

- Identifies where Singapore sources critical commodities (food, energy, minerals, etc.)
- Tracks import volumes and suppliers by country
- Categorizes goods by sector impact
- Updates periodically as trade patterns evolve

**Business use**: Build baseline understanding of supply chain exposure and dependencies

---

#### 📰 **News Curator**
**What it does**: Surfaces relevant global disruption signals

- Continuously monitors global news, geopolitical events, natural disasters, trade announcements
- Classifies news as:
  - **Internal**: Direct Singapore impact (Singapore-specific events, bilateral trade disputes)
  - **External**: Global supply chain impact (events affecting Singapore's suppliers)
- Ranks by severity and relevance
- Deduplicates to avoid news fatigue

**Business use**: Maintain real-time awareness of emerging risks without information overload

---

#### 🚨 **Disruption Monitor**
**What it does**: Automated 24/7 disruption event detection and tracking

- Runs daily (Singapore time) to scan for new disruption events
- LLM classifies severity:
  - `WARNING`: Minor supply friction expected
  - `CONSTRAINED`: Supply limitations likely
  - `DISRUPTED`: Significant supply impact
  - `CRITICAL`: Severe supply failure risk
- Tracks origin country, affected commodities, evidence sources
- Maintains historical record of all events
- Alerts on new or worsening disruptions

**Business use**: Automated 24/7 monitoring ensures no critical disruption goes unnoticed

---

## Key Features

| Feature | Benefit |
|---------|---------|
| **Real-time Monitoring** | Continuous 24/7 event detection—no manual scanning required |
| **Severity Ranking** | Focus on what matters: `CRITICAL` and `DISRUPTED` events get priority |
| **Historical Tracking** | Build knowledge of patterns, repeating risks, and seasonal vulnerabilities |
| **Deduplication & Consolidation** | One unified event record prevents duplicate alerts and confusion |
| **Multi-source Intelligence** | Evidence from multiple reputable sources increases confidence in signals |
| **Supply Chain Context** | News curator understands Singapore's supply dependencies—flags relevant events automatically |
| **LLM-Powered Classification** | Semantic understanding of disruption context (not just keyword matching) |

---

## Who Benefits?

### **Government & Policy**
- Trade ministries plan tariff and trade agreements
- Supply resilience teams prepare contingency responses
- National security agencies anticipate geopolitical supply risks

### **Private Sector**
- Importers and distributors optimize sourcing and inventory
- Manufacturers plan production adjustments
- Logistics companies adjust routing and capacity

### **Financial Institutions**
- Banks assess borrower supply chain risks
- Insurers price supply chain disruption coverage
- Investors evaluate supply chain resilience of Singapore-based companies

---

## Example Scenarios

### **Scenario 1: Geopolitical Trade Conflict**
A major trade dispute erupts between Singapore's main oil supplier and a neighboring country.
- **ALORE detects**: New headlines about the conflict + LLM identifies energy sector impact
- **Severity assigned**: `CRITICAL` (energy is essential commodity)
- **Action triggered**: Energy ministry reviews strategic reserves, explores alternative suppliers
- **Value**: 2-week early warning vs. discovering problem when deliveries stop

---

### **Scenario 2: Natural Disaster**
A hurricane hits a region producing 30% of Singapore's imported wheat.
- **ALORE detects**: News of harvest damage + LLM links to Singapore supply chain data
- **Severity assigned**: `DISRUPTED` (food security threat)
- **Historical context**: Event consolidated with prior similar events, showing pattern frequency
- **Action triggered**: Food authority activates alternative sourcing agreements
- **Value**: Automated detection + pattern visibility improves resilience planning

---

### **Scenario 3: Supply Constraint**
A factory producing critical semiconductor components shuts down temporarily.
- **ALORE detects**: News of shutdown + LLM assesses impact on Singapore's tech supply chain
- **Severity assigned**: `CONSTRAINED` (manageable impact)
- **Action triggered**: Electronics manufacturers adjust production schedules
- **Value**: Early signal allows smooth adjustment rather than production halts

---

## Technology Foundation

- **Backend**: FastAPI (Python) - fast, scalable API layer
- **Database**: SQLite with JSON support - persists event history
- **LLM Intelligence**: OpenAI GPT - semantic classification and curation
- **Web Scraper**: TINYSIDH - web scraping tool for trade, news, and geopolitical data
- **LLM Framework**: Multi-agent orchestration for negotiations and scenario simulations
- **Frontend**: React/Vite - accessible dashboards and decision support tools
- **Scheduling**: Automated daily runs - reliable 24/7 monitoring

---

## Impact Metrics

Measure ALORE success by:
- **Detection speed**: Days from disruption to alert (vs. weeks of manual discovery)
- **False positive rate**: Relevant events surfaced / total events flagged
- **Actionability**: % of alerts that trigger actual response/decision
- **Coverage**: % of Singapore's critical supply chains monitored
- **Cost savings**: Avoided supply disruption costs prevented by early action
- **Strategic value**: Policy decisions informed by TINYFISH intelligence

---

## Vision

ALORE is the **digital immune system** for Singapore's supply chain. Just as the human immune system detects and responds to threats automatically, ALORE continuously monitors the global environment, detects disruption signals, and alerts human decision-makers to take protective action.

The goal: **Transform Singapore from reactive responder to proactive resilience manager**—turning supply chain visibility into strategic advantage.

---

## Planned Features (Phase 2)

### 🤝 **Pre-Negotiation Simulation Agent**
**What it will do**: Intelligent trade negotiation simulation before real-world engagement

- **Process**:
  1. Internal discussion phase: Singapore agencies debate internal priorities, constraints, alternatives
  2. External negotiation phase: AI agents representing Singapore and alternative supplier countries negotiate
  3. Each agent equipped with live supply chain data via TINYSIDH (country-specific commodity availability, production capacity, trade flows)
  4. Agents debate trade-offs, pricing, delivery timelines, political considerations
  5. Generates negotiation outcomes and recommended positions

- **Business value**:
  - **Risk-free exploration**: Test negotiation outcomes before contacting real trading partners
  - **Better preparation**: Know likely positions and resistance points before formal talks
  - **Faster decisions**: Simulate multiple scenarios quickly to find optimal agreements
  - **Confident negotiations**: Engage from position of strength with predicted outcomes
  - **Relationship preservation**: Avoid failed negotiations that damage diplomatic ties

---

### 🎯 **What-If Scenario Simulation**
**What it will do**: Model hypothetical supply chain disruptions and mitigation strategies

- **Capabilities**:
  1. Define hypothetical scenario (e.g., "What if Country X closes ports for 6 months?")
  2. Simulate cascading impact across all dependent supply chains
  3. Model alternative sourcing options and their costs/risks
  4. Evaluate mitigation strategies (emergency reserves, alternate suppliers, domestic production)
  5. Quantify outcomes: delays, cost increases, vulnerability gaps
  6. Compare scenarios side-by-side to prioritize defenses

- **Business value**:
  - **Proactive resilience**: Identify vulnerabilities before disruptions occur
  - **Better contingency planning**: Test and refine response strategies in simulation
  - **Informed investments**: Know which supply chain investments yield highest resilience improvement
  - **Crisis preparedness**: Decision-makers already understand likely impacts and responses
  - **Strategic priorities**: Focus resources on highest-impact vulnerabilities

---

## Roadmap

- **Phase 1 (Current)**: Supply chain monitoring, news curation, disruption detection
- **Phase 2 (Planned)**: Pre-negotiation simulation, what-if scenario modeling
- **Phase 3 (Future)**:
  - Expand commodity coverage (beyond food/energy to electronics, rare earths, pharmaceuticals)
  - Integrate with government and industry supply chain datasets
  - Predictive disruption models (anticipate disruptions before they occur)
  - Real-time portfolio optimization (auto-recommend sourcing adjustments)
  - Cross-agency collaboration and coordinated response workflows
