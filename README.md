# ALORE: Singapore Supply Chain Resilience Platform

## Tech Stack

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/langgraph)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)

## Table of Contents

- [What is ALORE?](#what-is-alore)
- [How ALORE Works](#how-alore-works)
- [Who Benefits?](#who-benefits)
- [Business Value](#business-value)
- [Example Scenarios](#example-scenarios)
- [Technology Foundation](#technology-foundation)
- [Vision](#vision)
- [Detailed System Flow and Architecture](#detailed-system-flow-and-architecture)
- [All Features](#all-features)
- [Roadmap](#roadmap)

## What is ALORE?

ALORE is an **intelligent supply chain monitoring and intelligence platform** designed to help Singapore anticipate, monitor, and respond to global disruptions that threaten critical imports—food, energy, and essential commodities.
It is also designed as a reusable framework that can be adapted by other countries and businesses to build their own supply chain resilience platforms.

The platform automatically:
- **Tracks** Singapore supply chain dependencies (where goods come from, what commodities are at risk)
- **Monitors** global disruption events in real-time (political instability, natural disasters, trade conflicts), and alerts when disruptions occur
- **Reactive Mode**: If a disruption is detected, triggers simulation (can be controlled by the user)
- **Proactive Mode**: Generates "what-if" simulations to anticipate potential disruptions

---

## How ALORE Works

### **Current Modules**

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

#### 🤝 **Reactive Flow — Pre-Negotiation Simulation**
**What it does**: Runs intelligent trade negotiation simulations when a disruption is detected

- Triggered automatically when a disruption event is identified
- Prepares country-specific intelligence packets (scraper → knowledge base → RAG → planning agent)
- Launches parallel negotiation simulations: Singapore Agent vs. each candidate supplier country
- A judge agent evaluates each negotiation track for viability and trade-offs
- Aggregates all outcomes into a single recommendation: best partner, trade-off comparison, and next steps

**Business use**: Move from disruption detection to actionable partner recommendation—test negotiation outcomes before engaging real trading partners

---

#### 🎯 **Proactive Flow — What-If Scenario Simulation**
**What it does**: Models hypothetical disruptions and simulates cascading consequences before they happen

- Accepts user-defined hypothetical scenarios (e.g., "What if Country X closes ports for 6 months?")
- Runs a stateful simulation engine with propagation rules, event queues, and confidence scoring
- Agent layer proposes claims, requests evidence, and challenges weak hypotheses
- Evidence layer grounds the simulation with real-world data via TinyFish
- Verification layer normalizes evidence and only accepts claims that pass validation
- Produces verified impact chains, vulnerability assessments, and contingency recommendations

**Business use**: Stress-test supply chains and generate evidence-backed contingency plans before real shocks occur

---

#### 🟡 **Sentry — Real-Time Signal Monitoring**
**What it does**: Live observability layer that continuously tracks global supply chain signals

- Surfaces structured signals: commodity prices, trade activity, policy changes, and supply dependencies
- Each signal assigned a live status: `STABLE` → `MILD` → `DISRUPTED`
- Provides a signal overview (total monitored, active alerts, data sources), individual signal cards (category, value, trend, threshold, sources), and a chronological detection feed
- Displays all contributing data sources (Reuters, Bloomberg, MarineTraffic, FAO, etc.) for full traceability
- **Run Sweep**: manual refresh that re-triggers the scraping pipeline and recomputes all signals on demand
- Acts as the **entry point of intelligence** — signals crossing thresholds feed into the Reactive Flow as disruption events, and real-world trends inform What-If Scenario inputs

**Business use**: Always-on situational awareness dashboard — monitor early signals, inspect trends, and verify data sources without waiting for a disruption to be declared

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

## Example Scenarios

### **Scenario 1: Reactive Flow — Geopolitical Oil Disruption**
A geopolitical crisis disrupts Singapore's primary crude oil supply route through the Strait of Hormuz.
- **ALORE detects**: Disruption monitor flags the event as `CRITICAL` (energy is essential commodity)
- **Intelligence gathered**: Country-specific packets are prepared for Singapore, Saudi Arabia, Nigeria, and Kazakhstan—each with live export capacity, political constraints, and trade flow data via TinyFish
- **Negotiation simulations launched**:
  - SG Agent vs Saudi Arabia Agent → Judge evaluates pricing, delivery timeline, and diplomatic alignment
  - SG Agent vs Nigeria Agent → Judge evaluates capacity but flags political instability risk
  - SG Agent vs Kazakhstan Agent → Judge evaluates logistics cost and slower delivery window
- **Aggregated recommendation**: Saudi Arabia ranked as best immediate partner (fastest ramp-up, existing relationship), with Kazakhstan as secondary hedge
- **Value**: Decision-makers receive a data-backed, negotiation-tested recommendation within hours—not weeks of manual diplomatic outreach

---

### **Scenario 2: Proactive Flow — What-If Scenario on Rare Earth Export Ban**
A policy analyst asks: *"What if China restricts rare earth exports for 12 months?"*
- **Scenario seeded**: The what-if engine accepts the hypothetical and initializes world state with current rare earth dependency data
- **Propagation**: The engine identifies cascading effects—semiconductor manufacturing delays, defense electronics shortages, EV battery production slowdowns across ASEAN
- **Claims generated**: Agent layer proposes downstream consequences (e.g., "Singapore's electronics re-export sector contracts by 15%")
- **Evidence retrieved**: TinyFish fetches real-world data on alternative suppliers (Australia, Vietnam), current stockpile levels, and historical precedent from 2010 rare earth restrictions
- **Verification**: Claims checked against evidence—weak claims rejected, strong claims accepted as verified facts
- **Output**: Verified impact chain with confidence scores, vulnerability map, and contingency plan recommending strategic stockpile expansion and supplier diversification to Australia
- **Value**: Singapore identifies a critical vulnerability and develops a contingency strategy *before* the disruption occurs

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

## Vision

ALORE is the **digital immune system** for Singapore's supply chain. Just as the human immune system detects and responds to threats automatically, ALORE continuously monitors the global environment, detects disruption signals, and alerts human decision-makers to take protective action.

The goal: **Transform Singapore from reactive responder to proactive resilience manager**—turning supply chain visibility into strategic advantage.

---

## Detailed System Flow and Architecture

This section elaborates on the two core capabilities: **reactive disruption response** and **proactive what-if scenario simulation**. The diagrams below show how each capability is structured internally and how information flows through the system to produce grounded, actionable outputs. ALORE is designed to help Singapore respond to critical import disruptions and prepare for future risks, especially in a context where Singapore is highly trade-dependent and exposed to chokepoints and sudden global shocks.

---

### Key Feature 1: Reactive Flow — Real-Time Disruption Response

This feature corresponds to the pipeline that starts from a disruption event and ends with a data-backed recommendation on which trade partner to engage first.

#### What this feature does

When a real disruption occurs, the system does not immediately jump to a recommendation. Instead, it runs a **staged reasoning workflow** that first gathers intelligence, then simulates negotiation possibilities, and finally aggregates the outcomes into a decision-support output.

The purpose of this flow is to answer a question like:

> *"Given that a supplier route is disrupted, which alternative country should Singapore engage first, and why?"*

#### Architecture process

The debate architecture can be understood as four connected stages:

#### 1. Input layer: disruption intake

The process begins with a **disruption event**. This can represent a supply interruption involving a country, route, commodity, or geopolitical constraint. The orchestrator agent receives this event and triggers the rest of the system.

At this point, the disruption is treated as the initiating signal for a wider analysis pipeline rather than as an isolated alert.

#### 2. Intelligence layer: country-specific information preparation

After the disruption is received, the system prepares **intelligence packets** for Singapore and each candidate substitute country.

Each country has its own intelligence pipeline:

- **Scraper** → **Knowledge Base** → **RAG** → **Planning Agent**

This means every country is modeled with its own information context rather than sharing one generic pool of knowledge.

**Why this matters:**

- Singapore should reason from its own needs, constraints, and goals.
- A supplier country should reason from its own export capacity, incentives, political position, and constraints.
- This prevents the debate from becoming unrealistic or overly symmetric.

**Flow in practice:**

1. The **scraper** gathers relevant external information.
2. The **knowledge base** stores normalized country-specific information.
3. **RAG** retrieves the most relevant facts for the current disruption.
4. The **planning agent** converts retrieved facts into structured arguments or negotiation positions.

So before any debate begins, each side is equipped with a **grounded briefing packet**.

#### 3. Simulation layer: negotiation and debate

Once country-specific intelligence has been prepared, the system launches several negotiation simulations **in parallel**.

Each simulation has the structure:

> **Singapore Agent** ↔ **Country Agent** → **Judge**

For example:

- SG vs Country A
- SG vs Country B
- SG vs Country C

Each pair runs as an independent negotiation track.

Within each simulation:

- The **Singapore agent** argues from the perspective of Singapore's supply security, urgency, and strategic goals.
- The **country agent** argues from the perspective of the supplier country's interests and constraints.
- The **judge** evaluates the exchange and produces an agreement-oriented assessment.

This is not open-ended conversation for its own sake. The debate is a **structured evaluation mechanism** used to test:

- whether a partnership is viable,
- what trade-offs are involved,
- where the resistance points are,
- whether the outcome aligns with the user's goals.

This layer turns raw intelligence into a **negotiation outcome** rather than a static report.

#### 4. Decision layer: aggregation and recommendation

Each negotiation track produces an output that is then sent into the **results aggregator**.

The decision layer combines all parallel simulation outcomes and generates:

- **Best partner selection**
- **Trade-off comparison**
- **Recommendation**

Instead of returning three disconnected simulations, the system synthesizes them into a **single decision-support package** for stakeholders such as policymakers, businesses, or citizens.

#### Expanded description of the architecture

The debate architecture is designed around the idea that decision quality improves when each option is evaluated under its own evidence and negotiation context.

The important architectural choices are:

| Choice | Rationale |
|--------|-----------|
| **Separate intelligence stacks per country** | Ensures every country agent is grounded in different facts and incentives |
| **Parallel simulation branches** | Evaluates options independently, making comparison cleaner and faster |
| **Judge in every branch** | Acts as a structured evaluator rather than leaving output as raw agent dialogue |
| **Central aggregation at the end** | Prevents fragmented outputs and produces a single recommendation layer |

#### Why this matters

This architecture turns disruption response into more than a monitoring system. It becomes a **decision simulation system** that can move from detection to recommendation in a structured way.

In short, the reactive flow does three things:

1. **Understands** the disruption
2. **Tests** alternatives through negotiation
3. **Recommends** the best actionable path

---

### Key Feature 2: Proactive Flow — What-If Scenario Simulation

This feature allows users to input a hypothetical scenario, after which the system predicts its likelihood and consequences, generates a pre-emptive strategy, and improves readiness.

#### What this feature does

This feature allows users to ask:

> *"What happens if this disruption occurs?"*

Instead of waiting for a real event, the system accepts a hypothetical disruption and simulates how it may propagate across the broader supply ecosystem.

The goal is not only to predict impact, but also to **generate contingency plans** and **improve preparedness**.

#### Architecture process

The scenario engine architecture is more internal and system-oriented than the debate architecture. It focuses on state, propagation, evidence, and verification.

It can be read as six cooperating layers.

#### 1. Scenario engine: stateful simulation core

At the top of the architecture is the **scenario engine**, which contains:

- **Propagation Rules** — define how one disruption can trigger downstream effects
- **Events** — discrete happenings within the simulation
- **Confidence Scoring** — tracks how strongly supported each inferred consequence is
- **World State** — represents the current state of the simulated environment
- **Event Queue** — stores pending events to process

This is the simulation backbone. It exists so the simulation is not just a one-shot LLM answer. Instead, it behaves like a **stateful engine** that can evolve over time as more consequences are discovered.

#### 2. Orchestration layer: execution control

Below the scenario engine is the **orchestration layer**, which coordinates the workflow through nodes such as:

- `ScenarioSeedNode`
- `TinyFishExecutorNode`
- `PropagationNode`
- `TerminationCheckNode`
- `DebatePolicyNode`
- `ClaimPlannerNode`
- `EvidencePlannerNode`
- `StateUpdateNode`

A typical flow is:

1. Seed the scenario
2. Propagate effects
3. Decide what claims need to be generated
4. Decide what evidence needs to be retrieved
5. Validate updates
6. Write results back into the world state
7. Check whether the simulation should continue

This graph-based approach makes the system **modular and inspectable**. Each node has a clear responsibility.

#### 3. Agent layer: reasoning actions

The agent layer contains the reasoning primitives:

- `propose_claim` — generate hypotheses
- `request_evidence` — request supporting evidence
- `propose_consequence` — expand the scenario into downstream consequences
- `challenge_claim` — challenge weak claims

This layer gives the simulation its **exploratory intelligence**, while the rest of the system constrains and verifies that exploration.

#### 4. Evidence layer: external grounding with TinyFish

The evidence layer connects the simulation to the outside world through **TinyFish** and other external web sources.

Its role is to retrieve real supporting information relevant to:

- a proposed claim,
- a possible downstream consequence,
- or a scenario assumption.

This makes the simulation more than speculative brainstorming. It becomes a system that can **support hypothetical modeling with retrieved external evidence**.

For example, if the simulation proposes that a disruption in one region could affect shipping or commodity pricing, the evidence layer can collect supporting material from external sources before the claim is accepted.

#### 5. Verification layer: evidence normalization and claim verification

The verification layer consists of:

- `EvidenceNormalizerNode` — turns raw evidence into structured format
- `ClaimVerifierNode` — checks claims against structured evidence

Only approved claims move forward as verified outputs. This step is important because the system should not update the world state from unverified speculation. The verification layer acts as a **gatekeeper** between exploration and accepted simulation truth.

#### 6. Data objects: structured outputs of the simulation

At the bottom of the architecture are the data objects:

| Object | Role |
|--------|------|
| `VerifiedFact` | Accepted truths within the simulation |
| `EvidenceBundle` | Collections of retrieved evidence |
| `Event` | Discrete simulation happenings |
| `Claim` | Hypotheses generated by the agent layer |
| `EvidenceTask` | Tasks for evidence retrieval |

These objects are the common language of the system, making it possible to move information cleanly across layers.

#### Expanded description of the architecture

The scenario engine architecture is built around one core principle:

> **Hypothetical scenarios should still be processed through a disciplined, evidence-aware reasoning pipeline.**

That is why the architecture is not just a simple "input → model → output" structure. Instead, it contains:

- a state model,
- an event queue,
- a claim/evidence loop,
- a verification stage,
- and a termination check.

This design allows the system to **simulate chain reactions in a controlled way**.

For example, a user may define a disruption involving a key supplier country and a critical commodity. The engine seeds that scenario, expands possible downstream effects, asks what consequences are plausible, retrieves evidence, verifies claims, updates the simulated world state, and repeats until the system determines that the scenario has been sufficiently explored.

That is how the architecture supports both:

- **Likelihood-oriented analysis** — how probable is each consequence?
- **Pre-emptive planning** — what should be done in advance?

#### Why this matters

This architecture gives ALORE a **proactive capability** rather than limiting it to disruption detection.

It allows the system to:

- **Stress-test** supply chains before real shocks occur
- **Identify vulnerabilities** early
- **Generate contingency plans** grounded in evidence rather than speculation

---

## All Features

| Feature | Benefit |
|---------|---------|
| **Real-time Monitoring** | Continuous 24/7 event detection—no manual scanning required |
| **Reactive Negotiation Simulation** | Automatically simulates trade negotiations with candidate partners when a disruption hits, producing a ranked recommendation with trade-off analysis |
| **What-If Scenario Simulation** | Proactively models hypothetical disruptions, propagates cascading effects, and generates evidence-backed contingency plans before real shocks occur |
| **Sentry Signal Monitoring** | Live observability dashboard tracking commodity prices, trade activity, and policy changes — signals feed into reactive and proactive flows |
| **Severity Ranking** | Focus on what matters: `CRITICAL` and `DISRUPTED` events get priority |
| **Historical Tracking** | Build knowledge of patterns, repeating risks, and seasonal vulnerabilities |
| **Deduplication & Consolidation** | One unified event record prevents duplicate alerts and confusion |
| **Supply Chain Context** | News curator understands Singapore's supply dependencies—flags relevant events automatically |
| **LLM-Powered Classification** | Semantic understanding of disruption context (not just keyword matching) |

---

## Roadmap

- **Phase 1 (Current)**: Supply chain monitoring, news curation, disruption detection, reactive negotiation simulation, what-if scenario modeling
- **Phase 2 (Next)**:
  - Expand commodity coverage (beyond food/energy to electronics, rare earths, pharmaceuticals)
  - Integrate with government and industry supply chain datasets
  - Predictive disruption models (anticipate disruptions before they occur)
- **Phase 3 (Future)**:
  - Real-time portfolio optimization (auto-recommend sourcing adjustments)
  - Cross-agency collaboration and coordinated response workflows
  - Multi-scenario comparison dashboards for side-by-side contingency evaluation
  - Continuous learning from past disruption outcomes to improve simulation accuracy
